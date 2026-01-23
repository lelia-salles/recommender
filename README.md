# Hybrid Recommender System & Secure API 🧠🔒

[🇺🇸 English](#english) | [🇧🇷 Português](#portuguese)

---

<a name="english"></a>
## 🇺🇸 English

### 📖 About the Project
This is a **Hybrid Recommendation System** built with Python, designed to be robust, secure, and scalable. It combines **Graph Theory** (NetworkX) with **Machine Learning** (Random Forest/LSH) to suggest items and find hidden connections.

**Key Differentiator: Enterprise-Grade Security**
The system implements **Blind Indexing** using **Blake2b** hashing for sensitive data (PII), ensuring full compliance with privacy laws (GDPR/LGPD). It allows searching for users by email or Government ID (CPF) without ever storing the real data in plain text in the database.

### 🚀 Key Features
* **Hybrid Engine:** Combines Collaborative Filtering (Graph) + Content-based Filtering (ML).
* **Secure Authentication:** JWT Tokens + Bcrypt for password hashing.
* **Privacy First:** **Blind Indexing** (Blake2b + Pepper) for Emails and IDs. Real data is never exposed to the DB.
* **Interactive Dashboard:** A **Streamlit** admin panel to visualize the Graph interactively and test recommendations.
* **Persistence:** All data and relationships are stored in **PostgreSQL**.

### 🛠 Tech Stack
* **Language:** Python 3.10+
* **API Framework:** FastAPI
* **Database:** PostgreSQL (Psycopg2)
* **Data Science:** NetworkX, Scikit-learn, Pandas
* **Security:** Passlib (Bcrypt), Hashlib (Blake2b), Python-Jose (JWT)
* **Frontend:** Streamlit, PyVis

### ⚙️ Installation & Setup

**1. Clone the repository**
```bash
git clone [https://github.com/your-username/recommender.git](https://github.com/your-username/recommender.git)
cd recommender

python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

**2. Create a virtual environment
```
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```
**4. Environment Configuration (.env) Create a .env file in the root directory with the following variables:**
```bash
DB_HOST=localhost
DB_NAME=recommender
DB_USER=postgres
DB_PASS=your_password
SECRET_KEY=your_jwt_secret_key
SECURITY_PEPPER=super_secret_pepper_key_never_change_this
```
## Database Setup Run the utility scripts to create secure columns and populate the database**
### 1. Create secure columns (hashing) and indexes
python update_db_users.py

### 2. Populate DB with mock encrypted data
python seed_db.py

## ▶️ Usage
### 1. Start the API Server The backend handles the logic, graph processing, and database connections.

´´´bash
uvicorn app.api.api_main:app --reload
´´´
Access Swagger Documentation: https://www.google.com/search?q=http://127.0.0.1:8000/docs

### 2. Start the Admin Dashboard Open a new terminal to run the visual interface.

´´´bash
streamlit run dashboard.py
´´´
Access Dashboard: http://localhost:8501

*Default Test Credentials:*

User: U1

Password: senha123

<a name="portuguese"></a>

## 🇧🇷 Português
### 📖 Sobre o Projeto
Este é um Sistema de **Recomendação Híbrido** desenvolvido em Python, projetado para ser robusto, seguro e escalável. Ele combina **Teoria dos Grafos (NetworkX) com Machine Learning (Random Forest/LSH)** para sugerir itens e encontrar conexões ocultas.

**Diferencial Chave: **Segurança Nível Enterprise** O sistema implementa **Blind Indexing** usando hash **Blake2b** para dados sensíveis (PII), garantindo conformidade total com a **LGPD**. Isso permite buscar usuários por e-mail ou CPF sem nunca salvar o dado real em texto plano no banco de dados.**

### 🚀 Funcionalidades Principais
* **Motor Híbrido: Combina Filtragem Colaborativa (Grafo) + Baseada em Conteúdo (ML).**

* **Autenticação Segura: Tokens JWT + Bcrypt para senhas.**

* **Privacidade (LGPD): Blind Indexing (Blake2b + Pepper) para E-mails e CPFs. O dado real nunca é exposto ao Banco.**

* **Dashboard Interativo: Painel administrativo em Streamlit para visualizar o Grafo interativamente e testar recomendações.**

* **Persistência: Todos os dados e relacionamentos são salvos no PostgreSQL.**

### 🛠 Tecnologias
* **Linguagem: Python 3.10+**

* **API Framework: FastAPI**

* **Banco de Dados: PostgreSQL (Psycopg2)**

* **Data Science: NetworkX, Scikit-learn, Pandas**

* **Segurança: Passlib (Bcrypt), Hashlib (Blake2b), Python-Jose (JWT)**

* **Frontend: Streamlit, PyVis**

### ⚙️ Instalação e Configuração
**1. Clone o repositório**

```bash
git clone [https://github.com/seu-usuario/recommender.git](https://github.com/seu-usuario/recommender.git)
cd recommender
```
**2. Crie o Ambiente Virtual**

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

**3. Instale as Dependências**

```bash
pip install -r requirements.txt
```

**4. Configuração de Ambiente (.env) Crie um arquivo .env na raiz do projeto com as seguintes variáveis:**

```bash
DB_HOST=localhost
DB_NAME=recommender
DB_USER=postgres
DB_PASS=sua_senha
SECRET_KEY=sua_chave_secreta_jwt
SECURITY_PEPPER=sua_pimenta_secreta_nunca_mude_isso
```

**5. Configuração do Banco de Dados Execute os scripts utilitários para criar as colunas de segurança e popular o banco:**


# 1. Criar colunas de hash e índices de performance

```bash
python update_db_users.py
```
# 2. Popular o banco com dados de teste criptografados


```bash
python seed_db.py
```

## ▶️ Como Usar
### 1. Iniciar o Servidor API O backend gerencia a lógica, o processamento do grafo e as conexões com o banco.

```bash
uvicorn app.api.api_main:app --reload
```
Acesse a Documentação (Swagger): https://www.google.com/search?q=http://127.0.0.1:8000/docs

### 2. Iniciar o Dashboard Abra um novo terminal para rodar a interface visual.

```bash
streamlit run dashboard.py
```
Acesse o Painel: http://localhost:8501

*Credenciais de Teste Padrão:*

**Usuário: U1**

**Senha: senha123**
