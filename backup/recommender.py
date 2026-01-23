from collections import deque, defaultdict


class Graph:
    def __init__(self):
        self.adj_list = defaultdict(list)
        self.nodes = {}  # Armazena metadados: {"NodeA": {"type": "city", "data": {...}}}

    def add_node(self, node_id, node_type, **kwargs):
        self.nodes[node_id] = {"type": node_type, "properties": kwargs}

    def add_edge(self, u, v, weight=1):
        # Grafo não direcionado (A conexão vale para os dois lados)
        self.adj_list[u].append(v)
        self.adj_list[v].append(u)

    def clear(self):
        self.adj_list = defaultdict(list)
        self.nodes = {}


class GenericRecommender:
    def __init__(self):
        self.graph = Graph()

    def load_data(self, data: dict):
        """
        Recebe um JSON completo com nós e arestas e popula o grafo.
        Estrutura esperada:
        {
            "nodes": [{"id": "SP", "type": "cidade"}, ...],
            "edges": [{"source": "Joao", "target": "SP"}, ...]
        }
        """
        self.graph.clear()  # Limpa dados antigos

        for node in data.get("nodes", []):
            self.graph.add_node(node["id"], node["type"])

        for edge in data.get("edges", []):
            self.graph.add_edge(edge["source"], edge["target"])

        return len(self.graph.nodes), len(data.get("edges", []))

    def recommend(self, entity_id, target_type=None, top_n=3):
        """
        Recomenda entidades conectadas indiretamente.
        entity_id: O ponto de partida (ex: O Músico, ou um Fã)
        target_type: O tipo de coisa que queremos recomendar (ex: "cidade", "vaga")
        """
        if entity_id not in self.graph.adj_list:
            return []

        # Itens já conectados diretamente (para não recomendar o óbvio)
        connected_items = set(self.graph.adj_list[entity_id])

        scores = defaultdict(int)

        # Lógica de Collaborative Filtering Genérica (Vizinho do Vizinho)
        # Passo 1: Quem/O que está conectado a mim?
        direct_neighbors = self.graph.adj_list[entity_id]

        for neighbor in direct_neighbors:
            # Passo 2: O que está conectado aos meus vizinhos?
            neighbor_connections = self.graph.adj_list[neighbor]

            for candidate in neighbor_connections:
                if candidate == entity_id: continue
                if candidate in connected_items: continue

                # Passo 3: Filtrar pelo TIPO desejado (se especificado)
                # Ex: Se João quer saber CIDADES, ignoramos outros MÚSICOS.
                candidate_type = self.graph.nodes.get(candidate, {}).get("type")

                if target_type and candidate_type != target_type:
                    continue

                scores[candidate] += 1

        # Ordenar e retornar
        sorted_recs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [item for item, score in sorted_recs[:top_n]]