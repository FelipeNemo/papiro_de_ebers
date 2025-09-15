"""
MODULO PIPELINE
Consome a base local do SNOMED CT e PDFs de prontuários eletrônicos
para retornar diagnósticos simulados via LLM.

Autor: Felipe Augusto Bastista Mendes dos Santos
Stakeholder: Ebers Saúde
Ebers MVP - Pipeline de Diagnóstico com SNOMED CT
Data: 2024-08-30

Descrição:
Pipeline que processa PDFs de prontuários eletrônicos,
busca conceitos relevantes no SNOMED CT usando embeddings locais
e retorna diagnósticos simulados via LLM.

Componentes:
1. Pré-processamento SNOMED CT
2. Leitura e chunking do PDF
3. Busca no Vector Store (FAISS)
4. Pipeline LangGraph com rastreabilidade LangSmith
"""

# -------------------------------
# 2. Leitura e chunking do PDF
# -------------------------------
import pdfplumber
import re
import faiss
import os
import glob
import json
import pandas as pd
import numpy as np
from langgraph.graph import StateGraph, END
from langsmith import traceable
from typing import TypedDict, List, Dict
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

print("🔹 Inicializando modelo de embeddings...")
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# -------------------------------
# Utilitários
# -------------------------------
def clean_text(text: str) -> str:
    """Remove múltiplos espaços e quebras de linha, retornando texto limpo"""
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_and_chunk_txt(txt_path: str, chunk_size: int = 300) -> list[str]:
    """Lê TXT, normaliza e divide em chunks de tamanho aproximado (tokens/palavras)"""
    text_chunks = []
    with open(txt_path, "r", encoding="utf-8") as f:
        text = clean_text(f.read())
        words = text.split()
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            text_chunks.append(chunk)
    return text_chunks

def extract_and_chunk_pdf(pdf_path: str, chunk_size: int = 300) -> list[str]:
    """Lê PDF, extrai texto por página e divide em chunks de tamanho aproximado (tokens/palavras)"""
    text_chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text = clean_text(text)
                words = text.split()
                for i in range(0, len(words), chunk_size):
                    chunk = " ".join(words[i:i+chunk_size])
                    text_chunks.append(chunk)
    return text_chunks

def extract_and_chunk_file(file_path: str, chunk_size: int = 300) -> list[str]:
    """Decide automaticamente se o arquivo é PDF ou TXT e chama o parser correto"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_and_chunk_pdf(file_path, chunk_size)
    elif ext == ".txt":
        return extract_and_chunk_txt(file_path, chunk_size)
    else:
        raise ValueError(f"Formato de arquivo não suportado: {ext}")

# -------------------------------
# 3. Busca no Vector Store
# -------------------------------
# Reabrir índice e conceitos salvos
from typing import TypedDict, List, Dict

index = faiss.read_index("data/vector/snomed_ivf.index", faiss.IO_FLAG_MMAP)
concept_groups = pd.read_csv("data/vector/snomed_concepts.csv")

# Ajuste do nprobe (quantos clusters buscar por query)
index.nprobe = 16  # tradeoff entre velocidade x precisão

# Define estado compartilhado da pipeline (vem antes de search_snomed)
class PipelineState(TypedDict):
    pdf_path: str
    chunks: List[str]
    results: List[Dict]
    model: object  # modelo no estado da pipeline


def search_snomed(query: str, state: PipelineState, k: int = 5) -> list[dict]:
    """Busca os k conceitos mais próximos no SNOMED CT usando IVF on-disk"""
    query_emb = state["model"].encode([query])
    query_emb = np.array(query_emb).astype("float32")
    D, I = index.search(query_emb, k)
    return [concept_groups.iloc[idx].to_dict() for idx in I[0]]

# -------------------------------
# 4. Fluxo no LangGraph com LangSmith
# -------------------------------
load_dotenv()  # Carrega variáveis do .env

# Teste
print(os.getenv("LANGCHAIN_API_KEY"))

# --- NODES ---
@traceable(name="Input Node")
def input_node(state: PipelineState):
    """Recebe caminho do PDF"""
    return {"pdf_path": state["pdf_path"]}

@traceable(name="Process Node")
def process_node(state: PipelineState):
    """Extrai texto do PDF/TXT e realiza chunking"""
    chunks = extract_and_chunk_file(state["pdf_path"])  # <-- aqui
    return {"chunks": chunks}

@traceable(name="Retriever Node")
def retriever_node(state: PipelineState):
    """Busca os top-k conceitos SNOMED para cada chunk"""
    results = []
    for chunk in state["chunks"]:
        res = search_snomed(chunk, state, k=5)
        results.append({"chunk": chunk, "matches": res})
    return {"results": results}

@traceable(name="LLM Node")
def llm_node(state: PipelineState):
    """
    Você é um assistente médico especializado em mapeamento de prontuários eletrônicos
    para conceitos SNOMED CT. 
    """
    analyzed = []
    for r in state["results"]:
        analyzed.append({
            "chunk": r["chunk"],
            "concepts": r["matches"],
            "diagnostic": f"LLM avaliou e escolheu conceito mais próximo"
        })
    return {"results": analyzed}

# --- GRAPH ---
graph = StateGraph(PipelineState)
graph.add_node("input", input_node)
graph.add_node("process", process_node)
graph.add_node("retriever", retriever_node)
graph.add_node("llm", llm_node)
graph.set_entry_point("input")
graph.add_edge("input", "process")
graph.add_edge("process", "retriever")
graph.add_edge("retriever", "llm")
graph.add_edge("llm", END)

# Compilar pipeline
app = graph.compile()

# -------------------------------
# Execução com rastreabilidade no LangSmith
# -------------------------------
@traceable(name="SNOMED Pipeline")
def run_pipeline(pdf_path: str):
    """Executa a pipeline completa e envia logs para LangSmith"""
    return app.invoke({"pdf_path": pdf_path, "model": model})

# -------------------------------
# Execução universal para PDFs e TXT
# -------------------------------
input_folder = "data/test"
res_folder = os.path.join(input_folder, "res")
os.makedirs(res_folder, exist_ok=True)

# Pega todos os arquivos PDF e TXT
files = glob.glob(os.path.join(input_folder, "*.txt")) + glob.glob(os.path.join(input_folder, "*.pdf"))

for file_path in files:
    print(f"Processando {file_path}...")
    final_state = run_pipeline(file_path)
    base_name = os.path.basename(file_path)
    json_name = os.path.splitext(base_name)[0] + ".json"
    output_path = os.path.join(res_folder, json_name)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_state["results"], f, ensure_ascii=False, indent=2)
    print(f"Resultado salvo em {output_path}\n")






