from app.core.graph import Graph

def build_graph(interactions):
    graph = Graph()

    for interaction in interactions:
        graph.add_edge(
            interaction.source_id,
            interaction.target_id,
            interaction.weight
        )

    return graph


