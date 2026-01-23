from fastapi import FastAPI, Depends, HTTPException, status, Body, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
from typing import Optional, List

# --- IMPORTS DOS SERVIÇOS ---
from app.services.auth import get_current_user, create_access_token
# [MUDANÇA 1] Importando o motor Híbrido em vez do Genérico
from app.services.hybrid_recommender import HybridRecommender
from app.services.parser import FileParser

# --- INICIALIZAÇÃO DOS SERVIÇOS ---
# [MUDANÇA 2] Inicializa o Híbrido (ele conecta no Postgres e carrega o modelo .pkl automaticamente)
recommender = HybridRecommender()
parser = FileParser()


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
# Nota: O Item 2 (Salvar no Banco) será implementado no próximo passo.
# Por enquanto, mantivemos a rota recebendo o arquivo, mas ela ainda não
# persiste no Postgres (apenas processa).

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
        # [MUDANÇA AQUI]: Chamamos o novo método do hybrid_recommender
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