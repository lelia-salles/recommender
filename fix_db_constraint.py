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


def fix_constraints():
    print("--- CORRIGINDO RESTRIÇÕES DO BANCO ---")
    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        # 1. Torna a coluna 'email' opcional (DROP NOT NULL)
        # Isso permite que salvemos usuários sem expor o e-mail real
        print("1. Removendo obrigatoriedade do campo 'email' antigo...")
        cur.execute("ALTER TABLE public.users ALTER COLUMN email DROP NOT NULL;")

        # Opcional: Se quiser remover a coluna antiga de vez, descomente a linha abaixo:
        # cur.execute("ALTER TABLE public.users DROP COLUMN email;")

        conn.commit()
        print("✅ Sucesso! A tabela 'users' agora aceita e-mails nulos.")

    except psycopg2.errors.UndefinedColumn:
        print("⚠️ Aviso: A coluna 'email' parece não existir ou já foi removida. Tudo certo.")
        conn.rollback()
    except Exception as e:
        print(f"❌ Erro ao corrigir banco: {e}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()


if __name__ == "__main__":
    fix_constraints()