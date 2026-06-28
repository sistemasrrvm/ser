"""
Configuração do banco de dados
SQLModel + MySQL
"""

from sqlmodel import create_engine, Session, SQLModel
from typing import Generator, Optional
from .config import settings
import sys
import logging

# Logger básico de fallback (sempre disponível)
_logger = logging.getLogger(__name__)

# Variável global para armazenar o engine (lazy initialization)
_engine: Optional[Session] = None


def _normalize_mysql_url(url: str) -> str:
    """Garante charset=utf8mb4 na URL (evita ?? em acentos no Windows)."""
    if not url.startswith("mysql"):
        return url
    if "charset=" in url.lower():
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}charset=utf8mb4"


def _mysql_connect_args(url: str) -> dict:
    if not url.startswith("mysql"):
        return {}
    return {
        "charset": "utf8mb4",
        "use_unicode": True,
        "init_command": "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci",
    }


def _ensure_engine():
    """
    Cria o engine do banco de dados de forma lazy (apenas quando necessário)
    Isso evita erros silenciosos durante a importação do módulo
    """
    global _engine
    
    if _engine is not None:
        return _engine
    
    # Tentar importar colored_logging, mas usar fallback se não estiver disponível
    try:
        from .colored_logging import log_error, log_info, log_success
        log_func = log_info
        error_func = log_error
        success_func = log_success
    except (ImportError, AttributeError):
        # Fallback para logging básico se colored_logging não estiver disponível
        log_func = lambda msg: _logger.info(msg) or print(f"INFO: {msg}", file=sys.stderr)
        error_func = lambda msg, **kwargs: _logger.error(msg) or print(f"ERROR: {msg}", file=sys.stderr)
        success_func = lambda msg: _logger.info(msg) or print(f"SUCCESS: {msg}", file=sys.stderr)
    
    # Validar DATABASE_URL antes de criar engine
    if not settings.DATABASE_URL:
        error_func("DATABASE_URL não configurada! Verifique as variáveis de ambiente do Railway")
        print("ERRO CRÍTICO: DATABASE_URL não configurada!", file=sys.stderr)
        sys.exit(1)
    
    if not settings.DATABASE_URL.startswith(("mysql", "postgresql", "sqlite")):
        error_func(f"DATABASE_URL inválida: {settings.DATABASE_URL[:50]}...")
        print(f"ERRO CRÍTICO: DATABASE_URL inválida: {settings.DATABASE_URL[:50]}...", file=sys.stderr)
        sys.exit(1)
    
    log_func("🔧 Criando engine do banco de dados...")
    print("🔧 Criando engine do banco de dados...", file=sys.stderr)
    
    try:
        db_url = _normalize_mysql_url(settings.DATABASE_URL)
        _engine = create_engine(
            db_url,
            echo=False,  # Desabilitar logs SQL (mesmo em debug para evitar poluição)
            pool_pre_ping=True,   # Verificar conexão antes de usar
            pool_recycle=3600,    # Reciclar conexões a cada hora
            connect_args=_mysql_connect_args(db_url),
        )
        success_func("✅ Engine do banco de dados criado com sucesso")
        print("✅ Engine do banco de dados criado com sucesso", file=sys.stderr)
        return _engine
    except Exception as e:
        error_func(f"Erro ao criar engine do banco de dados: {e}")
        print(f"ERRO CRÍTICO ao criar engine: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise


class EngineProxy:
    """Proxy para acesso lazy ao engine"""
    def __getattr__(self, name):
        engine = _ensure_engine()
        return getattr(engine, name)
    
    def __call__(self, *args, **kwargs):
        return _ensure_engine()
    
    def __enter__(self):
        return _ensure_engine()
    
    def __exit__(self, *args):
        pass
    
    # Permitir que o proxy funcione diretamente quando passado para Session()
    def __iter__(self):
        """Permite usar 'with Session(engine)' corretamente"""
        return iter([_ensure_engine()])


# Variável engine que inicializa lazy quando acessada
# Retorna o engine real quando necessário
def _get_engine_for_export():
    """Função helper para obter engine quando exportado"""
    return _ensure_engine()

# Exportar engine - quando importado, inicializa lazy
engine = EngineProxy()


def get_session() -> Generator[Session, None, None]:
    """
    Dependency para obter sessão do banco de dados

    Yields:
        Session: Sessão do SQLModel
    """
    db_engine = _ensure_engine()
    with Session(db_engine) as session:
        yield session


# Garantir que engine pode ser usado diretamente como objeto
def __getattr__(name):
    """Permite acesso a engine via import *"""
    if name == "engine":
        return engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def apply_pending_migrations():
    """
    Migrations idempotentes aplicadas no startup / init-db.
    Railway não possui shell interativo — evita erro 500 silencioso em produção.
    """
    from sqlalchemy import text

    try:
        from .colored_logging import log_info, log_success, log_warning
    except (ImportError, AttributeError):
        log_info = lambda msg: _logger.info(msg)
        log_success = lambda msg: _logger.info(msg)
        log_warning = lambda msg, **kwargs: _logger.warning(msg)

    db_engine = _ensure_engine()

    with db_engine.begin() as conn:
        # #246 — CHECK legado bloqueava status em_correcao (migration 003)
        result = conn.execute(
            text(
                """
                SELECT COUNT(*)
                FROM information_schema.TABLE_CONSTRAINTS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'reports'
                  AND CONSTRAINT_NAME = 'chk_reports_status'
                  AND CONSTRAINT_TYPE = 'CHECK'
                """
            )
        )
        if result.scalar() > 0:
            conn.execute(text("ALTER TABLE `reports` DROP CHECK `chk_reports_status`"))
            log_success("✅ Migration 020: removido CHECK chk_reports_status (em_correcao)")
        else:
            log_info("Migration 020: chk_reports_status já ausente")


def create_db_and_tables():
    """
    Cria todas as tabelas no banco (se não existirem)
    NOTA: Em produção, usar migrations (Alembic)
    """
    try:
        from .colored_logging import log_error, log_success
        log_success_func = log_success
        log_error_func = log_error
    except (ImportError, AttributeError):
        log_success_func = lambda msg: print(f"SUCCESS: {msg}", file=sys.stderr)
        log_error_func = lambda msg, **kwargs: print(f"ERROR: {msg}", file=sys.stderr)

    try:
        # Registrar todos os models no metadata antes do create_all
        from .. import models  # noqa: F401

        apply_pending_migrations()

        db_engine = _ensure_engine()
        SQLModel.metadata.create_all(db_engine)
        log_success_func("✅ Tabelas do banco de dados criadas/verificadas")
    except Exception as e:
        log_error_func(f"Erro ao criar tabelas do banco de dados: {e}")
        print(f"ERROR ao criar tabelas: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise