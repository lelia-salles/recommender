from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import requests
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components
import os

# Configuração da Página
st.set_page_config(page_title="Recommender Admin", layout="wide", page_icon="🕸️")
API_URL = "http://127.0.0.1:8000"

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stButton>button {width: 100%;}
    .reportview-container {background: #f0f2f6}
    </style>
    """, unsafe_allow_html=True)


# --- FUNÇÕES AUXILIARES ---
def login(username, password):
    try:
        # A API espera form-data para login (OAuth2 padrão)
        response = requests.post(f"{API_URL}/login", data={"username": username, "password": password})
        if response.status_code == 200:
            return response.json()
        return None
    except:
        st.error("Erro ao conectar com a API. Ela está rodando?")
        return None


def get_recommendations(token, user_id, limit=5):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"{API_URL}/recommendations",
            params={"entity_id": user_id, "limit": limit},
            headers=headers
        )
        if response.status_code == 200:
            return response.json()
        return {"error": response.text}
    except Exception as e:
        return {"error": str(e)}


# --- TELA DE LOGIN (SIDEBAR) ---
st.sidebar.title("🔐 Acesso Seguro")

if 'token' not in st.session_state:
    st.session_state.token = None
    st.session_state.username = None

if not st.session_state.token:
    user_input = st.sidebar.text_input("Usuário", value="usuario_terminal")
    pass_input = st.sidebar.text_input("Senha", type="password", value="senha_do_terminal")

    if st.sidebar.button("Entrar"):
        data = login(user_input, pass_input)
        if data:
            st.session_state.token = data["access_token"]
            st.session_state.username = user_input
            st.sidebar.success(f"Logado como {user_input}")
            st.rerun()
        else:
            st.sidebar.error("Credenciais Inválidas")
else:
    st.sidebar.info(f"👤 Logado: {st.session_state.username}")
    if st.sidebar.button("Sair"):
        st.session_state.token = None
        st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("🕸️ Painel de Controle: Sistema Híbrido")

if not st.session_state.token:
    st.warning("Por favor, faça login na barra lateral para acessar o sistema.")
    st.stop()

# Abas do Dashboard
tab1, tab2, tab3 = st.tabs(["🔍 Simulador de IA", "📊 Visualizar Grafo", "📂 Upload de Dados"])

# --- ABA 1: SIMULADOR ---
with tab1:
    st.header("Testar Motor de Recomendação")

    col1, col2 = st.columns(2)
    with col1:
        target_user = st.text_input("ID do Usuário/Entidade", value="U1")
        limit = st.slider("Quantidade de Recomendações", 1, 20, 5)

    if st.button("🔮 Gerar Recomendações"):
        with st.spinner("Consultando API + Grafo + ML..."):
            data = get_recommendations(st.session_state.token, target_user, limit)

            if "recommendations" in data:
                recs = data["recommendations"]
                if recs:
                    df = pd.DataFrame(recs)
                    st.success(f"Encontramos {len(recs)} sugestões para **{target_user}**")

                    # Exibe bonito com métricas
                    for i, row in df.iterrows():
                        st.metric(label=f"Rank #{i + 1}: {row['item']}", value=f"Score: {row['score']:.4f}")

                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("Nenhuma recomendação encontrada (ou usuário novo sem conexões).")
            else:
                st.error(f"Erro na API: {data}")

# --- ABA 2: VISUALIZADOR DE GRAFO ---
with tab2:
    st.header("Visualização Interativa")
    st.markdown("Isso gera uma visualização baseada nos dados reais do Banco.")

    # Nota: Para visualização, vamos conectar direto no banco ou usar uma rota de exportação.
    # Por simplicidade e performance, vamos simular lendo do serviço (se fosse prod, usaríamos API).
    # Aqui, vamos usar a biblioteca pyvis localmente com os dados que temos no backend.

    if st.button("🔄 Renderizar Grafo Atual"):
        try:
            # Importa aqui para não quebrar se o backend não estiver no path
            from app.services.hybrid_recommender import HybridRecommender

            # Instancia apenas para ler o grafo (ReadOnly)
            rec_viz = HybridRecommender()
            G = rec_viz.graph

            if G.number_of_nodes() == 0:
                st.error("O Grafo está vazio.")
            else:
                st.info(f"Nós: {G.number_of_nodes()} | Arestas: {G.number_of_edges()}")

                # Configura PyVis
                net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white")
                net.from_nx(G)

                # Física para ficar interativo
                net.repulsion(node_distance=100, spring_length=200)

                # Salva e lê o HTML
                net.save_graph("graph_viz.html")
                with open("graph_viz.html", "r", encoding="utf-8") as f:
                    source_code = f.read()

                components.html(source_code, height=610)

        except Exception as e:
            st.error(f"Erro ao gerar visualização: {e}")

# --- ABA 3: UPLOAD ---
with tab3:
    st.header("Ingestão de Arquivos")
    uploaded_file = st.file_uploader("Arraste um CSV, Excel ou PDF aqui", type=['csv', 'xlsx', 'pdf', 'txt'])

    if uploaded_file and st.button("Enviar para Processamento"):
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}

        with st.spinner("Enviando para API..."):
            try:
                res = requests.post(f"{API_URL}/ingest-file", headers=headers, files=files)
                if res.status_code == 200:
                    st.balloons()
                    st.success("Arquivo processado e salvo no Banco!")
                    st.json(res.json())
                else:
                    st.error(f"Erro: {res.text}")
            except Exception as e:
                st.error(f"Falha na conexão: {e}")