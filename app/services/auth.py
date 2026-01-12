from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.services.auth import get_current_user

# --- CONFIGURAÇÕES ---
# IMPORTANTE: Use a mesma SECRET_KEY que você usou na função de login!
SECRET_KEY = "minha_chave_secreta_super_segura"
ALGORITHM = "HS256"

# Isso diz ao FastAPI que a rota para pegar o token é a "/login"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Função que valida o token JWT.
    Se o token for inválido, lança erro 401.
    Se for válido, retorna os dados do usuário.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Tenta decodificar o token usando a chave secreta
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        # Retorna um dicionário simples com os dados do usuário
        return {"username": username, "sub": username}

    except JWTError:
        raise credentials_exception