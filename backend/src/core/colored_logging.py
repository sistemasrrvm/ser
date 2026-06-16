"""
Colored Logging - Configuração de logs com formatação aprimorada
Sistema de logging com indentação e formatação aprimorada (sem cores)
"""

import logging
import sys
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """
    Formatter customizado para diferentes níveis de log (sem cores)
    """

    # Ícones por nível
    LEVEL_ICONS = {
        'DEBUG': '[DEBUG]',
        'INFO': '[INFO]',
        'WARNING': '[WARN]',
        'ERROR': '[ERROR]',
        'CRITICAL': '[CRIT]',
    }

    def format(self, record):
        # Obter ícone baseado no nível
        level_icon = self.LEVEL_ICONS.get(record.levelname, '')
        
        # Formatar timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Formatar nome do módulo (pegar apenas o nome do arquivo)
        module_name = record.name.split('.')[-1] if '.' in record.name else record.name
        if len(module_name) > 15:
            module_name = module_name[:12] + '...'
        
        # Formatar mensagem
        message = record.getMessage()
        
        # Adicionar espaçamento antes de erros
        prefix = ""
        if record.levelname in ['ERROR', 'CRITICAL']:
            prefix = "\n" * 5  # 5 linhas em branco antes de erros
        
        # Formatar sem cores
        formatted = (
            f"{prefix}"
            f"[{timestamp}] "
            f"{level_icon:8} "
            f"[{module_name:15}] "
            f"{message}"
        )
        
        return formatted


def setup_colored_logging(level: int = logging.INFO):
    """
    Configura logging formatado para a aplicação
    
    Args:
        level: Nível de logging (default: INFO)
    """
    # Configurar handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Aplicar formatter customizado
    formatter = ColoredFormatter()
    console_handler.setFormatter(formatter)

    # Configurar logger raiz
    root_logger = logging.getLogger()

    # Remover handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Adicionar novo handler formatado
    root_logger.addHandler(console_handler)
    root_logger.setLevel(level)

    # Desabilitar completamente logs do SQLAlchemy (evita poluição)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.ERROR)
    logging.getLogger('sqlalchemy.orm').setLevel(logging.ERROR)
    logging.getLogger('sqlalchemy.dialects').setLevel(logging.ERROR)
    logging.getLogger('sqlalchemy').setLevel(logging.ERROR)

    # Configurar logs do Uvicorn para usar nosso formatter
    uvicorn_logger = logging.getLogger('uvicorn')
    uvicorn_logger.setLevel(logging.INFO)
    uvicorn_logger.handlers.clear()
    uvicorn_logger.addHandler(console_handler)
    
    uvicorn_error_logger = logging.getLogger('uvicorn.error')
    uvicorn_error_logger.setLevel(logging.WARNING)
    uvicorn_error_logger.handlers.clear()
    uvicorn_error_logger.addHandler(console_handler)
    
    uvicorn_access_logger = logging.getLogger('uvicorn.access')
    uvicorn_access_logger.setLevel(logging.WARNING)  # Desabilitar access logs

    # Logger customizado para a aplicação
    app_logger = logging.getLogger('ser_app')
    app_logger.setLevel(level)

    return app_logger


def log_error(message: str, exc: Optional[Exception] = None, context: Optional[dict] = None):
    """
    Helper para logar erros com destaque e indentação
    
    Args:
        message: Mensagem do erro
        exc: Exceção (opcional)
        context: Contexto adicional (opcional)
    """
    logger = logging.getLogger('ser_app')
    
    # 5 linhas em branco antes do erro (já adicionado pelo formatter, mas garantir)
    logger.error("")
    logger.error("")
    logger.error("")
    logger.error("")
    logger.error("")
    logger.error("=" * 80)
    logger.error(f"ERRO: {message}")
    
    if context:
        logger.error("  Contexto:")
        for key, value in context.items():
            logger.error(f"    {key}: {value}")
    
    if exc:
        logger.error("  Exceção:")
        logger.error(f"    Tipo: {type(exc).__name__}")
        logger.error(f"    Mensagem: {str(exc)}")
        
        # Se houver traceback, mostrar as últimas linhas
        import traceback
        tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
        if tb_lines:
            logger.error("  Traceback (últimas linhas):")
            for line in tb_lines[-5:]:  # Últimas 5 linhas
                logger.error(f"    {line.rstrip()}")
    
    logger.error("=" * 80)
    logger.error("")


def log_warning(message: str, context: Optional[dict] = None):
    """
    Helper para logar warnings
    
    Args:
        message: Mensagem do warning
        context: Contexto adicional (opcional)
    """
    logger = logging.getLogger('ser_app')
    
    logger.warning(f"WARNING: {message}")
    
    if context:
        for key, value in context.items():
            logger.warning(f"  {key}: {value}")


def log_info(message: str, context: Optional[dict] = None):
    """
    Helper para logar informações
    
    Args:
        message: Mensagem informativa
        context: Contexto adicional (opcional)
    """
    logger = logging.getLogger('ser_app')
    
    logger.info(message)
    
    if context:
        for key, value in context.items():
            logger.info(f"  {key}: {value}")


def log_success(message: str, context: Optional[dict] = None):
    """
    Helper para logar sucesso
    
    Args:
        message: Mensagem de sucesso
        context: Contexto adicional (opcional)
    """
    logger = logging.getLogger('ser_app')
    
    logger.info(f"✓ {message}")
    
    if context:
        for key, value in context.items():
            logger.info(f"  {key}: {value}")


def log_request(method: str, path: str, user: Optional[str] = None, status: Optional[int] = None):
    """
    Helper para logar requisições HTTP de forma formatada
    
    Args:
        method: Método HTTP (GET, POST, etc)
        path: Caminho da requisição
        user: Usuário que fez a requisição (opcional)
        status: Status code da resposta (opcional)
    """
    logger = logging.getLogger('ser_app')
    
    # Status string
    status_str = ""
    if status:
        status_str = f" [{status}]"
    
    # Usuário
    user_str = ""
    if user:
        user_str = f" @{user}"
    
    logger.info(
        f"{method:6} {path}{user_str}{status_str}"
    )


def log_separator(char: str = "=", color: str = None):
    """
    Imprime uma linha separadora
    
    Args:
        char: Caractere para a linha (default: "=")
        color: Não utilizado (mantido para compatibilidade)
    """
    logger = logging.getLogger('ser_app')
    logger.info(f"{char*80}")
