import os
import psycopg2
import pandas as pd
import networkx as nx
import joblib
from collections import deque
from dotenv import load_dotenv
# Certifique-se que o lsh_service.py foi criado no passo anterior
from app.services.lsh_service import MinHashLSH

load_dotenv()

MODEL_PATH = "app/services/model_recommender.pkl"

DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "recommender"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASS", "password"),
}


class HybridRecommender:
    def __init__(self):
        self.graph = nx.Graph()
        self.model_artifacts = None
        # Inicializa LSH com threshold 0.2 para testes (pega vizinhos com 20% de similaridade)
        self.lsh = MinHashLSH(threshold=0.2)
        print("--- INICIALIZANDO RECOMENDADOR HÍBRIDO + LSH ---")
        self._load_resources()

    def _load_resources(self):
        try:
            print(f"1. Conectando no banco: {DB_PARAMS['database']}...")
            conn = psycopg2.connect(**DB_PARAMS)

            # Carrega interações existentes
            query = "SELECT source_id, target_id, weight FROM public.interactions"
            df = pd.read_sql(query, conn)
            conn.close()

            print(f"2. Linhas encontradas no banco: {len(df)}")

            if df.empty:
                print("!!! ALERTA: O BANCO PARECE VAZIO. O GRAFO INICIARÁ VAZIO. !!!")
            else:
                # --- [NOVO BLOCO LSH] ---
                print("   > Populando índice LSH...")
                # Agrupa interações por usuário: {'U1': {'ItemA', 'ItemB'}, ...}
                user_items = df.groupby('source_id')['target_id'].apply(set).to_dict()

                for user, items in user_items.items():
                    self.lsh.add_user(user, items)
                print(f"   > LSH indexado com {len(user_items)} usuários.")
                # ------------------------

            # Cria o grafo NetworkX
            self.graph = nx.from_pandas_edgelist(
                df, 'source_id', 'target_id', ['weight'], create_using=nx.Graph()
            )
            print(f"3. Grafo montado: {self.graph.number_of_nodes()} nós, {self.graph.number_of_edges()} arestas")

            # Carrega modelo ML
            if os.path.exists(MODEL_PATH):
                self.model_artifacts = joblib.load(MODEL_PATH)
                print("4. Modelo ML carregado com sucesso.")
            else:
                print("4. AVISO: Modelo .pkl não encontrado. Usando apenas lógica de Grafo.")

        except Exception as e:
            print(f"!!! ERRO FATAL AO CARREGAR RECURSOS: {e}")

    def ingest_data(self, graph_data: dict):
        """
        Recebe dados do Parser e salva no PostgreSQL.
        """
        edges = graph_data.get("edges", [])
        if not edges:
            return 0

        print(f"--- INGESTÃO: Salvando {len(edges)} novas conexões no Banco... ---")

        saved_count = 0
        conn = None
        try:
            conn = psycopg2.connect(**DB_PARAMS)
            cur = conn.cursor()

            for edge in edges:
                src = edge.get("source")
                tgt = edge.get("target")

                if not src or not tgt: continue

                insert_query = """
                               INSERT INTO public.interactions (source_id, target_id, weight, interaction_type)
                               VALUES (%s, %s, %s, %s)
                               ON CONFLICT (source_id, target_id, interaction_type) DO NOTHING; \
                               """

                cur.execute(insert_query, (src, tgt, 1.0, "upload_file"))
                cur.execute(insert_query, (tgt, src, 1.0, "upload_file_reverse"))

                # Atualiza memória RAM e LSH
                self.graph.add_edge(src, tgt, weight=1.0)

                # Nota: Para atualizar o LSH em tempo real seria necessário recalcular a assinatura do usuário.
                # Por simplicidade, o LSH é atualizado apenas no reinício do servidor ou se chamarmos _load_resources.

                saved_count += 1

            conn.commit()
            cur.close()
            print(f"✅ Sucesso: {saved_count} arestas processadas e salvas.")
            return saved_count

        except Exception as e:
            print(f"❌ Erro ao salvar no banco: {e}")
            if conn: conn.rollback()
            raise e
        finally:
            if conn: conn.close()

    def bfs_traversal(self, start_node, limit=20):
        if start_node not in self.graph: return set()
        visited = {start_node}
        queue = deque([(start_node, 0)])
        candidates = set()

        while queue and len(candidates) < limit:
            curr, depth = queue.popleft()
            for neighbor in self.graph.neighbors(curr):
                if neighbor not in visited:
                    visited.add(neighbor)
                    if not neighbor.startswith('U'):
                        candidates.add(neighbor)
                    queue.append((neighbor, depth + 1))
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

    def lsh_traversal(self, user_id, limit=20):
        """
        Estratégia LSH: Encontra usuários globais similares e sugere o que eles compraram.
        """
        print(f"   > [LSH] Buscando sósias de {user_id}...")
        # Chama o serviço LSH que criamos
        similar_users = self.lsh.find_similar_users(user_id)

        candidates = set()

        # Pega os Top 5 usuários mais parecidos
        for other_user, score in similar_users[:5]:
            print(f"     - Vizinho LSH encontrado: {other_user} (Score: {score:.2f})")

            # Pega itens desse vizinho no Grafo
            if other_user in self.graph:
                neighbors = self.graph.neighbors(other_user)
                for item in neighbors:
                    if not item.startswith('U'):
                        candidates.add(item)

            if len(candidates) >= limit:
                break

        return candidates

    def get_recommendations(self, user_id, top_k=5):
        print(f"\n--- PROCESSANDO RECOMENDAÇÃO PARA {user_id} ---")

        # 1. Busca Multi-Estratégia (BFS + DFS + LSH)
        candidates_bfs = self.bfs_traversal(user_id)
        candidates_dfs = self.dfs_traversal(user_id)
        candidates_lsh = self.lsh_traversal(user_id)

        # Une todos os candidatos (Set garante unicidade)
        candidates = list(candidates_bfs.union(candidates_dfs).union(candidates_lsh))

        # 2. Filtro: Remove o que o usuário já consumiu
        if user_id in self.graph:
            interacted = set(self.graph.neighbors(user_id))
            candidates = [c for c in candidates if c not in interacted]

        if not candidates:
            return []

        # 3. Ranking ML
        if self.model_artifacts:
            try:
                model = self.model_artifacts["model"]
                pagerank = self.model_artifacts["pagerank"]
                degree = self.model_artifacts["degree"]

                features = []
                valid_candidates = []

                for item in candidates:
                    pr_val = pagerank.get(item, 0)
                    deg_val = degree.get(item, 0)
                    features.append([pr_val, deg_val])
                    valid_candidates.append(item)

                if valid_candidates:
                    scores = model.predict(features)
                    results = sorted(zip(valid_candidates, scores), key=lambda x: x[1], reverse=True)
                    return results[:top_k]
            except Exception as e:
                print(f"Erro no ML Ranking: {e}. Retornando ordem padrão.")

        return [(c, 1.0) for c in candidates[:top_k]]