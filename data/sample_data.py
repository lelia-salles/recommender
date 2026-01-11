from app.models.interaction import Interaction
from app.core.graph import Graph

# Opcional: grafo de exemplo
def build_sample_graph():
    graph = Graph()
    graph.add_edge("U1", "COURSE_1", 5)
    graph.add_edge("U1", "CONCERT_1", 3)
    graph.add_edge("U1", "PRODUCT_1", 4)
    graph.add_edge("COURSE_1", "COURSE_2", 2)
    graph.add_edge("COURSE_2", "COURSE_3", 1)
    graph.add_edge("CONCERT_1", "SHOW_1", 2)
    graph.add_edge("SHOW_1", "SHOW_2", 1)
    graph.add_edge("PRODUCT_1", "PRODUCT_2", 2)
    graph.add_edge("PRODUCT_2", "PRODUCT_3", 1)
    return graph

# Lista de interações (interessante para build_graph)
interactions = [
    Interaction("U1", "P1", 1.0, "buy"),
    Interaction("U1", "P2", 0.8, "view"),
    Interaction("U2", "P2", 1.0, "buy"),
    Interaction("U2", "P3", 0.9, "view"),
    Interaction("U3", "P1", 0.7, "like"),
]
