import os
import psycopg2
import pandas as pd
import networkx as nx
import joblib
from collections import deque
from dotenv import load_dotenv

load_dotenv()

MODEL_PATH = "app/services/model_recommender.pkl"

# VERIFICAÇÃO 1: Garanta que o nome do banco está correto aqui
DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "recommender"),  # <--- TEM QUE SER 'recommender'
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASS", "password"),
}


class HybridRecommender:
    def __init__(self):
        self.graph = nx.Graph()
        self.model_artifacts = None
        print("--- INICIALIZANDO RECOMENDADOR ---")
        self._load_resources()

    def _load_resources(self):
        try:
            print(f"1. Conectando no banco: {DB_PARAMS['database']}...")
            conn = psycopg2.connect(**DB_PARAMS)
            query = "SELECT source_id, target_id, weight FROM public.interactions"
            df = pd.read_sql(query, conn)
            conn.close()

            print(f"2. Linhas encontradas no banco: {len(df)}")

            if df.empty:
                print("!!! ALERTA: O BANCO PARECE VAZIO !!!")

            self.graph = nx.from_pandas_edgelist(
                df, 'source_id', 'target_id', ['weight'], create_using=nx.Graph()
            )
            print(f"3. Grafo montado: {self.graph.number_of_nodes()} nós, {self.graph.number_of_edges()} arestas")

            if os.path.exists(MODEL_PATH):
                self.model_artifacts = joblib.load(MODEL_PATH)
                print("4. Modelo ML carregado com sucesso.")
            else:
                print("4. AVISO: Modelo .pkl não encontrado.")

        except Exception as e:
            print(f"!!! ERRO FATAL AO CARREGAR RECURSOS: {e}")

    def bfs_traversal(self, start_node, limit=20):
        print(f"   > Iniciando BFS para: {start_node}")
        if start_node not in self.graph:
            print(f"   > ERRO: Usuário {start_node} não está no Grafo!")
            return set()

        visited = {start_node}
        queue = deque([(start_node, 0)])
        candidates = set()

        while queue and len(candidates) < limit:
            curr, depth = queue.popleft()

            for neighbor in self.graph.neighbors(curr):
                if neighbor not in visited:
                    visited.add(neighbor)
                    # Adiciona se NÃO for usuário (assumindo que Users começam com 'U')
                    if not neighbor.startswith('U'):
                        candidates.add(neighbor)
                    queue.append((neighbor, depth + 1))

        print(f"   > Candidatos encontrados no BFS: {candidates}")
        return candidates

    def dfs_traversal(self, start_node, max_depth=3, limit=20):
        if start_node not in self.graph: return set()

        visited = {start_node}
        stack = [(start_node, 0)]
        candidates = set()

        while stack and len(candidates) < limit:
            curr, depth = stack.pop()
            if depth >= max_depth: continue

            for neighbor in self.graph.neighbors(curr):
                if neighbor not in visited:
                    visited.add(neighbor)
                    if not neighbor.startswith('U'):
                        candidates.add(neighbor)
                    stack.append((neighbor, depth + 1))
        return candidates

    def get_recommendations(self, user_id, top_k=5):
        print(f"\n--- PROCESSANDO RECOMENDAÇÃO PARA {user_id} ---")

        # 1. Busca
        candidates_bfs = self.bfs_traversal(user_id)
        candidates_dfs = self.dfs_traversal(user_id)
        candidates = list(candidates_bfs.union(candidates_dfs))

        # 2. Filtro
        if user_id in self.graph:
            interacted = set(self.graph.neighbors(user_id))
            print(f"   > Itens que {user_id} já comprou: {interacted}")
            candidates = [c for c in candidates if c not in interacted]
            print(f"   > Candidatos finais (novos): {candidates}")

        if not candidates:
            print("   > Nenhum candidato restou. Retornando vazio.")
            return []

        # 3. Ranking ML
        if not self.model_artifacts:
            return [(c, 1.0) for c in candidates[:top_k]]

        model = self.model_artifacts["model"]
        pagerank = self.model_artifacts["pagerank"]
        degree = self.model_artifacts["degree"]

        features = []
        valid_candidates = []

        for item in candidates:
            # Proteção contra itens que não estavam no treino
            pr_val = pagerank.get(item, 0)
            deg_val = degree.get(item, 0)
            features.append([pr_val, deg_val])
            valid_candidates.append(item)

        scores = model.predict(features)
        results = sorted(zip(valid_candidates, scores), key=lambda x: x[1], reverse=True)
        return results[:top_k]


recommender_engine = HybridRecommender()