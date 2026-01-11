import os
import psycopg2
from dotenv import load_dotenv
from app.core.security import verify_password, create_access_token

load_dotenv()


def login(username, password_attempt):
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "recommender_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASS", "password")
        )
        cur = conn.cursor()

        # Busca o hash no banco
        cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
        res = cur.fetchone()
        conn.close()

        if not res:
            print(f"❌ Usuário {username} não encontrado no banco.")
            return

        stored_hash = res[0]

        # Verifica a senha usando o bcrypt novo
        if verify_password(password_attempt, stored_hash):
            print(f"✅ SUCESSO! Senha correta para {username}.")
            token = create_access_token({"sub": username})
            print(f"🔑 Token JWT Gerado: {token[:20]}...")  # Mostra só o começo
        else:
            print(f"❌ FRACASSO! Senha errada para {username}.")

    except Exception as e:
        print(f"Erro de conexão: {e}")


if __name__ == "__main__":
    print("--- Testando Login ---")
    login("U1", "senha123")  # Deve funcionar
    login("U1", "senhaerrada")  # Deve falhar