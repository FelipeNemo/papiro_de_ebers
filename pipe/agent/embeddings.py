# embeddings.py
import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

index = faiss.read_index("data/vector/snomed_ivf.index", faiss.IO_FLAG_MMAP)
index.nprobe = 16
concept_groups = pd.read_csv("data/vector/snomed_concepts.csv")
snomed_terms = concept_groups["term"].dropna().tolist()

def search_snomed(query: str, k: int = 5, distance_threshold: float = 0.6) -> list:
    emb = np.array(embedding_model.encode([query])).astype("float32")
    D, I = index.search(emb, k)
    results = []

    for idx, dist in zip(I[0], D[0]):
        if dist <= distance_threshold:
            results.append(concept_groups.iloc[idx].to_dict())

    if not results and len(I[0]) > 0:
        results.append(concept_groups.iloc[I[0][0]].to_dict())
    return results
