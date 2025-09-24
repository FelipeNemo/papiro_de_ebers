"""
Sistema PubMedBERT com Cache Inteligente
Fase 3: Integração de cache para otimização
"""

import time
from typing import Dict, List, Optional
from .gpu_pubmedbert_search import GPUPubMedBERTSearch
from .intelligent_cache import IntelligentCache

class CachedPubMedBERTSearch:
    """Sistema PubMedBERT com cache inteligente"""
    
    def __init__(self, cache_size: int = 1000, device: str = None):
        """
        Inicializa sistema com cache
        
        Args:
            cache_size: Tamanho do cache
            device: Dispositivo para processamento
        """
        self.gpu_search = GPUPubMedBERTSearch(device)
        self.cache = IntelligentCache(cache_size)
        self.cache_enabled = True
        
        print(f"🚀 Sistema PubMedBERT com Cache Inicializado")
        print(f"💾 Cache: {cache_size} entradas")
        
    def load_model(self):
        """Carrega modelo PubMedBERT"""
        self.gpu_search.load_model()
        
    def load_index(self, index_path: str = "data/snomed_pubmedbert_large_index"):
        """Carrega índice SNOMED"""
        return self.gpu_search.load_index(index_path)
        
    def search_with_cache(self, query: str, specialty: str = None, top_k: int = 10, 
                         use_cache: bool = True) -> Dict:
        """
        Busca com cache inteligente
        
        Args:
            query: Query de busca
            specialty: Especialidade médica
            top_k: Número de resultados
            use_cache: Se deve usar cache
            
        Returns:
            Resultados da busca com metadados
        """
        start_time = time.time()
        
        # Tenta buscar no cache primeiro
        if use_cache and self.cache_enabled:
            cached_results = self.cache.get(query, specialty, top_k)
            if cached_results:
                cache_time = time.time() - start_time
                return {
                    "results": cached_results,
                    "source": "cache",
                    "search_time": cache_time,
                    "cache_hit": True,
                    "query": query,
                    "specialty": specialty,
                    "top_k": top_k
                }
        
        # Busca no sistema principal
        search_start = time.time()
        results = self.gpu_search.search_with_translation(query, specialty, top_k)
        search_time = time.time() - search_start
        
        # Armazena no cache
        if use_cache and self.cache_enabled:
            self.cache.put(query, results, specialty, top_k)
            
        total_time = time.time() - start_time
        
        return {
            "results": results,
            "source": "gpu_search",
            "search_time": search_time,
            "total_time": total_time,
            "cache_hit": False,
            "query": query,
            "specialty": specialty,
            "top_k": top_k
        }
        
    def search_batch(self, queries: List[str], specialty: str = None, top_k: int = 10) -> List[Dict]:
        """
        Busca em lote com cache
        
        Args:
            queries: Lista de queries
            specialty: Especialidade médica
            top_k: Número de resultados
            
        Returns:
            Lista de resultados
        """
        print(f"🔄 Processando {len(queries)} consultas em lote...")
        
        results = []
        cache_hits = 0
        
        for i, query in enumerate(queries, 1):
            print(f"   {i}/{len(queries)}: {query}")
            result = self.search_with_cache(query, specialty, top_k)
            results.append(result)
            
            if result["cache_hit"]:
                cache_hits += 1
                
        hit_rate = cache_hits / len(queries)
        print(f"📊 Cache hit rate: {hit_rate:.1%} ({cache_hits}/{len(queries)})")
        
        return results
        
    def get_similar_queries(self, query: str, threshold: float = 0.8) -> List[Dict]:
        """Busca consultas similares no cache"""
        return self.cache.get_similar_queries(query, threshold)
        
    def get_popular_queries(self, limit: int = 10) -> List[Dict]:
        """Retorna consultas populares"""
        return self.cache.get_popular_queries(limit)
        
    def get_cache_stats(self) -> Dict:
        """Retorna estatísticas do cache"""
        return self.cache.get_cache_stats()
        
    def optimize_cache(self):
        """Otimiza cache"""
        self.cache.optimize_cache()
        
    def clear_cache(self):
        """Limpa cache"""
        self.cache.clear_cache()
        
    def save_cache(self):
        """Salva cache"""
        self.cache.save_cache()
        
    def export_cache_report(self, output_file: str = "data/cache/cache_report.json"):
        """Exporta relatório do cache"""
        self.cache.export_cache_report(output_file)
        
    def disable_cache(self):
        """Desabilita cache"""
        self.cache_enabled = False
        print("⚠️ Cache desabilitado")
        
    def enable_cache(self):
        """Habilita cache"""
        self.cache_enabled = True
        print("✅ Cache habilitado")
        
    def benchmark_cache(self, test_queries: List[str], iterations: int = 3) -> Dict:
        """
        Benchmark do sistema com e sem cache
        
        Args:
            test_queries: Lista de queries para teste
            iterations: Número de iterações
            
        Returns:
            Resultados do benchmark
        """
        print(f"🧪 Benchmark do Cache - {len(test_queries)} queries, {iterations} iterações")
        
        # Teste com cache
        print("\n1️⃣ Testando com cache...")
        cache_times = []
        for i in range(iterations):
            start_time = time.time()
            for query in test_queries:
                self.search_with_cache(query, use_cache=True)
            cache_times.append(time.time() - start_time)
            
        # Teste sem cache
        print("2️⃣ Testando sem cache...")
        no_cache_times = []
        for i in range(iterations):
            start_time = time.time()
            for query in test_queries:
                self.search_with_cache(query, use_cache=False)
            no_cache_times.append(time.time() - start_time)
            
        # Calcula estatísticas
        avg_cache_time = sum(cache_times) / len(cache_times)
        avg_no_cache_time = sum(no_cache_times) / len(no_cache_times)
        speedup = avg_no_cache_time / avg_cache_time
        
        cache_stats = self.get_cache_stats()
        
        benchmark_results = {
            "test_queries": len(test_queries),
            "iterations": iterations,
            "avg_cache_time": avg_cache_time,
            "avg_no_cache_time": avg_no_cache_time,
            "speedup": speedup,
            "cache_hit_rate": cache_stats["hit_rate"],
            "cache_size": cache_stats["cache_size"]
        }
        
        print(f"\n📊 Resultados do Benchmark:")
        print(f"   ⏱️ Tempo com cache: {avg_cache_time:.3f}s")
        print(f"   ⏱️ Tempo sem cache: {avg_no_cache_time:.3f}s")
        print(f"   🚀 Aceleração: {speedup:.1f}x")
        print(f"   📈 Hit rate: {cache_stats['hit_rate']:.1%}")
        
        return benchmark_results
