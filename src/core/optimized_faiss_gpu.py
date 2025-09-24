"""
Otimizações FAISS para RTX 3060 Ti
Implementa tuning prático para máxima performance
"""

import faiss
import numpy as np
import torch
import os
from typing import Tuple, Optional
import time

class OptimizedFAISSGPU:
    """Otimizações FAISS para RTX 3060 Ti"""
    
    def __init__(self, device: str = "cuda"):
        """
        Inicializa otimizações FAISS
        
        Args:
            device: Dispositivo para processamento
        """
        self.device = device
        self.gpu_resources = None
        self.index = None
        
        # Configurações otimizadas para RTX 3060 Ti
        self.config = {
            "nlist": 224,  # √50k ≈ 224
            "nprobe": 16,  # 16-32 para boa precisão
            "m": 48,       # Para PQ
            "nbits": 8,    # Para PQ
            "use_gpu": True,
            "gpu_memory_fraction": 0.8,  # 80% da GPU
            "warmup_queries": 10
        }
        
        print(f"🚀 FAISS GPU Otimizado para RTX 3060 Ti")
        print(f"🎯 Dispositivo: {self.device}")
        
    def setup_gpu_resources(self):
        """Configura recursos GPU"""
        if self.device == "cuda" and torch.cuda.is_available():
            print("🔧 Configurando recursos GPU...")
            
            # Verifica se FAISS GPU está disponível
            try:
                import faiss
                if hasattr(faiss, 'StandardGpuResources'):
                    # Configura GPU
                    self.gpu_resources = faiss.StandardGpuResources()
                    
                    # Configura memória GPU
                    self.gpu_resources.setTempMemory(
                        int(self.config["gpu_memory_fraction"] * torch.cuda.get_device_properties(0).total_memory)
                    )
                    
                    print(f"✅ GPU configurada: {torch.cuda.get_device_name(0)}")
                    print(f"💾 Memória alocada: {self.config['gpu_memory_fraction']*100:.0f}%")
                else:
                    print("⚠️ FAISS GPU não disponível, usando CPU")
                    self.device = "cpu"
                    self.gpu_resources = None
            except Exception as e:
                print(f"⚠️ Erro ao configurar GPU: {e}, usando CPU")
                self.device = "cpu"
                self.gpu_resources = None
            
            # Configura threads
            torch.set_num_threads(1)  # Evita conflitos
        else:
            print("⚠️ GPU não disponível, usando CPU")
            self.device = "cpu"
            self.gpu_resources = None
            
    def create_optimized_index(self, dimension: int, num_vectors: int) -> faiss.Index:
        """
        Cria índice FAISS otimizado
        
        Args:
            dimension: Dimensão dos vetores
            num_vectors: Número de vetores
            
        Returns:
            Índice FAISS otimizado
        """
        print(f"🔨 Criando índice FAISS otimizado...")
        print(f"   📊 Dimensão: {dimension}")
        print(f"   📊 Vetores: {num_vectors}")
        
        # Escolhe tipo de índice baseado no tamanho
        if num_vectors <= 100000:
            # IVF-Flat para ≤100k
            print("   📊 Usando IVF-Flat (≤100k vetores)")
            quantizer = faiss.IndexFlatL2(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, self.config["nlist"])
        else:
            # IVF-PQ para >100k
            print("   📊 Usando IVF-PQ (>100k vetores)")
            quantizer = faiss.IndexFlatL2(dimension)
            index = faiss.IndexIVFPQ(quantizer, dimension, self.config["nlist"], self.config["m"], self.config["nbits"])
            
        # Move para GPU se disponível
        if self.device == "cuda" and self.gpu_resources and hasattr(faiss, 'index_cpu_to_gpu'):
            print("   🎯 Movendo para GPU...")
            index = faiss.index_cpu_to_gpu(self.gpu_resources, 0, index)
        else:
            print("   🖥️ Usando CPU")
            
        self.index = index
        print("✅ Índice criado!")
        
        return index
        
    def train_index(self, vectors: np.ndarray):
        """Treina índice com vetores"""
        print("🎓 Treinando índice...")
        
        # Normaliza vetores (L2)
        vectors = self._normalize_vectors(vectors)
        
        # Treina índice
        start_time = time.time()
        self.index.train(vectors.astype('float32'))
        train_time = time.time() - start_time
        
        print(f"✅ Índice treinado em {train_time:.2f}s")
        
    def add_vectors(self, vectors: np.ndarray):
        """Adiciona vetores ao índice"""
        print("📝 Adicionando vetores ao índice...")
        
        # Normaliza vetores
        vectors = self._normalize_vectors(vectors)
        
        # Adiciona vetores
        start_time = time.time()
        self.index.add(vectors.astype('float32'))
        add_time = time.time() - start_time
        
        print(f"✅ {len(vectors)} vetores adicionados em {add_time:.2f}s")
        
    def search(self, query_vectors: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Busca no índice
        
        Args:
            query_vectors: Vetores de consulta
            k: Número de resultados
            
        Returns:
            (scores, indices)
        """
        # Normaliza vetores de consulta
        query_vectors = self._normalize_vectors(query_vectors)
        
        # Configura nprobe
        if hasattr(self.index, 'nprobe'):
            self.index.nprobe = self.config["nprobe"]
            
        # Busca
        start_time = time.time()
        scores, indices = self.index.search(query_vectors.astype('float32'), k)
        search_time = time.time() - start_time
        
        return scores, indices, search_time
        
    def warmup(self, num_queries: int = 10):
        """Faz warm-up do índice"""
        print(f"🔥 Fazendo warm-up com {num_queries} consultas...")
        
        if self.index is None:
            print("⚠️ Índice não criado, pulando warm-up")
            return
            
        # Gera consultas aleatórias
        dimension = self.index.d
        query_vectors = np.random.randn(num_queries, dimension).astype('float32')
        
        # Busca de warm-up
        for i in range(num_queries):
            self.search(query_vectors[i:i+1], k=10)
            
        print("✅ Warm-up concluído!")
        
    def _normalize_vectors(self, vectors: np.ndarray) -> np.ndarray:
        """Normaliza vetores L2"""
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Evita divisão por zero
        return vectors / norms
        
    def save_index(self, path: str):
        """Salva índice"""
        print(f"💾 Salvando índice em: {path}")
        
        if self.device == "cuda" and self.gpu_resources and hasattr(faiss, 'index_gpu_to_cpu'):
            # Move para CPU antes de salvar
            cpu_index = faiss.index_gpu_to_cpu(self.index)
            faiss.write_index(cpu_index, path)
        else:
            faiss.write_index(self.index, path)
            
        print("✅ Índice salvo!")
        
    def load_index(self, path: str):
        """Carrega índice"""
        print(f"📂 Carregando índice de: {path}")
        
        # Carrega índice
        self.index = faiss.read_index(path)
        
        # Move para GPU se disponível
        if self.device == "cuda" and self.gpu_resources and hasattr(faiss, 'index_cpu_to_gpu'):
            print("   🎯 Movendo para GPU...")
            self.index = faiss.index_cpu_to_gpu(self.gpu_resources, 0, self.index)
        else:
            print("   🖥️ Usando CPU")
            
        print("✅ Índice carregado!")
        
    def get_index_stats(self) -> dict:
        """Retorna estatísticas do índice"""
        if self.index is None:
            return {}
            
        stats = {
            "dimension": self.index.d,
            "total_vectors": self.index.ntotal,
            "is_trained": self.index.is_trained,
            "device": self.device
        }
        
        if hasattr(self.index, 'nlist'):
            stats["nlist"] = self.index.nlist
        if hasattr(self.index, 'nprobe'):
            stats["nprobe"] = self.index.nprobe
            
        return stats
        
    def benchmark(self, query_vectors: np.ndarray, k: int = 10, num_runs: int = 100):
        """Faz benchmark do índice"""
        print(f"📊 Benchmarking índice...")
        print(f"   🔍 Consultas: {len(query_vectors)}")
        print(f"   🎯 k: {k}")
        print(f"   🔄 Runs: {num_runs}")
        
        # Warm-up
        self.warmup()
        
        # Benchmark
        latencies = []
        for i in range(num_runs):
            start_time = time.time()
            scores, indices, search_time = self.search(query_vectors, k)
            latency = time.time() - start_time
            latencies.append(latency)
            
        # Estatísticas
        avg_latency = np.mean(latencies)
        min_latency = np.min(latencies)
        max_latency = np.max(latencies)
        std_latency = np.std(latencies)
        throughput = len(query_vectors) / avg_latency
        
        print(f"\n📊 Resultados do Benchmark:")
        print(f"   ⏱️ Latência média: {avg_latency:.3f}s")
        print(f"   ⏱️ Latência mínima: {min_latency:.3f}s")
        print(f"   ⏱️ Latência máxima: {max_latency:.3f}s")
        print(f"   📊 Desvio padrão: {std_latency:.3f}s")
        print(f"   🚀 Throughput: {throughput:.1f} consultas/segundo")
        
        return {
            "avg_latency": avg_latency,
            "min_latency": min_latency,
            "max_latency": max_latency,
            "std_latency": std_latency,
            "throughput": throughput
        }
        
    def optimize_for_rtx3060ti(self):
        """Otimizações específicas para RTX 3060 Ti"""
        print("🎯 Aplicando otimizações para RTX 3060 Ti...")
        
        # Configurações específicas para RTX 3060 Ti
        rtx3060ti_config = {
            "nlist": 256,  # Otimizado para 8GB VRAM
            "nprobe": 32,  # Balance entre velocidade e precisão
            "m": 64,       # Para PQ
            "nbits": 8,    # Para PQ
            "gpu_memory_fraction": 0.9,  # 90% da VRAM
            "batch_size": 64  # Lote otimizado
        }
        
        # Atualiza configurações
        self.config.update(rtx3060ti_config)
        
        print("✅ Otimizações aplicadas!")
        print(f"   📊 nlist: {self.config['nlist']}")
        print(f"   📊 nprobe: {self.config['nprobe']}")
        print(f"   📊 m: {self.config['m']}")
        print(f"   📊 nbits: {self.config['nbits']}")
        print(f"   💾 GPU memory: {self.config['gpu_memory_fraction']*100:.0f}%")
        
    def cleanup(self):
        """Limpa recursos"""
        if self.gpu_resources:
            del self.gpu_resources
        if self.index:
            del self.index
        torch.cuda.empty_cache()
        print("🧹 Recursos limpos!")
