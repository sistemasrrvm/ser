"""
API v1 module
"""

from fastapi import APIRouter
from ...core import settings
from ...core.version import server_version
from .auth import router as auth_router
from .usuarios import router as usuarios_router
from .roles import router as roles_router
from .formularios import router as formularios_router
from .form_pages import router as form_pages_router
from .form_fields import router as form_fields_router
from .clientes import router as clientes_router
from .equipamentos import router as equipamentos_router
from .tipos_equipamento import router as tipos_equipamento_router
from .reports import router as reports_router
from .lookup_lists import router as lookup_lists_router
from .manut_data import router as manut_data_router
from .lookup import api_router as lookup_router
from .configuracoes import router as configuracoes_router
from .debug import router as debug_router
from .nr13_internal import router as nr13_internal_router

# Router principal da API v1
api_router = APIRouter(prefix="/api/v1")


# Rota raiz da API v1 - Status e versão
@api_router.get("/", tags=["Status"])
async def api_v1_root():
    """
    Rota raiz da API v1 - Retorna status e informações de versão
    Retorna código hash do backend baseado no código fonte
    """
    try:
        # Obter informações da versão (hash do código)
        instance_info = server_version.get_info()
        code_hash = instance_info.get("instance_id", "unknown") if instance_info else "unknown"
        
        return {
            "message": "SER API v1",
            "version": settings.APP_VERSION,
            "code_hash": code_hash,  # Hash do código fonte
            "instance_id": code_hash,  # Compatibilidade
            "started_at": instance_info.get("started_at", "unknown") if instance_info else "unknown",
            "uptime_seconds": instance_info.get("uptime_seconds", 0) if instance_info else 0,
            "status": "online"
        }
    except AttributeError as e:
        # Erro ao acessar atributos de server_version
        import sys
        print(f"ERRO AttributeError ao obter versão: {e}", file=sys.stderr)
        return {
            "message": "SER API v1",
            "version": settings.APP_VERSION,
            "code_hash": "unknown",
            "instance_id": "unknown",
            "started_at": "unknown",
            "uptime_seconds": 0,
            "status": "online",
            "error": "AttributeError"
        }
    except Exception as e:
        # Fallback simplificado - logar erro mas retornar resposta válida
        import sys
        import traceback
        error_msg = str(e)
        print(f"ERRO ao obter versão: {error_msg}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {
            "message": "SER API v1",
            "version": settings.APP_VERSION,
            "code_hash": "error",
            "instance_id": "error",
            "started_at": "error",
            "uptime_seconds": 0,
            "status": "online",
            "error": error_msg
        }


# Health check para Railway
@api_router.get("/health", tags=["Status"])
async def health_check():
    """
    Health check endpoint para Railway e monitoramento
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "service": "backend"
    }


@api_router.post("/apply-migrations", tags=["Admin"])
async def apply_migrations():
    """
    Aplica migrations idempotentes pendentes (ex.: #020 em_correcao).
    Seguro para reexecutar em produção.
    """
    from ...core.database import apply_pending_migrations

    try:
        apply_pending_migrations()
        return {"status": "completed", "message": "Migrations aplicadas com sucesso"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


# Inicialização do banco de dados (migrations + seed admin)
@api_router.post("/init-db", tags=["Admin"])
async def init_database():
    """
    Executa migrations e cria usuário admin inicial
    ATENÇÃO: Endpoint de uso único para inicialização
    """
    from ...core.database import create_db_and_tables, apply_pending_migrations, _ensure_engine
    from ...models import User
    from ...core.security import get_password_hash
    from sqlmodel import Session, select

    try:
        # Criar tabelas + migrations idempotentes (#020 em_correcao)
        create_db_and_tables()

        # Verificar se admin já existe
        db_engine = _ensure_engine()
        with Session(db_engine) as session:
            admin = session.exec(select(User).where(User.username == "admin")).first()

            if not admin:
                # Criar role admin se não existir
                from ...models import Role
                admin_role = session.exec(select(Role).where(Role.name == "admin")).first()
                if not admin_role:
                    admin_role = Role(name="admin", level=100, description="Administrador do Sistema")
                    session.add(admin_role)
                    session.commit()
                    session.refresh(admin_role)

                # Criar usuário admin
                admin_user = User(
                    username="admin",
                    email="admin@example.com",
                    full_name="Administrador",
                    password_hash=get_password_hash("admin123"),
                    role_id=admin_role.id,
                    is_active=True
                )
                session.add(admin_user)
                session.commit()
                session.refresh(admin_user)

                return {
                    "status": "completed",
                    "message": "Database initialized successfully",
                    "admin_created": True,
                    "admin_username": "admin",
                    "admin_password": "admin123"
                }
            else:
                return {
                    "status": "completed",
                    "message": "Database already initialized",
                    "admin_created": False
                }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }


# Incluir rotas (com tratamento de erro para evitar 500 durante importação)
try:
    api_router.include_router(auth_router)
    api_router.include_router(usuarios_router)
    api_router.include_router(roles_router)
    api_router.include_router(formularios_router)
    api_router.include_router(form_pages_router)
    api_router.include_router(form_fields_router)
    api_router.include_router(lookup_lists_router)
    api_router.include_router(lookup_router)
    api_router.include_router(clientes_router)
    api_router.include_router(equipamentos_router)
    api_router.include_router(tipos_equipamento_router)
    api_router.include_router(reports_router)
    api_router.include_router(manut_data_router)
    api_router.include_router(configuracoes_router)
    api_router.include_router(nr13_internal_router)
    api_router.include_router(debug_router)  # Debug endpoints
except Exception as e:
    # Log do erro mas não falha silenciosamente - isso vai aparecer no startup
    import traceback
    print(f"ERRO ao incluir routers: {e}", file=__import__('sys').stderr)
    traceback.print_exc(file=__import__('sys').stderr)
    raise

__all__ = ["api_router"]
