import psycopg2
import os
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Imports dos módulos do projeto
from app.core.security import verify_password, create_access_token, decode_access_token
from app.services.auth import get_current_user
from app.services.recommender import HybridRecommender


# --- SIMULAÇÃO DE DADOS (Ou carregue do seu DB) ---
def popular_dados_iniciais(rec_system):
    """
    Função para garantir que o grafo não inicie vazio.
    Aqui recriamos o cenário onde U1 tem conexões.
    """
    print("--- CARREGANDO DADOS NO GRAFO ---")

    # Adicionando Usuários
    rec_system.graph.add_node("U1", "user")
    rec_system.graph.add_node("U2", "user")
    rec_system.graph.add_node("U3", "user")

    # Adicionando Produtos
    rec_system.graph.add_node("P1", "product")  # Notebook
    rec_system.graph.add_node("P2", "product")  # Mouse
    rec_system.graph.add_node("P3", "product")  # Monitor
    rec_system.graph.add_node("P4", "product")  # Teclado (Recomendação esperada)

    # Adicionando Interações (Arestas)
    # U1 comprou P1 e P2
    rec_system.graph.add_edge("U1", "P1")
    rec_system.graph.add_edge("U1", "P2")

    # U2 comprou P1 e P4 (Aqui está a conexão: Quem comprou P1 também comprou P4)
    rec_system.graph.add_edge("U2", "P1")
    rec_system.graph.add_edge("U2", "P4")

    # U3 comprou P2 e P3
    rec_system.graph.add_edge("U3", "P2")
    rec_system.graph.add_edge("U3", "P3")

    print(f"Dados carregados. Nós: {len(rec_system.graph.adj_list)}")


# --- INICIALIZAÇÃO DO SISTEMA ---
recommender = HybridRecommender()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Executado antes do servidor começar a aceitar requisições
    popular_dados_iniciais(recommender)
    yield
    # (Código após o yield roda quando o servidor desliga)


app = FastAPI(lifespan=lifespan)


# ... Resto das suas rotas (/login, /recommendations) ...

@app.get("/recommendations")
# AQUI ESTÁ A MUDANÇA: 'current_user' agora depende da validação do token
def get_recommendations(current_user: dict = Depends(get_current_user)):
    # Extrai o ID do usuário de dentro do token (ajuste a chave se for "username" ou "id")
    user_id = current_user.get("username")

    print(f"Autenticado com sucesso. Gerando recomendações para: {user_id}")

    # Verifica se o usuário do token existe no grafo
    if user_id not in recommender.graph.adj_list:
        # Opcional: Adicionar o usuário ao grafo se for novo
        # recommender.graph.add_node(user_id, "user")
        return {"user": user_id, "recommendations": [], "msg": "Usuário novo ou sem histórico"}

    recs = recommender.recommend(user_id)
    return {"user": user_id, "recommendations": recs}