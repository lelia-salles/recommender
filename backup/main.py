import os
from app.services.recommender import recommend
from app.core.security import verify_password, create_access_token, decode_access_token
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def login_flow(username, password):
    """
    Simula o processo de login de uma API.
    Retorna o Token JWT se der certo, ou None se der errado.
    """
    try:
        # 1. Conectar ao banco para buscar a senha do usuário
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"), database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"), password=os.getenv("DB_PASS")
        )
        with conn.cursor() as cur:
            cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
            result = cur.fetchone()
        conn.close()

        if not result:
            print("❌ Usuário não encontrado.")
            return None

        stored_hash = result[0]

        # 2. Verificar senha e Gerar Token
        if verify_password(password, stored_hash):
            print(f"✅ Login bem-sucedido para {username}!")
            # O 'sub' (subject) do token será o username (ex: "U1")
            # Isso é importante porque é esse ID que usaremos para buscar recomendações
            token = create_access_token({"sub": username})
            return token
        else:
            print("❌ Senha incorreta.")
            return None

    except Exception as e:
        print(f"Erro no sistema de login: {e}")
        return None


def protected_view_recommendations(token):
    """
    Simula uma rota protegida. Só funciona se o token for válido.
    """
    print("\n--- Acessando Área Protegida de Recomendações ---")

    # 1. Validar o Token
    payload = decode_access_token(token)

    if not payload:
        print("⛔ ACESSO NEGADO: Token inválido ou expirado.")
        return

    # 2. Extrair quem é o usuário do token
    current_user = payload.get("sub")  # Vai retornar "U1"
    print(f"🔓 Acesso autorizado. Bem-vindo, {current_user}.")

    # 3. Chamar o sistema de recomendação (Postgres)
    # Note que agora pegamos o ID direto do token, não pedimos pro usuário digitar
    recs = recommend(current_user, limit=5, depth=3)

    if recs:
        print(f"\nRecomendações para você baseadas no seu histórico:")
        for i, (item, score) in enumerate(recs, 1):
            print(f"{i}. {item} (Score: {score:.2f})")
    else:
        print("\nNenhuma recomendação encontrada (Tente interagir com mais itens!)")


def main():
    # Cenário: Usuário U1 tentando entrar
    print("--- Simulação de Sistema ---")
    user = input("Usuário (tente U1): ") or "U1"
    pwd = input("Senha (tente senha123): ") or "senha123"

    # Tentativa de Login
    token = login_flow(user, pwd)

    if token:
        # Se login funcionou, tenta acessar as recomendações
        protected_view_recommendations(token)
    else:
        print("Encerrando sistema sem acesso.")


if __name__ == "__main__":
    main()
