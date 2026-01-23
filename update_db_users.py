import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "recommender"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASS", "password"),
}


def update_database_schema():
    print("--- INICIANDO MIGRAÇÃO DE SEGURANÇA (SCHEMA UPDATE) ---")

    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        # 1. Adicionar colunas de Hash (Blind Indexing)
        # Usamos VARCHAR(128) para garantir espaço para o Blake2b (que gera 64 chars) e sobrar.
        print("1. Adicionando colunas de Hash na tabela 'users'...")

        alter_queries = [
            "ALTER TABLE public.users ADD COLUMN IF NOT EXISTS email_hash VARCHAR(128);",
            "ALTER TABLE public.users ADD COLUMN IF NOT EXISTS sensitive_data_hash VARCHAR(128);"
        ]

        for q in alter_queries:
            cur.execute(q)

        # 2. Criar Índices para Busca Rápida
        # O segredo do Blind Indexing é a velocidade. Sem índice, a busca fica lenta.
        print("2. Criando índices de performance...")

        index_queries = [
            "CREATE INDEX IF NOT EXISTS idx_users_email_hash ON public.users(email_hash);",
            "CREATE INDEX IF NOT EXISTS idx_users_sensitive_hash ON public.users(sensitive_data_hash);"
        ]

        for q in index_queries:
            cur.execute(q)

        conn.commit()
        print("✅ Sucesso! Tabela 'users' atualizada com colunas seguras.")

        # 3. Verificação (Opcional)
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users';")
        cols = [row[0] for row in cur.fetchall()]
        print(f"   > Colunas atuais na tabela: {cols}")

    except Exception as e:
        print(f"❌ Erro ao atualizar banco: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()


if __name__ == "__main__":
    update_database_schema()