#Este teste cria um cenário controlado: o usuário tem dois caminhos possíveis para itens recomendados.
# Um caminho é feito apenas de interações fortes ("buy", peso 1.0) e o outro de interações fracas ("view", peso 0.5).
# O sistema deve recomendar o item do caminho forte primeiro

import unittest
from app.core.graph_builder import build_graph
from app.services.recommender import recommend
from app.models.interaction import Interaction


class TestWeightImpact(unittest.TestCase):

    def setUp(self):
        # Cenário:
        # U1 -> Comprou P_Forte (Peso 1.0)
        # U1 -> Viu P_Fraco   (Peso 0.5)
        #
        # P_Forte -> Conectado a U2 (que comprou P_Alvo_Forte)
        # P_Fraco -> Conectado a U3 (que viu P_Alvo_Fraco)

        self.interactions = [
            # Caminho Forte (Strong Path)
            Interaction("U1", "P_Connection_Strong", 1.0, "buy"),
            Interaction("U2", "P_Connection_Strong", 1.0, "buy"),
            Interaction("U2", "P_TARGET_STRONG", 1.0, "buy"),

            # Caminho Fraco (Weak Path)
            Interaction("U1", "P_Connection_Weak", 0.5, "view"),
            Interaction("U3", "P_Connection_Weak", 0.5, "view"),
            Interaction("U3", "P_TARGET_WEAK", 0.5, "view"),
        ]
        self.graph = build_graph(self.interactions)

    def test_strong_interactions_rank_higher(self):
        # Executa recomendação
        recs = recommend(self.graph, "U1", limit=2)

        # Extrai apenas os IDs da resposta (que é uma lista de tuplas ou objetos)
        # O retorno é [(item_id, score), ...]
        rec_ids = [item[0] for item in recs]

        print(f"\nOrdem da Recomendação: {rec_ids}")

        # O item do caminho de compras DEVE vir antes do item do caminho de views
        self.assertEqual(rec_ids[0], "P_TARGET_STRONG")
        self.assertEqual(rec_ids[1], "P_TARGET_WEAK")


if __name__ == "__main__":
    unittest.main()