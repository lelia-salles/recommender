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


def check_columns():
    print("--- VERIFICANDO ESTRUTURA REAL DO BANCO ---")
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        # Pergunta ao Postgres quais colunas existem na tabela users
        cur.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = 'users';
                    """)

        columns = cur.fetchall()

        print(f"Colunas encontradas na tabela 'users': {len(columns)}")
        found_email = False
        found_sensitive = False

        for col_name, dtype in columns:
            print(f" - {col_name} ({dtype})")
            if col_name == 'email_hash': found_email = True
            if col_name == 'sensitive_data_hash': found_sensitive = True

        print("\n--- RESULTADO ---")
        if found_email and found_sensitive:
            print("✅ SUCESSO! As colunas EXISTEM.")
            print("👉 O erro que você vê é apenas visual do seu editor (cache).")
            print("👉 Pode rodar o seed_db.py ou a API que vai funcionar.")
        else:
            print("❌ ERRO REAL: As colunas NÃO foram criadas.")
            print("👉 Você precisa rodar o update_db_users.py novamente ou verificar o nome do banco.")

        conn.close()

    except Exception as e:
        print(f"Erro de conexão: {e}")


if __name__ == "__main__":
    check_columns()