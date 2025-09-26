# tools.py
import os
import re
import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def extract_and_split_file(file_path: str, snomed_terms: list, chunk_size=150, chunk_overlap=30) -> list:
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
    return splitter.split_text(text)

def generate_questions(concepts: list) -> list:
    return [f"O paciente apresenta {c.get('term')}?" for c in concepts if c.get("term")]

def evaluate_results(results: list) -> dict:
    import time
    start = time.time()
    total = sum(len(r.get("qna", [])) for r in results)
    null_count = sum(1 for r in results for q in r.get("qna", []) if "Não mencionado" in q["resposta"])
    return {
        "total": total,
        "nulos": null_count,
        "ratio_nulos": null_count/total if total>0 else 0,
        "tempo_execucao": time.time() - start
    }
