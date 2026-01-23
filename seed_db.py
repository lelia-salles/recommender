import os
import psycopg2
import bcrypt
import hashlib
from dotenv import load_dotenv

load_dotenv()

DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "recommender"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASS", "password"),
}

SECRET_KEY = os.getenv("SECRET_KEY", "minha_chave_secreta_super_segura")
SECURITY_PEPPER = os.getenv("SECURITY_PEPPER", "pimenta_secreta_para_dados_sensiveis")


def get_password_hash(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def hash_sensitive_data(data):
    if not data: return None
    key_bytes = SECURITY_PEPPER.encode('utf-8')[:64]
    h = hashlib.blake2b(key=key_bytes, digest_size=32)
    h.update(data.encode('utf-8'))
    return h.hexdigest()


def seed_database():
    print("--- SEED: Povoando Banco com Mascaramento de Dados ---")
    conn = None
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        conn.set_session(autocommit=True)

        with conn.cursor() as cur:
            # 1. Limpeza
            print("1. Limpando tabelas...")
            cur.execute("TRUNCATE TABLE public.interactions CASCADE;")
            cur.execute("TRUNCATE TABLE public.users CASCADE;")

            # 2. Criar Usuários
            print("2. Criando Usuários...")

            mock_users = [
                ('U1', 'senha123', 'joao@teste.com', '111.111.111-11'),
                ('U2', 'senha123', 'maria@teste.com', '222.222.222-22'),
                ('U3', 'senha123', 'pedro@teste.com', '333.333.333-33'),
                ('U4', 'senha123', 'ana@teste.com', '444.444.444-44'),
                ('U5', 'senha123', 'lucas@teste.com', '555.555.555-55')
            ]

            for u, pwd, email, cpf in mock_users:
                p_hash = get_password_hash(pwd)
                e_hash = hash_sensitive_data(email)
                s_hash = hash_sensitive_data(cpf)

                # MÁSCARA: Geramos um email falso apenas para cumprir a regra NOT NULL do banco
                email_mask = f"masked_{u.lower()}@protegido.local"

                cur.execute(
                    """
                    INSERT INTO public.users
                        (username, email, password_hash, email_hash, sensitive_data_hash)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (u, email_mask, p_hash, e_hash, s_hash)
                )

            # 3. Criar Interações
            print("3. Criando Interações...")
            interactions = [
                ('U1', 'Celular_X', 5.0), ('U1', 'Fone_Y', 4.5),
                ('U2', 'Fone_Y', 4.0), ('U2', 'Livro_A', 5.0),
                ('U3', 'Livro_A', 4.5), ('U3', 'Livro_B', 3.0),
                ('U4', 'Livro_B', 5.0), ('U4', 'Notebook_Z', 5.0),
                ('U5', 'Notebook_Z', 2.0)
            ]

            for src, tgt, w in interactions:
                # Ida
                cur.execute(
                    "INSERT INTO public.interactions (source_id, target_id, weight) VALUES (%s, %s, %s)",
                    (src, tgt, w)
                )
                # Volta (Grafo não-direcionado)
                cur.execute(
                    "INSERT INTO public.interactions (source_id, target_id, weight) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                    (tgt, src, w)
                )

            print(f"✅ Sucesso! Dados inseridos. Emails reais ocultados.")

    except Exception as e:
        print(f"❌ Erro ao povoar banco: {e}")
    finally:
        if conn: conn.close()


if __name__ == "__main__":
    seed_database()