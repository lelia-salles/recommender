import os
import psycopg2

from fastapi import FastAPI, Depends, HTTPException, status, Body, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
from typing import Optional, List
from pydantic import BaseModel


from app.services.auth import get_current_user, create_access_token
from app.core.security import get_password_hash, hash_sensitive_data
from app.services.hybrid_recommender import HybridRecommender
from app.services.parser import FileParser

# --- INICIALIZAÇÃO DOS SERVIÇOS ---
# Conectando no Postgres e carrega o modelo .pkl automaticamente
recommender = HybridRecommender()
parser = FileParser()

# --- MODELO DE DADOS PARA REGISTRO ---
class UserCreate(BaseModel):
    username: str
    password: str
    email: str
    cpf: str  # Dado sensível (será hashado)

# --- LIFESPAN (Ciclo de Vida) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- INICIANDO SERVIDOR (Versão Híbrida) ---")

    # O HybridRecommender já carrega os dados no __init__,
    # então aqui apenas verificamos se está tudo certo.
    n_nodes = recommender.graph.number_of_nodes()
    n_edges = recommender.graph.number_of_edges()

    print(f"Status do Grafo: {n_nodes} nós e {n_edges} conexões carregadas do Banco.")

    yield
    print("--- DESLIGANDO SERVIDOR ---")


app = FastAPI(
    title="Sistema de Recomendação Universal (Hybrid Engine)",
    description="API v2 com conexão PostgreSQL e Machine Learning.",
    version="2.1.0",
    lifespan=lifespan
)


# ==========================================
# 0. ROTA DE REGISTRO (NOVA)
# ==========================================
@app.post("/register", status_code=201)
async def register(user: UserCreate):
    """
    Cadastra usuário protegendo os dados sensíveis.
    Preenche o campo 'email' legado com uma máscara.
    """
    conn = None
    try:
        # 1. Criptografia
        pwd_hash = get_password_hash(user.password)
        email_hash = hash_sensitive_data(user.email)
        cpf_hash = hash_sensitive_data(user.cpf)

        # 2. Máscara para o campo legado (NOT NULL)
        # Cria algo como: protegido_a7f9...@system.local
        # Isso garante unicidade se o banco exigir UNIQUE no email
        email_mask = f"protegido_{email_hash[:8]}@system.local"

        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "recommender"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASS", "password")
        )
        cur = conn.cursor()

        # 3. Inserção (Incluindo o campo 'email' com a máscara)
        query = """
                INSERT INTO public.users
                    (username, email, password_hash, email_hash, sensitive_data_hash)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING username; \
                """
        cur.execute(query, (user.username, email_mask, pwd_hash, email_hash, cpf_hash))

        conn.commit()
        cur.close()

        return {"msg": f"Usuário {user.username} criado com sucesso. Email real ocultado."}

    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=400, detail="Usuário ou dados já cadastrados.")
    except Exception as e:
        print(f"Erro no registro: {e}")
        raise HTTPException(status_code=500, detail="Erro interno.")
    finally:
        if conn: conn.close()

# ==========================================
# 1. ROTA DE AUTENTICAÇÃO (Login)
# ==========================================
@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Gera o Token JWT.
    """
    user_username = form_data.username
    # Em produção, você validaria a senha no banco aqui antes de gerar o token
    access_token = create_access_token(data={"sub": user_username})
    return {"access_token": access_token, "token_type": "bearer"}


# ==========================================
# 2. ROTAS DE INGESTÃO (Upload -> Banco)
# ==========================================

@app.post("/ingest-file")
async def ingest_file(
        file: UploadFile = File(...),
        current_user: dict = Depends(get_current_user)
):
    """
    [PERSISTENTE] Faz upload, converte e SALVA no PostgreSQL.
    """
    print(f"Usuário {current_user['username']} enviando arquivo: {file.filename}")

    try:
        # 1. Leitura e Parsing (Memória)
        content = await file.read()
        graph_data = parser.parse(file.filename, content)

        # 2. Ingestão (Persistência no DB + Atualização da RAM)

        saved_count = recommender.ingest_data(graph_data)

        return {
            "status": "Processado e Salvo com Sucesso",
            "filename": file.filename,
            "database_updates": {
                "new_interactions_saved": saved_count
            },
            "graph_current_state": {
                "total_nodes": recommender.graph.number_of_nodes(),
                "total_edges": recommender.graph.number_of_edges()
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Erro de formato: {str(e)}")
    except Exception as e:
        print(f"Erro interno: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao salvar dados.")
# ==========================================
# 3. ROTA DE RECOMENDAÇÃO (Core Híbrido)
# ==========================================
@app.get("/recommendations")
def get_recommendations(
        target_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        limit: int = 5,
        current_user: dict = Depends(get_current_user)
):
    """
    Gera recomendações usando Grafo + Machine Learning.
    """
    subject = entity_id if entity_id else current_user.get("username")

    print(f"Buscando recomendações Híbridas para: {subject}")

    # Verifica se o sujeito existe no grafo carregado
    if subject not in recommender.graph:
        return {
            "subject": subject,
            "warning": "Usuário/Entidade não encontrada no grafo atual.",
            "recommendations": []
        }

    # [MUDANÇA 3] Chama o método do híbrido
    # O hybrid_recommender.py retorna lista de tuplas: [('ItemA', 0.95), ('ItemB', 0.88)]
    results = recommender.get_recommendations(subject, top_k=limit)

    # Formata para JSON amigável
    formatted_recs = [{"item": item, "score": score} for item, score in results]

    return {
        "subject": subject,
        "engine": "Hybrid (Graph + Random Forest)",
        "recommendations": formatted_recs
    }


# ==========================================
# 4. ROTA DE DIAGNÓSTICO
# ==========================================
@app.get("/graph-stats")
def get_stats(current_user: dict = Depends(get_current_user)):
    return {
        "total_nodes": recommender.graph.number_of_nodes(),
        "total_edges": recommender.graph.number_of_edges(),
        "backend": "PostgreSQL + NetworkX"
    }