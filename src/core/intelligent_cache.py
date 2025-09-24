"""
Sistema de Cache Inteligente para PubMedBERT
Fase 3: Otimização de consultas frequentes
"""

import json
import time
import hashlib
from typing import Dict, List, Optional, Tuple
from collections import OrderedDict
import os
import pickle

class IntelligentCache:
    """Sistema de cache inteligente para consultas médicas"""
    
    def __init__(self, cache_size: int = 1000, cache_file: str = "data/cache/medical_cache.pkl"):
        """
        Inicializa o sistema de cache
        
        Args:
            cache_size: Tamanho máximo do cache
            cache_file: Arquivo para persistir cache
        """
        self.cache_size = cache_size
        self.cache_file = cache_file
        self.cache = OrderedDict()  # LRU cache
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_queries": 0
        }
        
        # Cria diretório de cache
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        
        # Carrega cache existente
        self.load_cache()
        
    def _generate_key(self, query: str, specialty: str = None, top_k: int = 10) -> str:
        """Gera chave única para a consulta"""
        key_data = f"{query.lower().strip()}|{specialty or 'general'}|{top_k}"
        return hashlib.md5(key_data.encode()).hexdigest()
        
    def get(self, query: str, specialty: str = None, top_k: int = 10) -> Optional[List[Dict]]:
        """
        Busca resultado no cache
        
        Args:
            query: Query de busca
            specialty: Especialidade médica
            top_k: Número de resultados
            
        Returns:
            Resultados do cache ou None se não encontrado
        """
        key = self._generate_key(query, specialty, top_k)
        self.stats["total_queries"] += 1
        
        if key in self.cache:
            # Move para o final (LRU)
            result = self.cache.pop(key)
            self.cache[key] = result
            self.stats["hits"] += 1
            return result["data"]
        else:
            self.stats["misses"] += 1
            return None
            
    def put(self, query: str, results: List[Dict], specialty: str = None, top_k: int = 10):
        """
        Armazena resultado no cache
        
        Args:
            query: Query de busca
            results: Resultados da busca
            specialty: Especialidade médica
            top_k: Número de resultados
        """
        key = self._generate_key(query, specialty, top_k)
        
        # Remove se já existe
        if key in self.cache:
            del self.cache[key]
            
        # Adiciona novo resultado
        self.cache[key] = {
            "data": results,
            "timestamp": time.time(),
            "query": query,
            "specialty": specialty,
            "top_k": top_k
        }
        
        # Remove itens antigos se necessário (LRU)
        while len(self.cache) > self.cache_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            self.stats["evictions"] += 1
            
    def get_similar_queries(self, query: str, threshold: float = 0.8) -> List[Dict]:
        """
        Busca consultas similares no cache
        
        Args:
            query: Query de busca
            threshold: Limiar de similaridade
            
        Returns:
            Lista de consultas similares
        """
        similar_queries = []
        query_lower = query.lower().strip()
        
        for key, data in self.cache.items():
            cached_query = data["query"].lower().strip()
            
            # Calcula similaridade simples (Jaccard)
            query_words = set(query_lower.split())
            cached_words = set(cached_query.split())
            
            if query_words and cached_words:
                similarity = len(query_words & cached_words) / len(query_words | cached_words)
                
                if similarity >= threshold:
                    similar_queries.append({
                        "query": data["query"],
                        "specialty": data["specialty"],
                        "similarity": similarity,
                        "timestamp": data["timestamp"],
                        "results_count": len(data["data"])
                    })
        
        # Ordena por similaridade
        similar_queries.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_queries[:5]  # Top 5 similares
        
    def get_popular_queries(self, limit: int = 10) -> List[Dict]:
        """
        Retorna consultas mais populares
        
        Args:
            limit: Número máximo de consultas
            
        Returns:
            Lista de consultas populares
        """
        # Por simplicidade, retorna as mais recentes
        # Em uma implementação mais sofisticada, poderia contar frequência
        popular = []
        for data in list(self.cache.values())[-limit:]:
            popular.append({
                "query": data["query"],
                "specialty": data["specialty"],
                "timestamp": data["timestamp"],
                "results_count": len(data["data"])
            })
        return popular
        
    def get_cache_stats(self) -> Dict:
        """Retorna estatísticas do cache"""
        hit_rate = self.stats["hits"] / max(self.stats["total_queries"], 1)
        
        return {
            "cache_size": len(self.cache),
            "max_size": self.cache_size,
            "hit_rate": hit_rate,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "evictions": self.stats["evictions"],
            "total_queries": self.stats["total_queries"]
        }
        
    def clear_cache(self):
        """Limpa o cache"""
        self.cache.clear()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0, "total_queries": 0}
        
    def save_cache(self):
        """Salva cache no disco"""
        try:
            cache_data = {
                "cache": dict(self.cache),
                "stats": self.stats
            }
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
        except Exception as e:
            print(f"⚠️ Erro ao salvar cache: {e}")
            
    def load_cache(self):
        """Carrega cache do disco"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    self.cache = OrderedDict(cache_data.get("cache", {}))
                    self.stats = cache_data.get("stats", {"hits": 0, "misses": 0, "evictions": 0, "total_queries": 0})
                print(f"📂 Cache carregado: {len(self.cache)} entradas")
        except Exception as e:
            print(f"⚠️ Erro ao carregar cache: {e}")
            self.cache = OrderedDict()
            
    def optimize_cache(self):
        """Otimiza cache removendo entradas antigas"""
        current_time = time.time()
        max_age = 7 * 24 * 3600  # 7 dias
        
        keys_to_remove = []
        for key, data in self.cache.items():
            if current_time - data["timestamp"] > max_age:
                keys_to_remove.append(key)
                
        for key in keys_to_remove:
            del self.cache[key]
            
        if keys_to_remove:
            print(f"🧹 Cache otimizado: removidas {len(keys_to_remove)} entradas antigas")
            
    def export_cache_report(self, output_file: str = "data/cache/cache_report.json"):
        """Exporta relatório do cache"""
        report = {
            "timestamp": time.time(),
            "stats": self.get_cache_stats(),
            "popular_queries": self.get_popular_queries(20),
            "cache_entries": len(self.cache)
        }
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        print(f"📊 Relatório do cache exportado: {output_file}")
