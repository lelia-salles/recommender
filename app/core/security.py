import os
import bcrypt
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURAÇÕES DE SEGURANÇA ---
# Chave para assinar os Tokens JWT (Autenticação)
SECRET_KEY = os.getenv("SECRET_KEY", "minha_chave_secreta_super_segura")

# Chave "Pepper" para mascarar dados sensíveis (PII)
# IMPORTANTE: Se você perder esta chave, não conseguirá mais buscar os dados hash no banco.
SECURITY_PEPPER = os.getenv("SECURITY_PEPPER", "pimenta_secreta_para_dados_sensiveis")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# ==========================================
# 1. HASHING DE SENHAS (Bcrypt)
# ==========================================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha bate com o hash do banco."""
    # Bcrypt requer bytes
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')

    return bcrypt.checkpw(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Gera um hash seguro para salvar a senha."""
    if isinstance(password, str):
        password = password.encode('utf-8')

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    return hashed.decode('utf-8')


# ==========================================
# 2. HASHING DE DADOS SENSÍVEIS (Blake2b)
# ==========================================
def hash_sensitive_data(data: str) -> str:
    """
    Usa BLAKE2b com chave (keyed hashing).
    Substitui o HMAC-SHA256 por ser mais moderno e seguro.
    Gera uma assinatura determinística (sempre igual para o mesmo dado).
    """
    if not data:
        return None

    # O Blake2b exige que a chave (key) tenha no máximo 64 bytes
    # Pegamos os primeiros 64 bytes da variável de ambiente
    key_bytes = SECURITY_PEPPER.encode('utf-8')[:64]

    # Cria o hash com a chave
    h = hashlib.blake2b(key=key_bytes, digest_size=32)
    h.update(data.encode('utf-8'))

    return h.hexdigest()


def verify_integrity(data: str, stored_hash: str) -> bool:
    """
    Verifica se um dado sensível (ex: CPF digitado) corresponde ao hash guardado.
    """
    calculated = hash_sensitive_data(data)
    # compare_digest compara strings em tempo constante para evitar 'Timing Attacks'
    return hmac.compare_digest(calculated, stored_hash)


# ==========================================
# 3. GESTÃO DE TOKENS (JWT)
# ==========================================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None