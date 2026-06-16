"""
Main module - FastAPI application
SER - Sistema de Emissão de Relatórios
"""

from fastapi import FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .core import settings
from .core.version import server_version
from .core.colored_logging import setup_colored_logging, log_error, log_info
from .core.middleware import RequestLoggingMiddleware
from .api.v1 import api_router

# Configurar logging formatado
app_logger = setup_colored_logging()


# Criar aplicação FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para gerenciamento de formulários e relatórios técnicos",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Adicionar middleware de logging de requisições (ANTES do CORS)
app.add_middleware(RequestLoggingMiddleware)

# Configurar CORS (permite cookies httpOnly)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,  # IMPORTANTE: permite envio de cookies
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluir rotas da API v1
app.include_router(api_router)


# Rota raiz
@app.get("/", tags=["Status"])
async def root():
    """
    Rota raiz - Status da API
    """
    instance_info = server_version.get_info()
    return {
        "message": "SER - Sistema de Emissão de Relatórios API",
        "version": settings.APP_VERSION,
        "instance_id": instance_info["instance_id"],
        "started_at": instance_info["started_at"],
        "uptime_seconds": instance_info["uptime_seconds"],
        "status": "online",
        "docs": "/api/docs"
    }


# Health check
@app.get("/health", tags=["Status"])
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }


# Handler para erros de validação (422)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler para erros de validação (422) com logs detalhados
    """
    from .core.colored_logging import log_warning
    
    errors = exc.errors()
    error_details = []
    
    for error in errors:
        field = ".".join(str(loc) for loc in error.get("loc", []))
        message = error.get("msg", "")
        error_type = error.get("type", "")
        error_details.append({
            "field": field,
            "message": message,
            "type": error_type
        })
    
    log_warning(
        f"⚠️ Erro de validação em {request.method} {request.url.path}",
        context={
            "path": str(request.url.path),
            "method": request.method,
            "errors": error_details
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Erro de validação",
            "errors": error_details
        }
    )


# Handler global de exceções
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Handler global para exceções não tratadas
    """
    # Logar erro em vermelho
    log_error(f"Exceção não tratada em {request.url.path}", exc)

    if settings.DEBUG:
        # Em modo debug, retornar detalhes do erro
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Erro interno do servidor",
                "error": str(exc),
                "type": type(exc).__name__
            }
        )
    else:
        # Em produção, retornar mensagem genérica
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Erro interno do servidor"
            }
        )


# Startup event
@app.on_event("startup")
async def startup_event():
    """
    Evento executado ao iniciar a aplicação
    """
    from .core.colored_logging import log_separator
    
    try:
        instance_info = server_version.get_info()
        code_hash = instance_info['instance_id']  # Hash do código fonte
        
        # Formato solicitado: simples e direto
        print('')
        print(f'🆔 Code Version ID (back): {code_hash} (hash do código)')
        print('')
        
        log_separator("=")
        log_info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION}")
        log_info(f"🆔 Code Version ID (back): {code_hash} (hash do código)")
        log_info(f"  Started at: {instance_info['started_at']}")
    except Exception as e:
        log_error(f"Erro ao obter versão do código: {e}", exc=e)
        print('')
        print('🆔 Code Version ID (back): erro (hash do código)')
        print('')
    log_info(f"  Docs: http://localhost:8000/api/docs")
    log_info(f"  CORS: {', '.join(settings.cors_origins_list)}")
    import sys
    from .services.excel_export_service import _normalize_engine
    engine = _normalize_engine()
    platform = sys.platform
    log_info(f"  Export Excel: engine={engine} (platform={platform})")
    log_info(f"  ✓ Logging formatado ativado")
    log_separator("=")

    try:
        from .core.database import apply_pending_migrations
        apply_pending_migrations()
    except Exception as e:
        log_error(f"Erro ao aplicar migrations pendentes: {e}", exc=e)

    log_info(f"Aplicação iniciada - Instance ID: {instance_info['instance_id']}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Evento executado ao desligar a aplicação
    """
    from .core.colored_logging import log_info
    log_info(f"👋 {settings.APP_NAME} desligando...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
