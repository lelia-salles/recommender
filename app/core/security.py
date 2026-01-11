import os
import bcrypt  # Mudamos de passlib para bcrypt direto
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

# Configurações
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Chave de criptografia de dados
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
fernet = Fernet(ENCRYPTION_KEY)


# --- FUNÇÕES DE SENHA (AGORA COM BCRYPT DIRETO) ---

def get_password_hash(password: str) -> str:
    """Transforma a senha em um hash seguro."""
    # O bcrypt precisa de bytes, então convertemos a string com .encode()
    pwd_bytes = password.encode('utf-8')

    # Gera o salt e o hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)

    # Retorna como string para salvar no banco (o banco espera varchar)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha bate com o hash."""
    # Converte tudo para bytes para o bcrypt comparar
    plain_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')

    return bcrypt.checkpw(plain_bytes, hashed_bytes)


# --- FUNÇÕES DE CRIPTOGRAFIA DE DADOS (Mantidas iguais) ---
def encrypt_data(data: str) -> str:
    return fernet.encrypt(data.encode()).decode()


def decrypt_data(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()


# --- FUNÇÕES JWT (Mantidas iguais) ---
def create_access_token(data: dict):
    to_encode = data.copy()
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