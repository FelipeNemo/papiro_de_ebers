# -------------------------------
# 1. Pré-processamento do SNOMED CT (com streaming de embeddings)
# -------------------------------
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

print("🔹 Inicializando modelo de embeddings...")
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

print("🔹 Carregando descrições ativas do SNOMED...")
desc = pd.read_csv("realeases/SnomedCT_InternationalRF2_PRODUCTION_20250801T120000Z/Snapshot/Terminology/sct2_Description_Snapshot-en_INT_20250801.txt", sep="\t", dtype=str)
desc["active"] = desc["active"].astype(int)
desc = desc[desc["active"] == 1]
print(f"✅ Descrições ativas carregadas: {len(desc)} linhas")

print("🔹 Agrupando termos por conceito...")
concept_groups = (
    desc.groupby("conceptId")["term"]
    .apply(lambda x: ". ".join(str(t) for t in x if pd.notna(t)))
    .reset_index()
)
print(f"✅ Total de conceitos únicos: {len(concept_groups)}")

print("🔹 Criando índice IVF do FAISS...")
dimension = model.get_sentence_embedding_dimension()
nlist = 100
quantizer = faiss.IndexFlatL2(dimension)
index_ivf = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_L2)

print("🔹 Treinando índice com amostra de termos...")
sample_terms = concept_groups["term"].sample(n=min(5000, len(concept_groups)), random_state=42).tolist()
sample_emb = model.encode(sample_terms, show_progress_bar=True)
sample_emb = np.array(sample_emb).astype("float32")
index_ivf.train(sample_emb)
print("✅ Índice treinado com sucesso")

print("🔹 Adicionando vetores ao índice em batches...")
batch_size = 128
total_batches = (len(concept_groups) + batch_size - 1) // batch_size
for i in range(0, len(concept_groups), batch_size):
    batch_terms = concept_groups["term"].iloc[i:i+batch_size].tolist()
    batch_emb = model.encode(batch_terms, show_progress_bar=True)
    batch_emb = np.array(batch_emb).astype("float32")
    index_ivf.add(batch_emb)
    print(f"📌 Processado batch {i//batch_size + 1} / {total_batches}")

print("🔹 Salvando índice e conceitos...")
faiss.write_index(index_ivf, "data/vector/snomed_ivf.index")
concept_groups.to_csv("data/vector/snomed_concepts.csv", index=False)
print("✅ Índice e conceitos salvos com sucesso!")
