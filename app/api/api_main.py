import psycopg2
import os
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

# Imports dos módulos do projeto
from app.core.security import verify_password, create_access_token, decode_access_token
from app.services.recommender import recommend

# Carrega variáveis de ambiente (.env)
load_dotenv()

# Inicializa a API
app = FastAPI(
    title="Recommender System API",
    description="API de Recomendação com Autenticação JWT e PostgreSQL",
    version="1.0"
)


# --- MODELOS Pydantic (Schemas) ---

class RecommendationResponse(BaseModel):
    item: str
    score: float


# Configuração do Swagger UI para suportar o botão "Authorize" (Cadeado)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# --- FUNÇÕES AUXILIARES ---

def get_db_connection():
    """Conecta ao banco PostgreSQL com encoding UTF-8."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "recommender_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "password"),
        client_encoding='utf-8'
    )


def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependência de segurança:
    1. Lê o Token Bearer do Header.
    2. Valida a assinatura JWT.
    3. Retorna o username (sub) se for válido.
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload.get("sub")


# --- ROTAS DA API ---

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Rota de Autenticação.
    Compatível com o botão 'Authorize' do Swagger.
    Recebe 'username' e 'password' via Form-Data.
    """
    conn = None  # Inicializa como None para evitar erro no finally
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Busca o hash da senha no banco (schema public explícito)
            cur.execute("SELECT password_hash FROM public.users WHERE username = %s", (form_data.username,))
            result = cur.fetchone()

        # Verifica se o usuário existe e se a senha bate com o hash
        if not result or not verify_password(form_data.password, result[0]):
            # Retorna 400 (Bad Request) para senha errada
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuário ou senha incorretos"
            )

        # Gera o Token de Acesso
        access_token = create_access_token(data={"sub": form_data.username})
        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException as he:
        # Se for erro de senha (400) ou Auth (401), relança para o usuário ver
        raise he
    except Exception as e:
        # Se for erro de banco ou código, loga no terminal e dá erro 500
        print(f"Erro CRÍTICO no login: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no servidor")
    finally:
        # Só tenta fechar se a conexão foi aberta com sucesso
        if conn:
            conn.close()


@app.get("/recommendations", response_model=List[RecommendationResponse])
def get_recommendations(current_user: str = Depends(get_current_user)):
    """
    Rota Protegida (Requer Cadeado).
    Usa o usuário logado (current_user) para buscar recomendações no Postgres.
    """
    print(f"Gerando recomendações para: {current_user}")

    try:
        # Chama o serviço de recomendação
        # O serviço recommender.py já gerencia sua própria conexão com banco
        raw_recs = recommend(current_user, limit=5, depth=3)

        # Converte a resposta (Tuplas) para o formato JSON esperado
        return [{"item": item, "score": score} for item, score in raw_recs]

    except Exception as e:
        print(f"Erro ao recomendar: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar recomendações")


@app.get("/")
def root():
    return {
        "status": "online",
        "message": "Sistema de Recomendação Ativo",
        "docs_url": "/docs"
    }