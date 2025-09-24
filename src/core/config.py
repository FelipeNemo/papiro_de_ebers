"""
Configurações centralizadas do sistema
"""

import os

# -------------------------------
# Configurações de Diretórios
# -------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
VECTOR_DIR = os.path.join(DATA_DIR, "vector")
TEST_INPUT_FOLDER = os.path.join(DATA_DIR, "test")
TEST_OUTPUT_FOLDER = os.path.join(TEST_INPUT_FOLDER, "res")
SNOMED_RELEASES_DIR = os.path.join(BASE_DIR, "SnomedCT_InternationalRF2_PRODUCTION_20250801T120000Z")
SNOMED_DATA_PATH = SNOMED_RELEASES_DIR

# -------------------------------
# Configurações do SNOMED CT
# -------------------------------
SNOMED_DESCRIPTION_PATH = os.path.join(
    SNOMED_RELEASES_DIR,
    "Snapshot",
    "Terminology",
    "sct2_Description_Snapshot-en_INT_20250801.txt"
)

# Caminhos para índices FAISS
VECTOR_INDEX_PATH = os.path.join(VECTOR_DIR, "snomed_ivf.index")
CONCEPTS_CSV_PATH = os.path.join(VECTOR_DIR, "snomed_concepts.csv")
VECTOR_INDEX_REAL_PATH = os.path.join(VECTOR_DIR, "snomed_ivf_real.index")
CONCEPTS_CSV_REAL_PATH = os.path.join(VECTOR_DIR, "snomed_concepts_real.csv")
VECTOR_INDEX_ENHANCED_PATH = os.path.join(VECTOR_DIR, "snomed_ivf_enhanced.index")
CONCEPTS_CSV_ENHANCED_PATH = os.path.join(VECTOR_DIR, "snomed_concepts_enhanced.csv")

# -------------------------------
# Configurações do Modelo de Embeddings
# -------------------------------
EMBEDDING_MODEL = "NeuML/pubmedbert-base-embeddings"

# -------------------------------
# Configurações do FAISS
# -------------------------------
FAISS_NPROBE = 16
SEARCH_K = 5

# -------------------------------
# Configurações de Qualidade
# -------------------------------
QUALITY_THRESHOLD = 6.0  # Threshold mínimo para considerar resultado de qualidade
CONFIDENCE_THRESHOLD = 5.0  # Threshold mínimo para confiança

# -------------------------------
# Funções Utilitárias
# -------------------------------
def create_directories():
    """Cria diretórios necessários"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(VECTOR_DIR, exist_ok=True)
    os.makedirs(TEST_INPUT_FOLDER, exist_ok=True)
    os.makedirs(TEST_OUTPUT_FOLDER, exist_ok=True)
    print("✅ Diretórios criados/verificados")

print("🔧 Configurações carregadas com sucesso!")
