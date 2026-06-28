"""
Configurações da aplicação
Carrega variáveis de ambiente e define configurações globais
"""

from pydantic_settings import BaseSettings
from typing import List
import os
import logging


class Settings(BaseSettings):
    """Configurações da aplicação"""

    # Database
    DATABASE_URL: str

    def __init__(self, **kwargs):
        """Inicializa e valida configurações"""
        super().__init__(**kwargs)

        # Debug: logar DATABASE_URL no startup (apenas primeiros/últimos caracteres)
        logger = logging.getLogger('ser_app')
        try:
            if self.DATABASE_URL:
                url_preview = f"{self.DATABASE_URL[:20]}...{self.DATABASE_URL[-20:]}" if len(self.DATABASE_URL) > 40 else self.DATABASE_URL
                logger.info(f"CONFIG: DATABASE_URL carregada: {url_preview}")
            else:
                logger.warning(f"CONFIG: ERRO: DATABASE_URL esta vazia ou None!")
                logger.warning(f"CONFIG: DATABASE_URL do ambiente: {os.getenv('DATABASE_URL', 'NOT_FOUND')}")
        except Exception as e:
            # Ignorar erros de encoding no Windows
            pass

    # JWT (variáveis de ambiente: ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Tempo até o login "cair"; aumentar (ex: 480 = 8h) se usuário reclamar
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Password Reset
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173"

    # Application
    APP_NAME: str = "SER - Sistema de Emissão de Relatórios"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # NR13 API Botset (#292)
    NR13_API_BASE_URL: str = (
        "https://bpm.api.botset.net/api/callback/RRVMNR13/RRVMNR13/cadastros"
    )
    NR13_API_BASIC_USER: str = ""
    NR13_API_BASIC_PASSWORD: str = ""
    NR13_EQUIPAMENTO_TIPO: str = "12"
    NR13_DATA_REF_DAYS_BACK: int = 2
    NR13_SYNC_CRON_SECRET: str = ""
    NR13_API_TIMEOUT_SECONDS: float = 120.0

    # SMTP / notificações de fluxo (#248)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 465
    SMTP_USE_SSL: bool = True
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_FROM_NAME: str = "SER - Sistema de Emissão de Relatórios"
    FRONTEND_URL: str = ""

    # Exportação Excel (#304 / migração COM Windows)
    # Valores: excel_com | openpyxl | none | (vazio = auto: excel_com no Windows, none no Linux)
    EXPORT_ENGINE: str = ""
    EXCEL_COM_TIMEOUT_SECONDS: int = 300
    EXCEL_TEMP_DIR: str = ""
    EXCEL_COM_VISIBLE: bool = False

    @property
    def cors_origins_list(self) -> List[str]:
        """Retorna lista de origins permitidas para CORS"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        # Permitir arquivo .env se existir (desenvolvimento local)
        # Mas sempre dar preferência para variáveis de ambiente do sistema (Railway)
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        # Variáveis de ambiente do sistema têm prioridade sobre .env
        env_prefix = ""
        extra = "ignore"  # Ignorar variáveis extras não mapeadas


# Instância global de configurações
settings = Settings()
