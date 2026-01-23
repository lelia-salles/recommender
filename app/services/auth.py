from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# --- CONFIGURAÇÕES ---
# Em produção, use uma chave aleatória complexa e salve em variáveis de ambiente (.env)
SECRET_KEY = "minha_chave_secreta_super_segura"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Define a rota que o Swagger usará para pedir login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# --- 1. FUNÇÃO PARA CRIAR TOKEN (O que faltava) ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Gera um token JWT codificado com os dados do usuário e validade.
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Adiciona a data de expiração no payload
    to_encode.update({"exp": expire})

    # Cria o token criptografado
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- 2. FUNÇÃO PARA VALIDAR TOKEN (A que você já tinha) ---
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Decodifica o token recebido e valida o usuário.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        # Retorna os dados do usuário para ser usado na rota
        return {"username": username}

    except JWTError:
        raise credentials_exception