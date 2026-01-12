import os
import psycopg2
from typing import List, Tuple, Dict, Any
from dotenv import load_dotenv
from collections import deque, defaultdict


# 1. Estrutura básica do Grafo
class Graph:
    def __init__(self):
        self.adj_list = defaultdict(list)
        self.nodes = {}  # Armazena metadados: {"U1": {"type": "user"}, "P1": {"type": "product"}}

    def add_node(self, node_id, node_type):
        self.nodes[node_id] = {"type": node_type}

    def add_edge(self, u, v):
        # Grafo não direcionado (se U1 comprou P1, P1 foi comprado por U1)
        self.adj_list[u].append(v)
        self.adj_list[v].append(u)


# 2. A Classe Wrapper que o erro estava reclamando
class HybridRecommender:
    def __init__(self):
        self.graph = Graph()

    def recommend(self, user_id, top_n=3):
        """
        Lógica de recomendação baseada em vizinhos (Quem comprou isso, também comprou...)
        """
        if user_id not in self.graph.adj_list:
            return []

        # Itens que o usuário JÁ comprou (para não recomendar de novo)
        purchased_items = set(self.graph.adj_list[user_id])

        # Pontuação de recomendação
        scores = defaultdict(int)

        # Passo 1: Achar produtos comprados pelo usuário alvo
        # (user_id) -> [P1, P2]
        user_products = self.graph.adj_list[user_id]

        for product in user_products:
            # Passo 2: Achar outros usuários que compraram esses mesmos produtos
            # (P1) -> [U2, U3]
            similar_users = self.graph.adj_list[product]

            for other_user in similar_users:
                if other_user == user_id:
                    continue  # Pula o próprio usuário

                # Passo 3: Achar produtos que esses "outros usuários" compraram
                # (U2) -> [P3, P4]
                other_user_products = self.graph.adj_list[other_user]

                for potential_recommendation in other_user_products:
                    # Só recomenda se for PRODUTO e se o usuário alvo AINDA NÃO comprou
                    if (self.graph.nodes.get(potential_recommendation, {}).get("type") == "product" and
                            potential_recommendation not in purchased_items):
                        # Aumenta o score (quanto mais gente comprou, melhor)
                        scores[potential_recommendation] += 1

        # Ordenar pelos mais recomendados
        sorted_recs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [item for item, score in sorted_recs[:top_n]]