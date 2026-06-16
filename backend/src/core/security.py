"""
Módulo de segurança
Funções para autenticação, hashing de senhas e geração de tokens JWT
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHash
import secrets

from .config import settings


# Configuração do Argon2
ph = PasswordHasher(
    time_cost=3,           # iterations
    memory_cost=65536,     # 64 MB
    parallelism=4,         # threads
    hash_len=32,           # bytes
    salt_len=16            # bytes
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha fornecida corresponde ao hash

    Args:
        plain_password: Senha em texto plano
        hashed_password: Hash Argon2 da senha

    Returns:
        True se a senha corresponder, False caso contrário
    """
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except (VerifyMismatchError, InvalidHash):
        return False


def get_password_hash(password: str) -> str:
    """
    Gera hash Argon2 da senha

    Args:
        password: Senha em texto plano

    Returns:
        Hash Argon2 da senha
    """
    return ph.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria access token JWT

    Args:
        data: Dados a serem incluídos no token (user_id, username, role)
        expires_delta: Tempo de expiração customizado

    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria refresh token JWT

    Args:
        data: Dados a serem incluídos no token (user_id, username)
        expires_delta: Tempo de expiração customizado

    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodifica e valida token JWT

    Args:
        token: Token JWT codificado

    Returns:
        Payload do token se válido, None caso contrário
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_password_reset_token() -> str:
    """
    Gera token aleatório para recuperação de senha

    Returns:
        Token seguro de 64 caracteres hexadecimais
    """
    return secrets.token_urlsafe(48)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Valida força da senha conforme requisitos
    Requisitos: mínimo 8 caracteres, números, maiúsculas e caracteres especiais

    Args:
        password: Senha a ser validada

    Returns:
        Tupla (válida: bool, mensagem: str)
    """
    if len(password) < 8:
        return False, "Senha deve ter no mínimo 8 caracteres"

    if not any(char.isupper() for char in password):
        return False, "Senha deve conter pelo menos uma letra maiúscula"

    if not any(char.isdigit() for char in password):
        return False, "Senha deve conter pelo menos um número"

    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(char in special_chars for char in password):
        return False, "Senha deve conter pelo menos um caractere especial"

    return True, "Senha válida"
