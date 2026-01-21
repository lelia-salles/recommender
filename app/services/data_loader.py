import pandas as pd
import json
import io
from pypdf import PdfReader
from docx import Document


class DataLoader:
    """
    Responsável por ler diferentes formatos de arquivo e normalizar
    para o formato que o Grafo entende (Lista de Nós e Arestas).
    Salva na memória RAM para testes ao invés de salvar o BD (data\load_data)
    """

    def process_file(self, filename: str, file_content: bytes):
        ext = filename.split('.')[-1].lower()

        if ext == 'csv':
            return self._process_csv(file_content)
        elif ext in ['xls', 'xlsx']:
            return self._process_excel(file_content)
        elif ext == 'json':
            return self._process_json(file_content)
        elif ext == 'pdf':
            return self._process_pdf(file_content)
        elif ext in ['docx', 'doc']:
            return self._process_docx(file_content)
        elif ext == 'txt':
            return self._process_txt(file_content)
        else:
            raise ValueError(f"Formato '{ext}' não suportado.")

    # --- PROCESSADORES DE DADOS ESTRUTURADOS (Tabelas) ---
    def _process_csv(self, content):
        # Lê o CSV. Assume que tem colunas como 'source', 'target', 'type'
        df = pd.read_csv(io.BytesIO(content))
        return self._dataframe_to_graph_data(df)

    def _process_excel(self, content):
        df = pd.read_excel(io.BytesIO(content))
        return self._dataframe_to_graph_data(df)

    def _process_json(self, content):
        # JSON já deve vir no formato certo, ou adaptamos
        data = json.loads(content)
        # Se vier no formato {nodes: [], edges: []}, retorna direto
        if "nodes" in data and "edges" in data:
            return data
        else:
            raise ValueError("JSON deve conter chaves 'nodes' e 'edges'")

    # --- PROCESSADORES DE DADOS NÃO-ESTRUTURADOS (Texto) ---
    # Nota: Transformar texto livre em grafo é complexo.
    # Aqui vamos assumir que o texto tem um formato "Origem -> Destino" por linha
    # ou simplesmente extrair o texto para análise futura.

    def _process_pdf(self, content):
        reader = PdfReader(io.BytesIO(content))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return self._text_to_graph_data(text)

    def _process_docx(self, content):
        doc = Document(io.BytesIO(content))
        text = "\n".join([para.text for para in doc.paragraphs])
        return self._text_to_graph_data(text)

    def _process_txt(self, content):
        text = content.decode('utf-8')
        return self._text_to_graph_data(text)

    # --- CONVERSORES AUXILIARES ---
    def _dataframe_to_graph_data(self, df):
        """Converte Tabela (Pandas) para JSON de Grafo"""
        # Tenta adivinhar nomes das colunas se não forem padrão
        cols = df.columns.str.lower()
        source_col = next((c for c in cols if 'source' in c or 'origem' in c or 'usuario' in c), df.columns[0])
        target_col = next((c for c in cols if 'target' in c or 'destino' in c or 'produto' in c), df.columns[1])

        nodes = set()
        edges = []

        for _, row in df.iterrows():
            u, v = str(row[source_col]), str(row[target_col])
            nodes.add(u)
            nodes.add(v)
            edges.append({"source": u, "target": v})

        # Formata lista de nós (assumindo tipo genérico por enquanto)
        nodes_list = [{"id": n, "type": "generic"} for n in nodes]
        return {"nodes": nodes_list, "edges": edges}

    def _text_to_graph_data(self, text):
        """
        Tenta extrair relações de texto puro.
        Regra simples: Procura linhas com '->', ' conecta ', ou CSV simples
        """
        nodes = set()
        edges = []

        for line in text.split('\n'):
            if '->' in line:
                parts = line.split('->')
            elif ',' in line:
                parts = line.split(',')
            else:
                continue

            if len(parts) >= 2:
                u = parts[0].strip()
                v = parts[1].strip()
                if u and v:
                    nodes.add(u)
                    nodes.add(v)
                    edges.append({"source": u, "target": v})

        return {"nodes": [{"id": n, "type": "extracted"} for n in nodes], "edges": edges}