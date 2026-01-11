import os
import psycopg2
from dotenv import load_dotenv
from app.core.security import get_password_hash, encrypt_data

# Carrega variáveis do .env
load_dotenv()


def create_users():
    # Conecta no banco
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "recommender_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASS", "password")
        )
        cur = conn.cursor()
        print("Conectado ao banco de dados.")
    except Exception as e:
        print(f"Erro ao conectar: {e}")
        return

    # Lista de usuários para criar (baseado no seu sample_data)
    # Formato: (username, senha, dado_sensivel)
    users_to_create = [
        ("U1", "senha123", "CPF-111.111.111-11"),
        ("U2", "senha456", "CPF-222.222.222-22"),
        ("U3", "senha789", "CPF-333.333.333-33"),
    ]

    print("\n--- Criando Usuários ---")
    for username, password, sensitive_info in users_to_create:
        try:
            # 1. Gerar Hash da senha (segurança)
            pwd_hash = get_password_hash(password)

            # 2. Criptografar dado sensível (segurança)
            sensitive_encrypted = encrypt_data(sensitive_info)

            # 3. Inserir no Banco
            # Note que inserimos o 'username' também como 'id' para manter compatibilidade
            # com seu sample_data antigo que usa "U1", "U2" como IDs.
            # Se seu banco usa ID serial (número), precisaremos ajustar a tabela ou o código.
            # Vou assumir aqui que você quer manter "U1" como o identificador.

            # OBS: Se sua tabela 'users' tem ID SERIAL (automático), não forçamos o ID.
            # Mas para o recommender funcionar com "U1", o username deve ser "U1".

            cur.execute("""
                        INSERT INTO users (username, email, password_hash, sensitive_data)
                        VALUES (%s, %s, %s, %s) ON CONFLICT (username) DO NOTHING
                RETURNING id;
                        """, (username, f"{username.lower()}@email.com", pwd_hash, sensitive_encrypted))

            user_id = cur.fetchone()

            if user_id:
                print(f"✅ Usuário {username} criado com sucesso (ID Banco: {user_id[0]})")
            else:
                print(f"⚠️ Usuário {username} já existe.")

        except Exception as e:
            print(f"❌ Erro ao criar {username}: {e}")
            conn.rollback()

    conn.commit()
    cur.close()
    conn.close()
    print("\nProcesso finalizado.")


if __name__ == "__main__":
    create_users()