from fastapi import FastAPI, Depends, HTTPException, status, Body, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
from typing import Optional, List

# --- IMPORTS DOS SERVIÇOS ---
# Certifique-se que os arquivos auth.py, recommender.py e parser.py existem em app/services/
from app.services.auth import get_current_user, \
    create_access_token  # Assumindo que você tem o create_access_token no auth.py ou similar
from app.services.recommender import GenericRecommender
from app.services.parser import FileParser

# --- INICIALIZAÇÃO DOS SERVIÇOS ---
recommender = GenericRecommender()
parser = FileParser()


# --- LIFESPAN (Ciclo de Vida) ---
# Carrega um dataset mínimo de exemplo ao iniciar, apenas para não começar vazio
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- INICIANDO SERVIDOR ---")
    print("Carregando dados de exemplo na memória...")

    # Exemplo: Grafo simples de Rede Social
    sample_data = {
        "nodes": [
            {"id": "Admin", "type": "user"},
            {"id": "Python", "type": "skill"},
            {"id": "FastAPI", "type": "skill"}
        ],
        "edges": [
            {"source": "Admin", "target": "Python"},
            {"source": "Admin", "target": "FastAPI"}
        ]
    }
    recommender.load_data(sample_data)
    print("Sistema pronto.")
    yield
    print("--- DESLIGANDO SERVIDOR ---")


app = FastAPI(
    title="Sistema de Recomendação Universal",
    description="API flexível para recomendação baseada em Grafos (Arquivos e JSON).",
    version="2.0.0",
    lifespan=lifespan
)


# ==========================================
# 1. ROTA DE AUTENTICAÇÃO (Login)
# ==========================================
@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Gera o Token JWT.
    Para simplificar o teste, aceita qualquer usuário/senha,
    mas num caso real validaria no banco.
    """
    # Simulação de validação (Substitua por lógica real de banco de dados)
    # Aqui aceitamos qualquer login para fins de teste de desenvolvimento
    user_username = form_data.username

    # Cria o token (Certifique-se de ter a função create_access_token no auth.py ou implemente aqui)
    # Se não tiver, vou simular uma resposta simples, mas o ideal é usar o jwt.encode
    access_token = create_access_token(data={"sub": user_username})

    return {"access_token": access_token, "token_type": "bearer"}


# ==========================================
# 2. ROTAS DE INGESTÃO DE DADOS (Treinamento)
# ==========================================

@app.post("/ingest-file")
async def ingest_file(
        file: UploadFile = File(...),
        current_user: dict = Depends(get_current_user)
):
    """
    [FLEXÍVEL] Faz upload de arquivos (PDF, Excel, CSV, TXT, JSON).
    O sistema lê o arquivo, extrai nós e conexões e atualiza o grafo.
    """
    print(f"Usuário {current_user['username']} enviando arquivo: {file.filename}")

    try:
        content = await file.read()

        # 1. O Parser converte o binário do arquivo em estrutura de Grafo
        graph_data = parser.parse(file.filename, content)

        # 2. O Recommender carrega essa estrutura na memória
        n_nodes, n_edges = recommender.load_data(graph_data)

        return {
            "status": "Processado com sucesso",
            "filename": file.filename,
            "summary": {
                "nodes_total": n_nodes,
                "edges_total": n_edges
            },
            "preview_nodes": graph_data["nodes"][:5]  # Debug visual
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Erro de formato: {str(e)}")
    except Exception as e:
        print(f"Erro interno: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar arquivo.")


@app.post("/ingest-json")
async def ingest_json(
        data: dict = Body(...),
        current_user: dict = Depends(get_current_user)
):
    """
    [DEV] Envia um JSON direto com nós e arestas para popular o grafo manualmente.
    Formato: {"nodes": [{"id": "A", "type": "x"}], "edges": [{"source": "A", "target": "B"}]}
    """
    try:
        n_nodes, n_edges = recommender.load_data(data)
        return {"msg": "Dados JSON carregados", "stats": f"{n_nodes} nós, {n_edges} arestas."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 3. ROTA DE RECOMENDAÇÃO (Core)
# ==========================================

@app.get("/recommendations")
def get_recommendations(
        target_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        limit: int = 5,
        current_user: dict = Depends(get_current_user)
):
    """
    Gera recomendações baseadas no grafo atual.

    - **entity_id**: Quem é o ponto de partida? (Ex: 'Joao', 'ClienteX').
                     Se vazio, usa o usuário logado.
    - **target_type**: O que você procura? (Ex: 'cidade', 'musica', 'vaga').
                       Se vazio, traz qualquer coisa relevante.
    """
    # Define quem é o "sujeito" da recomendação
    subject = entity_id if entity_id else current_user.get("username")

    print(f"Buscando recomendações para: {subject} | Filtro: {target_type}")

    # Verifica se o sujeito existe no grafo
    if subject not in recommender.graph.adj_list:
        return {
            "subject": subject,
            "warning": "Entidade não encontrada no grafo atual.",
            "recommendations": [],
            "tip": "Faça upload de um arquivo ou use /ingest-json para adicionar dados sobre este sujeito."
        }

    # Roda o algoritmo
    recs = recommender.recommend(subject, target_type=target_type, top_n=limit)

    return {
        "subject": subject,
        "looking_for": target_type if target_type else "Tudo",
        "recommendations": recs
    }


# ==========================================
# 4. ROTA DE DIAGNÓSTICO
# ==========================================
@app.get("/graph-stats")
def get_stats(current_user: dict = Depends(get_current_user)):
    """Retorna o tamanho atual do grafo na memória."""
    return {
        "total_nodes": len(recommender.graph.nodes),
        "total_edges_mapped": len(recommender.graph.adj_list),
        "node_types": list(set(d['type'] for d in recommender.graph.nodes.values()))
    }