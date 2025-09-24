"""
Script para construir índice PubMedBERT com 50.000 conceitos
Fase 2: Expansão incremental do sistema
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.gpu_pubmedbert_search import GPUPubMedBERTSearch
from src.core.config import SNOMED_DATA_PATH
import time

def build_large_index():
    """Constrói índice com 50.000 conceitos"""
    print("🚀 Fase 2: Construindo Índice PubMedBERT com 50.000 Conceitos")
    print("=" * 70)
    
    # Inicializa sistema
    gpu_search = GPUPubMedBERTSearch()
    
    # Mostra informações da GPU
    gpu_info = gpu_search.get_gpu_info()
    print(f"🎯 GPU: {gpu_info['gpu_name']}")
    print(f"💾 Memória total: {gpu_info['memory_total']:.1f} GB")
    
    # Carrega modelo
    print("\n🔬 Carregando modelo PubMedBERT...")
    start_time = time.time()
    gpu_search.load_model()
    load_time = time.time() - start_time
    print(f"✅ Modelo carregado em {load_time:.2f}s")
    
    # Constrói índice com 50.000 conceitos
    print("\n🔨 Construindo índice com 50.000 conceitos...")
    print("📊 Isso pode levar alguns minutos...")
    
    start_time = time.time()
    gpu_search.build_gpu_index(
        snomed_data_path=SNOMED_DATA_PATH,
        output_path="data/snomed_pubmedbert_large_index",
        sample_size=50000,  # 50.000 conceitos
        batch_size=128      # Lote maior para eficiência
    )
    build_time = time.time() - start_time
    
    print(f"\n✅ Índice construído em {build_time:.2f}s")
    print(f"📊 Conceitos processados: 50.000")
    print(f"🎯 Dispositivo: {gpu_search.device}")
    print(f"⚡ Velocidade: {50000/build_time:.1f} conceitos/segundo")
    
    return True

def test_large_index():
    """Testa o índice expandido"""
    print("\n🧪 Testando Índice Expandido...")
    
    try:
        gpu_search = GPUPubMedBERTSearch()
        gpu_search.load_model()
        
        # Carrega índice expandido
        if gpu_search.load_index("data/snomed_pubmedbert_large_index"):
            print("✅ Índice expandido carregado!")
            
            # Teste com queries mais complexas
            test_queries = [
                "infarto agudo do miocárdio",
                "diabetes mellitus tipo 2 descompensado",
                "pneumonia adquirida na comunidade",
                "hipertensão arterial sistêmica",
                "insuficiência cardíaca congestiva"
            ]
            
            total_time = 0
            for i, query in enumerate(test_queries, 1):
                print(f"\n{i}. Testando: '{query}'")
                start_time = time.time()
                results = gpu_search.search_with_translation(query, top_k=5)
                search_time = time.time() - start_time
                total_time += search_time
                
                print(f"   ⏱️ Tempo: {search_time:.3f}s")
                print(f"   📊 Resultados: {len(results)}")
                for j, result in enumerate(results[:2]):
                    score = result['similarity_score']
                    term = result['term']
                    print(f"   {j+1}. {term} (score: {score:.3f})")
            
            avg_time = total_time / len(test_queries)
            print(f"\n📈 Performance do Índice Expandido:")
            print(f"   ⏱️ Tempo médio: {avg_time:.3f}s")
            print(f"   🚀 Velocidade: {1/avg_time:.1f} buscas/segundo")
            print(f"   📊 Conceitos: 50.000")
            
            return True
        else:
            print("❌ Falha ao carregar índice expandido")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    print("🏥 Fase 2: Expansão do Sistema PubMedBERT")
    print("=" * 70)
    
    # Constrói índice expandido
    success = build_large_index()
    
    if success:
        # Testa o índice
        test_success = test_large_index()
        
        if test_success:
            print("\n" + "=" * 70)
            print("🎉 FASE 2 CONCLUÍDA!")
            print("✅ Índice expandido para 50.000 conceitos")
            print("🚀 Performance mantida com GPU")
            print("🔬 Pronto para Fase 3: Cache Inteligente")
        else:
            print("\n❌ Falha no teste do índice expandido")
    else:
        print("\n❌ Falha na construção do índice expandido")
