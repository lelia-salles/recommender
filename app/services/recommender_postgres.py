import psycopg2
from contextlib import contextmanager


class PostgresRecommender:
    def __init__(self, db_config):
        self.db_config = db_config

    @contextmanager
    def get_cursor(self):
        conn = psycopg2.connect(**self.db_config)
        try:
            yield conn.cursor()
        finally:
            conn.close()

    def recommend(self, user_id, limit=5, max_depth=3):
        query = """
                WITH RECURSIVE graph_traversal AS (
                    -- Nível 1
                    SELECT target_id, weight, 1 as depth
                    FROM interactions
                    WHERE source_id = %s

                    UNION ALL

                    -- Nível N
                    SELECT i.target_id, i.weight, gt.depth + 1
                    FROM interactions i
                             INNER JOIN graph_traversal gt ON i.source_id = gt.target_id
                    WHERE gt.depth < %s)
                SELECT target_id, SUM(weight / (depth + 1)) as total_score
                FROM graph_traversal
                -- Remove itens que o próprio usuário já interagiu (opcional, mas recomendado)
                WHERE target_id NOT IN (SELECT target_id \
                                        FROM interactions \
                                        WHERE source_id = %s)
                  -- Remove o próprio usuário se ele aparecer nos resultados
                  AND target_id != %s
                GROUP BY target_id
                ORDER BY total_score DESC
                    LIMIT %s; \
                """

        with self.get_cursor() as cur:
            # Passamos os parâmetros: user_id, max_depth, user_id, user_id, limit
            cur.execute(query, (user_id, max_depth, user_id, user_id, limit))
            results = cur.fetchall()

            # Retorna lista de tuplas (item, score)
            return results


# --- Exemplo de Uso ---
if __name__ == "__main__":
    db_config = {
        "dbname": "recommender_db",
        "user": "postgres",
        "password": "password",
        "host": "localhost"
    }

    rec_service = PostgresRecommender(db_config)
    recommendations = rec_service.recommend("U1", limit=5, max_depth=3)

    print("Recomendações via Postgres:")
    for item, score in recommendations:
        print(f"Item: {item} | Score: {score:.4f}")