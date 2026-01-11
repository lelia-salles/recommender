import unittest

from data.sample_data import interactions
from app.core.graph_builder import build_graph
from app.services.recommender import recommend

class TestRecommenderSystem(unittest.TestCase):

    def setUp(self):
        self.graph = build_graph(interactions)

    def test_returns_list(self):
        self.assertIsInstance(recommend(self.graph, "U1"), list)

    def test_not_empty(self):
        self.assertGreater(len(recommend(self.graph, "U1")), 0)

    def test_limit(self):
        self.assertEqual(len(recommend(self.graph, "U1", limit=2)), 2)

    def test_unknown_user(self):
        self.assertEqual(recommend(self.graph, "UNKNOWN"), [])

if __name__ == "__main__":
    unittest.main()
