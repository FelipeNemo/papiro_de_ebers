"""
API REST para Sistema de Busca Médica PubMedBERT
Fase 5: Interface para integração externa
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import time
import json
import os
import sys

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.cached_pubmedbert_search import CachedPubMedBERTSearch
from src.core.config import SNOMED_DATA_PATH

# Inicializa FastAPI
app = FastAPI(
    title="Sistema de Busca Médica PubMedBERT",
    description="API REST para busca de conceitos SNOMED CT usando PubMedBERT com GPU",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variáveis globais
search_system = None
cache_stats = {}

class SearchRequest(BaseModel):
    """Modelo para requisição de busca"""
    query: str
    specialty: Optional[str] = None
    top_k: Optional[int] = 10
    use_cache: Optional[bool] = True

class SearchResponse(BaseModel):
    """Modelo para resposta de busca"""
    query: str
    specialty: Optional[str]
    results: List[Dict]
    search_time: float
    cache_hit: bool
    total_results: int
    model_info: Dict

class BatchSearchRequest(BaseModel):
    """Modelo para busca em lote"""
    queries: List[str]
    specialty: Optional[str] = None
    top_k: Optional[int] = 10
    use_cache: Optional[bool] = True

class BatchSearchResponse(BaseModel):
    """Modelo para resposta de busca em lote"""
    queries: List[str]
    results: List[Dict]
    total_time: float
    cache_hit_rate: float
    model_info: Dict

class SystemStatus(BaseModel):
    """Modelo para status do sistema"""
    status: str
    gpu_available: bool
    model_loaded: bool
    index_loaded: bool
    cache_stats: Dict
    uptime: float

# Inicialização do sistema
@app.on_event("startup")
async def startup_event():
    """Inicializa o sistema na startup"""
    global search_system, cache_stats
    
    print("🚀 Inicializando Sistema de Busca Médica PubMedBERT...")
    
    try:
        # Inicializa sistema de busca
        search_system = CachedPubMedBERTSearch(cache_size=1000)
        
        # Carrega modelo
        print("📥 Carregando modelo PubMedBERT...")
        search_system.load_model()
        
        # Carrega índice
        print("📂 Carregando índice SNOMED...")
        if search_system.load_index("data/snomed_pubmedbert_large_index"):
            print("✅ Índice carregado com sucesso!")
        else:
            print("⚠️ Índice não encontrado, criando...")
            search_system.gpu_search.build_gpu_index(
                snomed_data_path=SNOMED_DATA_PATH,
                output_path="data/snomed_pubmedbert_large_index",
                sample_size=10000,
                batch_size=64
            )
            search_system.load_index("data/snomed_pubmedbert_large_index")
        
        # Inicializa estatísticas
        cache_stats = {
            "startup_time": time.time(),
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        print("✅ Sistema inicializado com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")
        search_system = None

@app.get("/", response_model=Dict)
async def root():
    """Endpoint raiz"""
    return {
        "message": "Sistema de Busca Médica PubMedBERT",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs"
    }

@app.get("/health", response_model=SystemStatus)
async def health_check():
    """Verifica saúde do sistema"""
    global search_system, cache_stats
    
    if search_system is None:
        return SystemStatus(
            status="offline",
            gpu_available=False,
            model_loaded=False,
            index_loaded=False,
            cache_stats={},
            uptime=0
        )
    
    # Verifica GPU
    gpu_available = search_system.gpu_search.device == "cuda"
    
    # Verifica modelo
    model_loaded = search_system.gpu_search.model is not None
    
    # Verifica índice
    index_loaded = search_system.gpu_search.index is not None
    
    # Estatísticas do cache
    cache_stats_current = search_system.get_cache_stats()
    
    # Uptime
    uptime = time.time() - cache_stats.get("startup_time", time.time())
    
    return SystemStatus(
        status="online" if (model_loaded and index_loaded) else "degraded",
        gpu_available=gpu_available,
        model_loaded=model_loaded,
        index_loaded=index_loaded,
        cache_stats=cache_stats_current,
        uptime=uptime
    )

@app.post("/search", response_model=SearchResponse)
async def search_concepts(request: SearchRequest):
    """Busca conceitos SNOMED CT"""
    global search_system, cache_stats
    
    if search_system is None:
        raise HTTPException(status_code=503, detail="Sistema não inicializado")
    
    try:
        # Executa busca
        start_time = time.time()
        result = search_system.search_with_cache(
            query=request.query,
            specialty=request.specialty,
            top_k=request.top_k,
            use_cache=request.use_cache
        )
        search_time = time.time() - start_time
        
        # Atualiza estatísticas
        cache_stats["total_requests"] += 1
        if result["cache_hit"]:
            cache_stats["cache_hits"] += 1
        else:
            cache_stats["cache_misses"] += 1
        
        # Informações do modelo
        model_info = {
            "model_name": search_system.gpu_search.model_name,
            "device": search_system.gpu_search.device,
            "index_size": len(search_system.gpu_search.concepts_df) if search_system.gpu_search.concepts_df is not None else 0
        }
        
        return SearchResponse(
            query=result["query"],
            specialty=result["specialty"],
            results=result["results"],
            search_time=search_time,
            cache_hit=result["cache_hit"],
            total_results=len(result["results"]),
            model_info=model_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")

@app.post("/search/batch", response_model=BatchSearchResponse)
async def search_concepts_batch(request: BatchSearchRequest):
    """Busca conceitos em lote"""
    global search_system, cache_stats
    
    if search_system is None:
        raise HTTPException(status_code=503, detail="Sistema não inicializado")
    
    try:
        # Executa busca em lote
        start_time = time.time()
        results = search_system.search_batch(
            queries=request.queries,
            specialty=request.specialty,
            top_k=request.top_k
        )
        total_time = time.time() - start_time
        
        # Calcula hit rate do cache
        cache_hits = sum(1 for r in results if r["cache_hit"])
        cache_hit_rate = cache_hits / len(results) if results else 0
        
        # Atualiza estatísticas
        cache_stats["total_requests"] += len(request.queries)
        cache_stats["cache_hits"] += cache_hits
        cache_stats["cache_misses"] += len(request.queries) - cache_hits
        
        # Informações do modelo
        model_info = {
            "model_name": search_system.gpu_search.model_name,
            "device": search_system.gpu_search.device,
            "index_size": len(search_system.gpu_search.concepts_df) if search_system.gpu_search.concepts_df is not None else 0
        }
        
        return BatchSearchResponse(
            queries=request.queries,
            results=results,
            total_time=total_time,
            cache_hit_rate=cache_hit_rate,
            model_info=model_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na busca em lote: {str(e)}")

@app.get("/cache/stats", response_model=Dict)
async def get_cache_stats():
    """Retorna estatísticas do cache"""
    global search_system
    
    if search_system is None:
        raise HTTPException(status_code=503, detail="Sistema não inicializado")
    
    return search_system.get_cache_stats()

@app.post("/cache/clear")
async def clear_cache():
    """Limpa o cache"""
    global search_system
    
    if search_system is None:
        raise HTTPException(status_code=503, detail="Sistema não inicializado")
    
    search_system.clear_cache()
    return {"message": "Cache limpo com sucesso"}

@app.post("/cache/optimize")
async def optimize_cache():
    """Otimiza o cache"""
    global search_system
    
    if search_system is None:
        raise HTTPException(status_code=503, detail="Sistema não inicializado")
    
    search_system.optimize_cache()
    return {"message": "Cache otimizado com sucesso"}

@app.get("/similar/{query}")
async def find_similar_queries(query: str, threshold: float = 0.8):
    """Encontra consultas similares no cache"""
    global search_system
    
    if search_system is None:
        raise HTTPException(status_code=503, detail="Sistema não inicializado")
    
    try:
        similar_queries = search_system.get_similar_queries(query, threshold)
        return {
            "query": query,
            "threshold": threshold,
            "similar_queries": similar_queries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar consultas similares: {str(e)}")

@app.get("/popular")
async def get_popular_queries(limit: int = 10):
    """Retorna consultas populares"""
    global search_system
    
    if search_system is None:
        raise HTTPException(status_code=503, detail="Sistema não inicializado")
    
    try:
        popular_queries = search_system.get_popular_queries(limit)
        return {
            "limit": limit,
            "popular_queries": popular_queries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar consultas populares: {str(e)}")

@app.get("/model/info", response_model=Dict)
async def get_model_info():
    """Retorna informações do modelo"""
    global search_system
    
    if search_system is None:
        raise HTTPException(status_code=503, detail="Sistema não inicializado")
    
    try:
        gpu_info = search_system.gpu_search.get_gpu_info()
        return {
            "model_name": search_system.gpu_search.model_name,
            "device": search_system.gpu_search.device,
            "gpu_info": gpu_info,
            "index_size": len(search_system.gpu_search.concepts_df) if search_system.gpu_search.concepts_df is not None else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter informações do modelo: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "medical_search_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
