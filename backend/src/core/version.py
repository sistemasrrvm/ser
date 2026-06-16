"""
Sistema de versionamento e rastreamento de instâncias
Gera ID baseado no hash do código para identificar versão exata
"""

import hashlib
import os
import logging
from datetime import datetime
from pathlib import Path


class ServerVersion:
    """Informações de versão e instância do servidor"""

    def __init__(self):
        # Gerar ID baseado no hash dos arquivos Python
        self.instance_id = self._generate_code_hash()
        self.started_at = datetime.utcnow()

    def _generate_code_hash(self) -> str:
        """
        Gera hash MD5 dos arquivos Python do projeto
        Garante que o mesmo código sempre gera o mesmo ID
        Se qualquer linha de código mudar, o hash muda
        """
        try:
            # Diretório raiz do projeto (backend/src)
            src_dir = Path(__file__).parent.parent

            # Coletar conteúdo de todos os arquivos .py
            files_content = []
            file_count = 0

            for py_file in sorted(src_dir.rglob("*.py")):
                # Ignorar __pycache__ e arquivos temporários
                if "__pycache__" in str(py_file) or py_file.name.startswith("."):
                    continue

                try:
                    with open(py_file, "rb") as f:
                        content = f.read()
                        files_content.append(content)
                        file_count += 1
                except Exception as e:
                    # Ignorar erros de leitura de arquivos individuais
                    continue

            # Gerar hash MD5 de todo o conteúdo
            if files_content:
                combined = b"".join(files_content)
                hash_md5 = hashlib.md5(combined).hexdigest()
                code_id = hash_md5[:8]
                return code_id
            else:
                # Fallback caso não consiga ler arquivos
                return "00000000"
        except Exception as e:
            # Se houver qualquer erro, retornar fallback
            return "00000000"

    def get_info(self) -> dict:
        """Retorna informações da instância atual"""
        try:
            uptime = datetime.utcnow() - self.started_at
            return {
                "instance_id": self.instance_id,
                "started_at": self.started_at.isoformat(),
                "uptime_seconds": int(uptime.total_seconds())
            }
        except Exception as e:
            # Fallback se houver erro ao calcular uptime
            return {
                "instance_id": self.instance_id if hasattr(self, 'instance_id') else "unknown",
                "started_at": self.started_at.isoformat() if hasattr(self, 'started_at') else "unknown",
                "uptime_seconds": 0
            }

    def get_log_prefix(self) -> str:
        """Retorna prefixo para logs com ID da instância"""
        return f"[{self.instance_id}]"


# Instância global
server_version = ServerVersion()
