import os
import psycopg2
from typing import List, Tuple, Dict, Any
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Configurações do Banco de Dados
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "recommender_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "password")


def get_db_connection():
    """
    Estabelece conexão com o PostgreSQL.
    Define client_encoding='utf-8' para evitar erros com senhas/caracteres especiais.
    """
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        client_encoding='utf-8'
    )
    return conn


def recommend(user_id: str, limit: int = 5, depth: int = 3, config: Dict[str, Any] = None) -> List[Tuple[str, float]]:
    """
    Gera recomendações usando Recursive CTE (Common Table Expression) no PostgreSQL.
    Isso substitui o grafo em memória, permitindo escalar para milhões de dados.

    Args:
        user_id: ID do utilizador (nó de origem).
        limit: Quantidade máxima de itens a retornar.
        depth: Profundidade da busca no grafo (vizinhos dos vizinhos).
        config: Dicionário opcional para sobrescrever limit/depth.

    Returns:
        Lista de tuplas: [('PRODUTO_X', 2.5), ('PRODUTO_Y', 1.2), ...]
    """

    # Permite sobrescrever configurações via dicionário
    if config:
        limit = config.get("limit", limit)
        depth = config.get("depth", depth)

    conn = get_db_connection()
    results = []

    try:
        with conn.cursor() as cur:
            # Query otimizada com schema 'public.' explícito
            # O uso de %s é obrigatório para evitar SQL Injection via psycopg2
            # noinspection SqlNoDataSourceInspection,SqlResolve
            query = """
                        WITH RECURSIVE graph_traversal AS (
                            -- 1. Caso Base: Vizinhos diretos (Nível 1)
                            SELECT 
                                t1.target_id, 
                                t1.weight, 
                                1 as current_depth
                            FROM public.interactions t1
                            WHERE t1.source_id = %s

                            UNION ALL

                            -- 2. Passo Recursivo: Vizinhos dos vizinhos (Nível N)
                            SELECT 
                                i.target_id, 
                                i.weight, 
                                gt.current_depth + 1
                            FROM public.interactions i
                            INNER JOIN graph_traversal gt ON i.source_id = gt.target_id
                            WHERE gt.current_depth < %s
                        )

                        -- 3. Agregação e Cálculo do Score Final
                        SELECT 
                            gt_final.target_id, 
                            SUM(gt_final.weight / (gt_final.current_depth + 1)) as score
                        FROM graph_traversal gt_final

                        -- Filtros:
                        WHERE gt_final.target_id != %s -- Não recomendar o próprio usuário
                          AND gt_final.target_id NOT IN (
                            -- Não recomendar itens com os quais o usuário JÁ interagiu diretamente
                            SELECT existing.target_id
                            FROM public.interactions existing
                            WHERE existing.source_id = %s
                        )
                        GROUP BY gt_final.target_id
                        ORDER BY score DESC
                        LIMIT %s;
                        """

            # Parâmetros na ordem exata dos %s:
            # 1. source_id (Caso Base)
            # 2. max_depth (Limite Recursão)
            # 3. user_id (Filtro != self)
            # 4. user_id (Subquery NOT IN)
            # 5. limit (Resultado final)
            params = (user_id, depth, user_id, user_id, limit)

            cur.execute(query, params)
            results = cur.fetchall()

    except Exception as e:
        print(f"Erro ao gerar recomendações no banco de dados: {e}")
        # Em produção, aqui você usaria um logger (ex: logging.error(e))

    finally:
        if conn:
            conn.close()

    return results