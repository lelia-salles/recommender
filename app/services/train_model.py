import os
import psycopg2
import pandas as pd
import networkx as nx
import numpy as np
import joblib
from sklearn.ensemble import RandomForestRegressor
from dotenv import load_dotenv

# Carrega ambiente para conectar no banco
load_dotenv()

MODEL_PATH = "app/services/model_recommender.pkl"


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "recommender"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASS", "password")
    )


def train_and_save():
    print("--- Iniciando Pipeline de Treinamento Real ---")

    # 1. Carregar Dados Reais do Postgres
    conn = get_db_connection()
    query = "SELECT source_id, target_id, weight FROM public.interactions"
    df = pd.read_sql(query, conn)
    conn.close()

    if df.empty:
        print("Sem dados para treinar. Abortando.")
        return

    # 2. Construir o Grafo para Extrair Features Reais [cite: 6, 18]
    G = nx.from_pandas_edgelist(
        df, 'source_id', 'target_id', ['weight'], create_using=nx.Graph()
    )

    # 3. Engenharia de Features (O segredo do ML Real)
    # Calculamos métricas reais da topologia do grafo
    print("Calculando PageRank e Centralidade...")
    pagerank = nx.pagerank(G)
    degree_centrality = nx.degree_centrality(G)

    # 4. Preparar Dataset de Treino (Positivos + Negativos)
    # Precisamos ensinar ao modelo o que é uma conexão "Boa" (Existente) e "Ruim" (Inexistente)
    X = []
    y = []

    # Amostras POSITIVAS (As interações que existem)
    for _, row in df.iterrows():
        u, v, w = row['source_id'], row['target_id'], row['weight']
        # Features: [PageRank do Item, Grau do Item, Peso Original]
        feat = [pagerank.get(v, 0), degree_centrality.get(v, 0)]
        X.append(feat)
        y.append(w)  # O alvo é o peso real (ex: 5 estrelas)

    # Amostras NEGATIVAS (Criar exemplos do que NÃO recomendar para balancear)
    # Em produção, pegamos pares aleatórios que não têm aresta
    all_nodes = list(G.nodes())
    num_negatives = len(df) // 2  # Gera 50% de negativos

    for _ in range(num_negatives):
        u = np.random.choice(all_nodes)
        v = np.random.choice(all_nodes)
        if not G.has_edge(u, v) and u != v:
            feat = [pagerank.get(v, 0), degree_centrality.get(v, 0)]
            X.append(feat)
            y.append(0)  # O alvo é 0 (sem interesse)

    # 5. Treinar Modelo [cite: 10, 11]
    print(f"Treinando Random Forest com {len(X)} amostras...")
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X, y)

    # 6. Salvar Modelo e Métricas (Cache)
    # Salvamos também o PageRank para não recalcular na hora da recomendação
    artifacts = {
        "model": model,
        "pagerank": pagerank,
        "degree": degree_centrality
    }
    joblib.dump(artifacts, MODEL_PATH)
    print(f"Modelo salvo com sucesso em: {MODEL_PATH}")


if __name__ == "__main__":
    train_and_save()
