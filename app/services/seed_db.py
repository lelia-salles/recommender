import os
import psycopg2
import bcrypt
from dotenv import load_dotenv

load_dotenv()

# Ajustei o default para 'recommender' conforme seu banco real
DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "recommender"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASS", "password"),
}


def get_password_hash(password):
    """Gera hash usando bcrypt puro"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def seed_database():
    print("--- Iniciando Povoamento do Banco de Dados (Seed) ---")
    conn = psycopg2.connect(**DB_PARAMS)
    conn.set_session(autocommit=True)

    try:
        with conn.cursor() as cur:
            # 1. Limpar dados antigos
            print("Limpando tabelas antigas...")
            cur.execute("TRUNCATE TABLE public.interactions CASCADE;")
            cur.execute("TRUNCATE TABLE public.users CASCADE;")

            # 2. Criar Usuários (U1 a U5)
            print("Inserindo Usuários...")
            users = ['U1', 'U2', 'U3', 'U4', 'U5']
            default_pass_hash = get_password_hash("senha123")

            for u in users:
                # Geramos um email fictício baseada no nome
                fake_email = f"{u.lower()}@teste.com"

                # ATENÇÃO: Adicionei a coluna 'email' no INSERT abaixo
                cur.execute(
                    """
                    INSERT INTO public.users (username, email, password_hash)
                    VALUES (%s, %s, %s)
                    """,
                    (u, fake_email, default_pass_hash)
                )

            # 3. Criar Interações
            print("Inserindo Interações (Arestas do Grafo)...")
            interactions = [
                ('U1', 'Celular_X', 5.0),
                ('U1', 'Fone_Y', 4.5),
                ('U2', 'Fone_Y', 4.0),
                ('U2', 'Livro_A', 5.0),
                ('U3', 'Livro_A', 4.5),
                ('U3', 'Livro_B', 3.0),
                ('U4', 'Livro_B', 5.0),
                ('U4', 'Notebook_Z', 5.0),
                ('U5', 'Notebook_Z', 2.0)
            ]

            for src, tgt, w in interactions:
                cur.execute(
                    """
                    INSERT INTO public.interactions (source_id, target_id, weight)
                    VALUES (%s, %s, %s)
                    """,
                    (src, tgt, w)
                )

            print(f"Sucesso! {len(users)} usuários e {len(interactions)} interações criadas.")

    except Exception as e:
        print(f"Erro ao povoar banco: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    seed_database()