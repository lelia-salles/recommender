import os
import psycopg2
from dotenv import load_dotenv
from data.sample_data import interactions

# 1. Carrega variáveis de ambiente (.env)
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "recommender"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD")
}


def load_data():
    conn = None
    try:
        if not DB_CONFIG["password"]:
            raise ValueError("Senha não encontrada. Verifique seu arquivo .env")

        print("Conectando ao banco de dados...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # --- PASSO 1: CRIAR ESTRUTURA (DDL) ---
        # Resolvemos o problema garantindo que a tabela existe antes de mexer nela
        print("Verificando/Criando tabela 'interactions'...")
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS interactions
                    (
                        id               SERIAL PRIMARY KEY,
                        source_id        VARCHAR(255) NOT NULL,
                        target_id        VARCHAR(255) NOT NULL,
                        weight           FLOAT     DEFAULT 1.0,
                        interaction_type VARCHAR(100),
                        created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT unique_interaction UNIQUE (source_id, target_id, interaction_type)
                    );
                    """)
        # IMPORTANTE: Salvar a criação da tabela imediatamente
        conn.commit()

        # --- PASSO 2: LIMPEZA ---
        # Agora o IDE pode reclamar, mas o Python sabe que a tabela existe
        print("Limpando dados antigos...")
        # Adicionei 'CAST' ou '::regclass' se fosse necessário, mas direto funciona
        cur.execute("TRUNCATE TABLE interactions RESTART IDENTITY;")

        # --- PASSO 3: INSERÇÃO ---
        print(f"Inserindo {len(interactions)} registros base...")
        for i in interactions:
            # Ida
            cur.execute("""
                        INSERT INTO interactions (source_id, target_id, weight, interaction_type)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (source_id, target_id, interaction_type) DO NOTHING;
                        """, (i.source_id, i.target_id, i.weight, i.type))

            # Volta
            cur.execute("""
                        INSERT INTO interactions (source_id, target_id, weight, interaction_type)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (source_id, target_id, interaction_type) DO NOTHING;
                        """, (i.target_id, i.source_id, i.weight, i.type + "_reverse"))

        # Salvar os dados
        conn.commit()
        cur.close()
        print("✅ Sucesso! Tabela e dados carregados.")

    except Exception as e:
        print(f"❌ Erro: {e}")
        if conn:
            conn.rollback()  # Desfaz alterações se der erro no meio
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    load_data()


if __name__ == "__main__":
    load_data()