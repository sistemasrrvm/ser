"""
Middleware customizado para logging de requisições HTTP
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
import time
from typing import Callable

from .colored_logging import log_request, log_error


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para logar todas as requisições HTTP com cores e formatação
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Tempo de início
        start_time = time.time()
        
        # Obter informações da requisição
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""
        
        # Obter usuário (se autenticado)
        user = None
        if "authorization" in request.headers:
            # Tentar extrair username do token (opcional)
            pass
        
        # Executar requisição
        try:
            response = await call_next(request)
            
            # Calcular tempo de processamento
            process_time = time.time() - start_time
            
            # Obter status code (pode ser de Response ou StreamingResponse)
            status_code = response.status_code if hasattr(response, 'status_code') else 200
            
            # Log da requisição
            log_request(
                method=method,
                path=path,
                user=user,
                status=status_code
            )
            
            # Adicionar header com tempo de processamento (apenas se for Response normal)
            if hasattr(response, 'headers'):
                response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            return response
            
        except Exception as e:
            # Calcular tempo até o erro
            process_time = time.time() - start_time
            
            # Log do erro
            log_error(
                f"Erro ao processar requisição {method} {path}",
                exc=e,
                context={
                    "method": method,
                    "path": path,
                    "query_params": query_params,
                    "process_time": f"{process_time:.3f}s"
                }
            )
            
            # Re-raise para que o handler global de exceções trate
            raise

