import pandas as pd
import json
import io
# Bibliotecas para formatos específicos (certifique-se de instalá-las)
from pypdf import PdfReader
from docx import Document


class FileParser:
    """
    Serviço especializado em transformar bytes de arquivos (Uploads)
    em um dicionário estruturado de Grafo: {"nodes": [], "edges": []}
    """

    def parse(self, filename: str, file_content: bytes) -> dict:
        ext = filename.split('.')[-1].lower()

        try:
            if ext == 'csv':
                return self._parse_csv(file_content)
            elif ext in ['xls', 'xlsx']:
                return self._parse_excel(file_content)
            elif ext == 'json':
                return json.loads(file_content)
            elif ext == 'pdf':
                return self._parse_pdf(file_content)
            elif ext in ['docx', 'doc']:
                return self._parse_docx(file_content)
            elif ext == 'txt':
                return self._parse_txt(file_content)
            else:
                raise ValueError(f"Extensão '{ext}' não suportada.")
        except Exception as e:
            raise ValueError(f"Erro ao processar arquivo: {str(e)}")

    # --- MÉTODOS INTERNOS DE PARSING ---

    def _dataframe_to_graph(self, df):
        """Converte Pandas DataFrame para formato de Grafo"""
        # Tenta identificar colunas automaticamente
        cols = [c.lower() for c in df.columns]

        # Lógica flexível para achar origem/destino
        source_col = next(
            (c for c in df.columns if 'source' in c.lower() or 'origem' in c.lower() or 'de' in c.lower()),
            df.columns[0])
        target_col = next(
            (c for c in df.columns if 'target' in c.lower() or 'destino' in c.lower() or 'para' in c.lower()),
            df.columns[1])

        nodes = set()
        edges = []

        for _, row in df.iterrows():
            u, v = str(row[source_col]), str(row[target_col])
            if u != 'nan' and v != 'nan':
                nodes.add(u)
                nodes.add(v)
                edges.append({"source": u, "target": v})

        return {
            "nodes": [{"id": n, "type": "generic"} for n in nodes],
            "edges": edges
        }

    def _parse_csv(self, content):
        df = pd.read_csv(io.BytesIO(content))
        return self._dataframe_to_graph(df)

    def _parse_excel(self, content):
        df = pd.read_excel(io.BytesIO(content))
        return self._dataframe_to_graph(df)

    def _parse_pdf(self, content):
        reader = PdfReader(io.BytesIO(content))
        text = "\n".join([page.extract_text() for page in reader.pages])
        return self._text_to_graph(text)

    def _parse_docx(self, content):
        doc = Document(io.BytesIO(content))
        text = "\n".join([para.text for para in doc.paragraphs])
        return self._text_to_graph(text)

    def _parse_txt(self, content):
        return self._text_to_graph(content.decode('utf-8'))

    def _text_to_graph(self, text):
        """
        Extração simples baseada em texto.
        Procura padrões como "A -> B" ou "A, B" por linha.
        """
        nodes = set()
        edges = []

        for line in text.split('\n'):
            line = line.strip()
            if not line: continue

            parts = []
            if '->' in line:
                parts = line.split('->')
            elif ',' in line:
                parts = line.split(',')

            if len(parts) >= 2:
                u, v = parts[0].strip(), parts[1].strip()
                nodes.add(u)
                nodes.add(v)
                edges.append({"source": u, "target": v})

        return {
            "nodes": [{"id": n, "type": "extracted_text"} for n in nodes],
            "edges": edges
        }