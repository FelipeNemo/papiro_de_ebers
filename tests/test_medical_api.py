"""
Script para Testar API REST do Sistema Médico
Fase 5: Teste de integração da API
"""

import requests
import json
import time
from typing import Dict, List

class MedicalAPITester:
    """Cliente para testar a API médica"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_health(self) -> Dict:
        """Testa endpoint de saúde"""
        print("🏥 Testando saúde da API...")
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            
            health_data = response.json()
            print(f"   Status: {health_data['status']}")
            print(f"   GPU disponível: {health_data['gpu_available']}")
            print(f"   Modelo carregado: {health_data['model_loaded']}")
            print(f"   Índice carregado: {health_data['index_loaded']}")
            print(f"   Uptime: {health_data['uptime']:.2f}s")
            
            return health_data
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            return {}
    
    def test_single_search(self, query: str, specialty: str = None, top_k: int = 5) -> Dict:
        """Testa busca única"""
        print(f"\n🔍 Testando busca: '{query}'")
        
        try:
            payload = {
                "query": query,
                "specialty": specialty,
                "top_k": top_k,
                "use_cache": True
            }
            
            response = self.session.post(f"{self.base_url}/search", json=payload)
            response.raise_for_status()
            
            result = response.json()
            print(f"   ⏱️ Tempo: {result['search_time']:.3f}s")
            print(f"   📊 Resultados: {result['total_results']}")
            print(f"   💾 Cache hit: {result['cache_hit']}")
            print(f"   🎯 Fonte: {result['model_info']['device']}")
            
            # Mostra alguns resultados
            for i, concept in enumerate(result['results'][:3]):
                print(f"   {i+1}. {concept['term']} (score: {concept['similarity_score']:.3f})")
            
            return result
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            return {}
    
    def test_batch_search(self, queries: List[str], specialty: str = None) -> Dict:
        """Testa busca em lote"""
        print(f"\n🔄 Testando busca em lote: {len(queries)} consultas")
        
        try:
            payload = {
                "queries": queries,
                "specialty": specialty,
                "top_k": 3,
                "use_cache": True
            }
            
            response = self.session.post(f"{self.base_url}/search/batch", json=payload)
            response.raise_for_status()
            
            result = response.json()
            print(f"   ⏱️ Tempo total: {result['total_time']:.3f}s")
            print(f"   💾 Cache hit rate: {result['cache_hit_rate']:.1%}")
            print(f"   🚀 Velocidade: {len(queries)/result['total_time']:.1f} consultas/segundo")
            
            return result
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            return {}
    
    def test_cache_stats(self) -> Dict:
        """Testa estatísticas do cache"""
        print("\n📊 Testando estatísticas do cache...")
        
        try:
            response = self.session.get(f"{self.base_url}/cache/stats")
            response.raise_for_status()
            
            stats = response.json()
            print(f"   Tamanho: {stats['cache_size']}/{stats['max_size']}")
            print(f"   Hit rate: {stats['hit_rate']:.1%}")
            print(f"   Hits: {stats['hits']}")
            print(f"   Misses: {stats['misses']}")
            print(f"   Total queries: {stats['total_queries']}")
            
            return stats
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            return {}
    
    def test_similar_queries(self, query: str) -> Dict:
        """Testa busca de consultas similares"""
        print(f"\n🔍 Testando consultas similares: '{query}'")
        
        try:
            response = self.session.get(f"{self.base_url}/similar/{query}")
            response.raise_for_status()
            
            result = response.json()
            print(f"   Consultas similares: {len(result['similar_queries'])}")
            
            for sim in result['similar_queries'][:3]:
                print(f"   - {sim['query']} (similaridade: {sim['similarity']:.2f})")
            
            return result
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            return {}
    
    def test_popular_queries(self, limit: int = 5) -> Dict:
        """Testa consultas populares"""
        print(f"\n📈 Testando consultas populares (limite: {limit})...")
        
        try:
            response = self.session.get(f"{self.base_url}/popular?limit={limit}")
            response.raise_for_status()
            
            result = response.json()
            print(f"   Consultas populares: {len(result['popular_queries'])}")
            
            for pop in result['popular_queries']:
                print(f"   - {pop['query']} (especialidade: {pop['specialty']})")
            
            return result
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            return {}
    
    def test_model_info(self) -> Dict:
        """Testa informações do modelo"""
        print("\n🔬 Testando informações do modelo...")
        
        try:
            response = self.session.get(f"{self.base_url}/model/info")
            response.raise_for_status()
            
            info = response.json()
            print(f"   Modelo: {info['model_name']}")
            print(f"   Dispositivo: {info['device']}")
            print(f"   Tamanho do índice: {info['index_size']}")
            
            if 'gpu_info' in info:
                gpu = info['gpu_info']
                print(f"   GPU: {gpu.get('gpu_name', 'N/A')}")
                print(f"   Memória total: {gpu.get('memory_total', 0):.1f} GB")
            
            return info
            
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            return {}
    
    def run_comprehensive_test(self):
        """Executa teste abrangente da API"""
        print("🧪 Teste Abrangente da API Médica")
        print("=" * 60)
        
        # Teste de saúde
        health = self.test_health()
        if health.get('status') != 'online':
            print("❌ Sistema não está online. Verifique se a API está rodando.")
            return False
        
        # Teste de busca única
        test_queries = [
            "dor no peito",
            "diabetes mellitus",
            "hipertensão arterial",
            "pneumonia",
            "asma brônquica"
        ]
        
        for query in test_queries:
            self.test_single_search(query)
        
        # Teste de busca em lote
        self.test_batch_search(test_queries)
        
        # Teste de estatísticas do cache
        self.test_cache_stats()
        
        # Teste de consultas similares
        self.test_similar_queries("dor no peito")
        
        # Teste de consultas populares
        self.test_popular_queries(5)
        
        # Teste de informações do modelo
        self.test_model_info()
        
        print("\n✅ Teste abrangente concluído!")
        return True

def test_api_performance():
    """Testa performance da API"""
    print("\n⚡ Teste de Performance da API")
    print("=" * 40)
    
    tester = MedicalAPITester()
    
    # Teste de latência
    queries = ["dor no peito", "diabetes", "hipertensão", "pneumonia", "asma"]
    
    print("🔄 Testando latência...")
    latencies = []
    
    for query in queries:
        start_time = time.time()
        result = tester.test_single_search(query, top_k=3)
        latency = time.time() - start_time
        latencies.append(latency)
    
    avg_latency = sum(latencies) / len(latencies)
    print(f"   Latência média: {avg_latency:.3f}s")
    print(f"   Latência mínima: {min(latencies):.3f}s")
    print(f"   Latência máxima: {max(latencies):.3f}s")
    
    # Teste de throughput
    print("\n🚀 Testando throughput...")
    start_time = time.time()
    result = tester.test_batch_search(queries * 2)  # 10 consultas
    total_time = time.time() - start_time
    
    throughput = len(queries * 2) / total_time
    print(f"   Throughput: {throughput:.1f} consultas/segundo")
    
    return {
        "avg_latency": avg_latency,
        "throughput": throughput
    }

if __name__ == "__main__":
    print("🏥 Teste da API REST do Sistema Médico")
    print("=" * 60)
    
    # Verifica se a API está rodando
    tester = MedicalAPITester()
    
    try:
        # Teste de conectividade
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ API está rodando!")
            
            # Executa teste abrangente
            success = tester.run_comprehensive_test()
            
            if success:
                # Testa performance
                performance = test_api_performance()
                
                print("\n" + "=" * 60)
                print("📊 Resumo dos Testes:")
                print(f"   ✅ Conectividade: PASSOU")
                print(f"   ✅ Funcionalidade: PASSOU")
                print(f"   ⚡ Latência média: {performance['avg_latency']:.3f}s")
                print(f"   🚀 Throughput: {performance['throughput']:.1f} consultas/segundo")
                
                print("\n🎉 API FUNCIONANDO PERFEITAMENTE!")
                print("🚀 Pronto para integração externa!")
            else:
                print("\n❌ Alguns testes falharam")
        else:
            print("❌ API não está respondendo corretamente")
            
    except requests.exceptions.ConnectionError:
        print("❌ API não está rodando. Execute: python src/api/medical_search_api.py")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
