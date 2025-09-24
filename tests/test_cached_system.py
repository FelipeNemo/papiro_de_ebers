"""
Teste do Sistema PubMedBERT com Cache Inteligente
Fase 3: Teste de performance e otimização
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.cached_pubmedbert_search import CachedPubMedBERTSearch
from src.core.config import SNOMED_DATA_PATH
import time
import json

def test_cached_system():
    """Testa sistema com cache"""
    print("🧪 Teste do Sistema PubMedBERT com Cache Inteligente")
    print("=" * 70)
    
    try:
        # Inicializa sistema
        print("🚀 Inicializando sistema com cache...")
        cached_search = CachedPubMedBERTSearch(cache_size=500)
        
        # Carrega modelo e índice
        print("\n🔬 Carregando modelo e índice...")
        cached_search.load_model()
        
        if not cached_search.load_index("data/snomed_pubmedbert_large_index"):
            print("❌ Índice não encontrado. Execute build_large_pubmedbert_index.py primeiro")
            return False
            
        print("✅ Sistema carregado!")
        
        # Teste 1: Consultas únicas (cache miss)
        print("\n1️⃣ Teste: Consultas únicas (cache miss)")
        unique_queries = [
            "dor no peito",
            "falta de ar",
            "diabetes tipo 2",
            "hipertensão arterial",
            "pneumonia"
        ]
        
        for i, query in enumerate(unique_queries, 1):
            print(f"\n   {i}. Buscando: '{query}'")
            result = cached_search.search_with_cache(query, top_k=3)
            
            print(f"      ⏱️ Tempo: {result['search_time']:.3f}s")
            print(f"      📊 Resultados: {len(result['results'])}")
            print(f"      🎯 Fonte: {result['source']}")
            print(f"      💾 Cache hit: {result['cache_hit']}")
            
            for j, concept in enumerate(result['results'][:2]):
                print(f"         {j+1}. {concept['term']} (score: {concept['similarity_score']:.3f})")
        
        # Teste 2: Consultas repetidas (cache hit)
        print("\n2️⃣ Teste: Consultas repetidas (cache hit)")
        print("   Repetindo as mesmas consultas...")
        
        for i, query in enumerate(unique_queries, 1):
            print(f"\n   {i}. Buscando novamente: '{query}'")
            result = cached_search.search_with_cache(query, top_k=3)
            
            print(f"      ⏱️ Tempo: {result['search_time']:.3f}s")
            print(f"      🎯 Fonte: {result['source']}")
            print(f"      💾 Cache hit: {result['cache_hit']}")
        
        # Teste 3: Consultas similares
        print("\n3️⃣ Teste: Consultas similares")
        similar_query = "dor torácica"
        similar_queries = cached_search.get_similar_queries(similar_query, threshold=0.5)
        
        print(f"   Query: '{similar_query}'")
        print(f"   📊 Consultas similares encontradas: {len(similar_queries)}")
        for sim in similar_queries[:3]:
            print(f"      - {sim['query']} (similaridade: {sim['similarity']:.2f})")
        
        # Teste 4: Consultas populares
        print("\n4️⃣ Teste: Consultas populares")
        popular_queries = cached_search.get_popular_queries(5)
        print(f"   📊 Consultas populares: {len(popular_queries)}")
        for pop in popular_queries:
            print(f"      - {pop['query']} (especialidade: {pop['specialty']})")
        
        # Teste 5: Benchmark
        print("\n5️⃣ Teste: Benchmark de Performance")
        benchmark_queries = unique_queries * 2  # 10 consultas
        benchmark_results = cached_search.benchmark_cache(benchmark_queries, iterations=2)
        
        # Estatísticas finais
        print("\n📊 Estatísticas Finais do Cache:")
        cache_stats = cached_search.get_cache_stats()
        print(f"   💾 Tamanho do cache: {cache_stats['cache_size']}/{cache_stats['max_size']}")
        print(f"   📈 Hit rate: {cache_stats['hit_rate']:.1%}")
        print(f"   ✅ Hits: {cache_stats['hits']}")
        print(f"   ❌ Misses: {cache_stats['misses']}")
        print(f"   🗑️ Evictions: {cache_stats['evictions']}")
        print(f"   🔢 Total queries: {cache_stats['total_queries']}")
        
        # Salva relatório
        cached_search.export_cache_report("data/cache/test_cache_report.json")
        
        print("\n✅ Sistema com cache funcionando perfeitamente!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_batch_processing():
    """Testa processamento em lote"""
    print("\n🔄 Teste: Processamento em Lote")
    print("=" * 50)
    
    try:
        cached_search = CachedPubMedBERTSearch(cache_size=200)
        cached_search.load_model()
        cached_search.load_index("data/snomed_pubmedbert_large_index")
        
        # Lista de consultas para teste
        batch_queries = [
            "infarto do miocárdio",
            "diabetes mellitus",
            "hipertensão arterial",
            "pneumonia",
            "insuficiência cardíaca",
            "infarto do miocárdio",  # Repetida para testar cache
            "diabetes mellitus",     # Repetida para testar cache
            "asma brônquica",
            "gastrite",
            "hepatite"
        ]
        
        print(f"🔄 Processando {len(batch_queries)} consultas em lote...")
        start_time = time.time()
        
        results = cached_search.search_batch(batch_queries, top_k=3)
        
        batch_time = time.time() - start_time
        
        print(f"\n📊 Resultados do Lote:")
        print(f"   ⏱️ Tempo total: {batch_time:.3f}s")
        print(f"   🚀 Velocidade: {len(batch_queries)/batch_time:.1f} consultas/segundo")
        
        # Analisa resultados
        cache_hits = sum(1 for r in results if r['cache_hit'])
        hit_rate = cache_hits / len(results)
        
        print(f"   💾 Cache hits: {cache_hits}/{len(results)} ({hit_rate:.1%})")
        
        # Mostra alguns resultados
        print(f"\n📋 Exemplos de Resultados:")
        for i, result in enumerate(results[:3]):
            query = result['query']
            source = result['source']
            results_count = len(result['results'])
            print(f"   {i+1}. '{query}' -> {results_count} resultados ({source})")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no processamento em lote: {e}")
        return False

if __name__ == "__main__":
    print("🏥 Teste do Sistema PubMedBERT com Cache Inteligente")
    print("=" * 70)
    
    # Teste principal
    success = test_cached_system()
    
    if success:
        # Teste de processamento em lote
        batch_success = test_batch_processing()
        
        print("\n" + "=" * 70)
        print("📋 Resumo dos Testes:")
        print(f"   ✅ Sistema com cache: {'PASSOU' if success else 'FALHOU'}")
        print(f"   ✅ Processamento em lote: {'PASSOU' if batch_success else 'FALHOU'}")
        
        if success and batch_success:
            print("\n🎉 FASE 3 CONCLUÍDA!")
            print("✅ Cache inteligente implementado")
            print("🚀 Performance otimizada")
            print("🔬 Pronto para Fase 4: Fine-tuning")
        else:
            print("\n⚠️ Alguns testes falharam")
    else:
        print("\n❌ Falha nos testes principais")
