"""
MODULO PIPELINE
Processa PDFs/TXT de prontuários eletrônicos, busca conceitos SNOMED CT
usando embeddings locais e retorna diagnósticos simulados via LLM.

Autor: Felipe Augusto Bastista Mendes dos Santos
Stakeholder: Ebers Saúde
Data: 2024-08-30
"""

import os
import re
import glob
import json
import time
import pdfplumber
import pandas as pd
import numpy as np
from typing import TypedDict, List, Dict
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langsmith import traceable
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from langsmith.wrappers import wrap_openai  # traces openai calls
import webbrowser


import os



load_dotenv(dotenv_path=".env")
print(os.getenv("OPENAI_API_KEY"))  # deve imprimir a chave
client = wrap_openai(OpenAI()) 

print("TRACING:", os.getenv("LANGCHAIN_TRACING_V2"))
print("ENDPOINT:", os.getenv("LANGCHAIN_ENDPOINT"))
print("API_KEY:", os.getenv("LANGCHAIN_API_KEY"))
print("PROJECT:", os.getenv("LANGSMITH_PROJECT"))

# -------------------------------
# Inicialização de modelos
# -------------------------------
print("🔹 Inicializando modelo de embeddings...")
embedding_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# -------------------------------
# Utilitários
# -------------------------------
def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def extract_and_split_file(file_path: str, snomed_terms: List[str], chunk_size: int = 150, chunk_overlap: int = 30) -> List[str]:
    """Lê PDF ou TXT, gera chunks e filtra por termos SNOMED, mas retorna todos se nenhum match."""
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    if ext == ".pdf":
        with pdfplumber.open(file_path) as pdf:
            text = " ".join(page.extract_text() or "" for page in pdf.pages)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        raise ValueError(f"Formato de arquivo não suportado: {ext}")

    text = clean_text(text)
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_text(text)

    # Filtra chunks que contêm termos SNOMED
    term_chunks = [chunk for chunk in chunks if any(term.lower() in chunk.lower() for term in snomed_terms)]
    # TODO: Evitar chunks irrelevantes
    # Se não houver matches, não retornar todos, mas apenas os primeiros 1-2 chunks para debug
    return chunks
    # Se não houver matches, retorna todos os chunks (para debug ou fallback)
    #return term_chunks or chunks

def generate_questions(concepts: List[Dict]) -> List[str]:
    return [f"O paciente apresenta {c.get('term')}?" for c in concepts if c.get("term")]

def build_prompt(concepts: List[Dict], chunk: str) -> str:
    context = (
        "Você é um assistente clínico especializado em terminologias médicas (SNOMED CT). "
        "Sua tarefa é analisar trechos de prontuários médicos e sugerir diagnósticos potenciais."
    )
    instructions = (
        "Siga estas etapas:\n"
        "1. Leia o trecho do prontuário.\n"
        "2. Analise os conceitos SNOMED CT recuperados.\n"
        "3. Escolha o conceito mais relevante.\n"
        "4. Justifique brevemente sua escolha.\n"
        "5. Retorne no formato estruturado JSON."
    )
    input_section = f"Trecho: {chunk}\nConceitos candidatos: {concepts}"
    output_section = "Formato esperado:\n{ 'diagnostico': 'nome do conceito SNOMED CT', 'justificativa': 'texto curto' }"
    return f"{context}\n\n{instructions}\n\n{input_section}\n\n{output_section}"

def build_qna(chunk: str, questions: List[str]) -> List[Dict]:
    qna_results = []
    for q in questions:
        prompt = f"""
Você é um assistente clínico. Leia atentamente o trecho do prontuário abaixo.
Responda apenas com 'Sim', 'Não' ou 'Não mencionado'.

Trecho: {chunk}

Pergunta: {q}

Instruções:
- Responda 'Sim' somente se houver **evidência textual clara** no trecho que confirma o conceito.
- Responda 'Não' se houver evidência textual que negue o conceito.
- Responda 'Não mencionado' se não houver informações suficientes no trecho.

Responda **apenas com uma destas três opções**, sem explicações adicionais.
"""
        response = llm.invoke(prompt).content.strip()
        qna_results.append({"pergunta": q, "resposta": response})
    return qna_results

def evaluate_results(results: List[Dict]) -> Dict:
    start = time.time()
    total = sum(len(r.get("qna", [])) for r in results)
    null_count = sum(1 for r in results for q in r.get("qna", []) if "Não mencionado" in q["resposta"])
    return {"total": total, "nulos": null_count, "ratio_nulos": null_count/total if total>0 else 0, "tempo_execucao": time.time() - start}

# -------------------------------
# Setup Vector Store FAISS
# -------------------------------
import faiss

index = faiss.read_index("data/vector/snomed_ivf.index", faiss.IO_FLAG_MMAP)
index.nprobe = 16
concept_groups = pd.read_csv("data/vector/snomed_concepts.csv")

# TODO: 
# Sem filtro por categoria
snomed_terms = concept_groups["term"].dropna().tolist()


class PipelineState(TypedDict):
    pdf_path: str
    chunks: List[str]
    results: List[Dict]
    questions_map: List[Dict]
    qna_results: List[Dict]
    metrics: Dict

 # ajustar distance_threshold conforme os resultados (0.5–0.7 costuma funcionar bem).
# ajustar distance_threshold conforme os resultados (0.5–0.7 costuma funcionar bem).
def search_snomed(query: str, k: int = 5, distance_threshold: float = 0.6) -> List[Dict]: 
    emb = np.array(embedding_model.encode([query])).astype("float32")
    D, I = index.search(emb, k)

    results = []  # inicializa a lista de resultados

    # Filtra conceitos apenas pelo threshold de distância
    for idx, dist in zip(I[0], D[0]):
        # FAISS retorna similaridade invertida dependendo do índice: use <= para IVF ou 1/dist
        if dist <= distance_threshold:
            results.append(concept_groups.iloc[idx].to_dict())

    # Se quiser sempre pelo menos 1 resultado, mesmo que distante:
    if not results and len(I[0]) > 0:
        results.append(concept_groups.iloc[I[0][0]].to_dict())

    return results



# -------------------------------
# LangGraph Nodes
# -------------------------------
@traceable(name="Input Node")
def input_node(state: PipelineState):
    return {"pdf_path": state["pdf_path"]}

@traceable(name="Process Node")
def process_node(state: PipelineState):
    return {"chunks": extract_and_split_file(state["pdf_path"], snomed_terms, 100, 20)}


def retriever_node(state: PipelineState):
    return {"results": [{"chunk": chunk, "matches": search_snomed(chunk, k=5, distance_threshold=0.8)} for chunk in state["chunks"]]}

@traceable(name="LLM Node")
def llm_node(state: PipelineState):
    analyzed = []
    for r in state["results"]:
        prompt = build_prompt(r["matches"], r["chunk"])
        analyzed.append({"chunk": r["chunk"], "concepts": r["matches"], "diagnostic": llm.invoke(prompt).content})
    return {"results": analyzed}

@traceable(name="Question Node")
def question_node(state: PipelineState):
    return {"results": state["results"], "questions_map": [{"chunk": r["chunk"], "questions": generate_questions(r["concepts"])} for r in state["results"]]}

@traceable(name="QnA Node")
def qna_node(state: PipelineState):
    return {"qna_results": [{"chunk": qm["chunk"], "qna": build_qna(qm["chunk"], qm["questions"])} for qm in state["questions_map"]]}

@traceable(name="Evaluation Node")
def evaluation_node(state: PipelineState):
    metrics = evaluate_results(state["qna_results"])
    return {"qna_results": state["qna_results"], "metrics": metrics}

# -------------------------------
# Grafo LangGraph
# -------------------------------
graph = StateGraph(PipelineState)
nodes = [("input", input_node), ("process", process_node), ("retriever", retriever_node), 
         ("llm", llm_node), ("questions", question_node), ("qna", qna_node), ("evaluation", evaluation_node)]

for name, node in nodes:
    graph.add_node(name, node)

graph.set_entry_point("input")
edges = [("input","process"),("process","retriever"),("retriever","llm"),("llm","questions"),
         ("questions","qna"),("qna","evaluation"),("evaluation",END)]

for src, dst in edges:
    graph.add_edge(src,dst)

app = graph.compile()

# -------------------------------
# Execução da Pipeline
# -------------------------------

@traceable(name="SNOMED Pipeline")
def run_pipeline(pdf_path: str):
    return app.invoke({"pdf_path": pdf_path})    
# -------------------------------
# Batch Execution
# -------------------------------
input_folder = "data/test"
res_folder = os.path.join(input_folder, "res")
os.makedirs(res_folder, exist_ok=True)

files = glob.glob(os.path.join(input_folder, "*.txt")) + glob.glob(os.path.join(input_folder, "*.pdf"))

for file_path in files:
    print(f"Processando {file_path}...")
    final_state = run_pipeline(file_path)
    # -------------------------------
    # Abrir painel do LangSmith no navegador
    # -------------------------------
    ORG_ID = "coloque_aqui_o_id_da_sua_org"  # pegue no site smith.langchain.com (URL da sua org)
    project = os.getenv("LANGSMITH_PROJECT")
    url = f"https://smith.langchain.com/o/{ORG_ID}/projects/{project}"
    print(f"\n🔗 Abra o painel aqui: {url}")
    webbrowser.open(url)

    # Exemplo de debug: imprimir todos os nodes e resultados
    for node_name, node_data in final_state.items():
        print(f"Node: {node_name}")
        print(json.dumps(node_data, ensure_ascii=False, indent=2))
        print("-"*50)
    
    output_path = os.path.join(res_folder, os.path.splitext(os.path.basename(file_path))[0] + ".json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_state, f, ensure_ascii=False, indent=2)
    print(f"Resultado salvo em {output_path}\n")
