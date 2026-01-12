from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
import bcrypt  # Usamos direto agora
import os
from dotenv import load_dotenv

load_dotenv()

# Configurações JWT
SECRET_KEY = os.getenv("SECRET_KEY", "minha_chave_secreta_super_segura")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha bate com o hash do banco."""
    # O bcrypt precisa de bytes, então convertemos com .encode()
    # O hash do banco vem como string, convertemos para bytes também
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Gera o hash da senha."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')  # Retorna string para salvar no banco


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
