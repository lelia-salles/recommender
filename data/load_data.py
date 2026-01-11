from data.sample_data import interactions  # Seus dados antigos
import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "database": "recommender_db",
    "user": "postgres",
    "password": "sua_senha_aqui"
}


def load_data():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print("Limpando tabela antiga...")
    cur.execute("DELETE FROM interactions;")

    print("Inserindo dados...")
    for i in interactions:
        # Inserção IDA (A -> B)
        cur.execute("""
        
        []
        
                    INSERT INTO interactions (source_id, target_id, weight, interaction_type)
                    VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;
                    """, (i.source_id, i.target_id, i.weight, i.type))

        # Inserção VOLTA (B -> A) - Para simular grafo não direcionado
        cur.execute("""
                    INSERT INTO interactions (source_id, target_id, weight, interaction_type)
                    VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;
                    """, (i.target_id, i.source_id, i.weight, i.type + "_reverse"))

    conn.commit()
    cur.close()
    conn.close()
    print("Dados carregados com sucesso!")


if __name__ == "__main__":
    load_data()