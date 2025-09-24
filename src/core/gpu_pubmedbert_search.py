"""
Sistema de Busca PubMedBERT Otimizado para GPU
Usa RTX 3060 Ti para acelerar geração de embeddings
"""

import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer
from typing import Dict, List, Tuple, Optional
import faiss
import pickle
import os
from .medical_filters import MedicalFilters
from .medical_translator import MedicalTranslator
from .config import EMBEDDING_MODEL

class GPUPubMedBERTSearch:
    """Sistema de busca PubMedBERT otimizado para GPU"""
    
    def __init__(self, device: str = None):
        """
        Inicializa o sistema de busca PubMedBERT com GPU
        
        Args:
            device: Dispositivo para processamento ('cuda' ou 'cpu')
        """
        self.model_name = EMBEDDING_MODEL
        self.device = device or self._get_best_device()
        self.model = None
        self.index = None
        self.concepts_df = None
        self.medical_filters = MedicalFilters()
        self.medical_translator = MedicalTranslator()
        
        print(f"🚀 Inicializando PubMedBERT com {self.device}")
        
    def _get_best_device(self) -> str:
        """Detecta o melhor dispositivo disponível"""
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"🎯 GPU detectada: {gpu_name}")
            return "cuda"
        else:
            print("⚠️ GPU não disponível, usando CPU")
            return "cpu"
            
    def load_model(self):
        """Carrega o modelo PubMedBERT na GPU"""
        print(f"🔬 Carregando modelo PubMedBERT na {self.device}...")
        
        # Carrega modelo
        self.model = SentenceTransformer(self.model_name)
        
        # Move para GPU se disponível
        if self.device == "cuda":
            self.model = self.model.to(self.device)
            print(f"✅ Modelo movido para GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("✅ Modelo carregado na CPU")
            
    def load_index(self, index_path: str = "data/snomed_pubmedbert_gpu_index"):
        """Carrega o índice FAISS"""
        if not os.path.exists(index_path):
            print(f"❌ Índice não encontrado em: {index_path}")
            return False
            
        print(f"📂 Carregando índice de: {index_path}")
        
        # Carrega índice FAISS
        self.index = faiss.read_index(os.path.join(index_path, "index.faiss"))
        
        # Carrega conceitos
        self.concepts_df = pd.read_csv(os.path.join(index_path, "concepts.csv"))
            
        print(f"✅ Índice carregado: {len(self.concepts_df)} conceitos")
        return True
        
    def search_with_translation(self, query: str, specialty: str = None, top_k: int = 10) -> List[Dict]:
        """
        Busca conceitos SNOMED usando PubMedBERT com tradução na GPU
        
        Args:
            query: Query em português
            specialty: Especialidade médica
            top_k: Número de resultados
            
        Returns:
            Lista de conceitos SNOMED
        """
        if self.model is None or self.index is None:
            raise RuntimeError("Modelo ou índice não carregados")
            
        print(f"🔍 Buscando: '{query}' (especialidade: {specialty})")
        
        # 1. Traduz query para inglês
        translated_query = self.medical_translator.translate_text(query)
        print(f"🌐 Traduzido: '{translated_query}'")
        
        # 2. Gera embedding da query traduzida na GPU
        with torch.no_grad():
            query_embedding = self.model.encode([translated_query], convert_to_tensor=True, device=self.device)
            query_embedding = query_embedding.cpu().numpy()
            
        faiss.normalize_L2(query_embedding)
        
        # 3. Busca no índice
        scores, indices = self.index.search(query_embedding, top_k * 2)
        
        # 4. Filtra por especialidade se especificada
        if specialty and specialty != 'general':
            filtered_results = self._filter_by_specialty(indices[0], scores[0], specialty)
            if len(filtered_results) < top_k:
                filtered_results = list(zip(indices[0], scores[0]))
        else:
            filtered_results = list(zip(indices[0], scores[0]))
            
        # 5. Limita resultados
        filtered_results = filtered_results[:top_k]
        
        # 6. Formata resultados
        results = []
        for idx, score in filtered_results:
            concept = self.concepts_df.iloc[idx].to_dict()
            concept['similarity_score'] = float(score)
            concept['translated_query'] = translated_query
            concept['original_query'] = query
            concept['device_used'] = self.device
            results.append(concept)
            
        return results
        
    def build_gpu_index(self, snomed_data_path: str, output_path: str = "data/snomed_pubmedbert_gpu_index", 
                       sample_size: int = None, batch_size: int = 32):
        """
        Constrói índice PubMedBERT otimizado para GPU
        
        Args:
            snomed_data_path: Caminho para dados SNOMED CT
            output_path: Caminho para salvar o índice
            sample_size: Tamanho da amostra (None para todos)
            batch_size: Tamanho do lote para processamento
        """
        print("🔬 Construindo índice PubMedBERT otimizado para GPU...")
        print(f"🎯 Dispositivo: {self.device}")
        print(f"📊 Tamanho do lote: {batch_size}")
        
        # Carrega modelo
        self.load_model()
        
        # Carrega dados SNOMED
        concepts_df = self._load_snomed_data(snomed_data_path)
        
        # Filtra conceitos relevantes
        relevant_concepts = concepts_df[
            (concepts_df['active'] == 1) & 
            (concepts_df['definitionStatusId'] == 900000000000073002)  # Fully defined
        ].copy()
        
        # Aplica amostragem se especificado
        if sample_size and sample_size < len(relevant_concepts):
            print(f"📊 Amostrando {sample_size} conceitos de {len(relevant_concepts)}")
            relevant_concepts = relevant_concepts.sample(n=sample_size, random_state=42)
        
        print(f"📊 Conceitos para processar: {len(relevant_concepts)}")
        
        # Gera embeddings em lotes na GPU
        print("🔄 Gerando embeddings com PubMedBERT na GPU...")
        terms = relevant_concepts['term'].tolist()
        
        # Processa em lotes para otimizar memória
        embeddings_list = []
        total_batches = (len(terms) + batch_size - 1) // batch_size
        
        for i in range(0, len(terms), batch_size):
            batch_terms = terms[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            print(f"   📦 Processando lote {batch_num}/{total_batches} ({len(batch_terms)} termos)")
            
            with torch.no_grad():
                batch_embeddings = self.model.encode(
                    batch_terms, 
                    convert_to_tensor=True, 
                    device=self.device,
                    show_progress_bar=False
                )
                # Move para CPU para economizar memória GPU
                batch_embeddings = batch_embeddings.cpu().numpy()
                embeddings_list.append(batch_embeddings)
                
            # Limpa cache da GPU
            if self.device == "cuda":
                torch.cuda.empty_cache()
        
        # Concatena todos os embeddings
        embeddings = np.vstack(embeddings_list)
        print(f"✅ Embeddings gerados: {embeddings.shape}")
        
        # Normaliza embeddings
        faiss.normalize_L2(embeddings)
        
        # Cria índice FAISS
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner Product para similaridade de cosseno
        
        # Adiciona embeddings ao índice
        print("🔨 Construindo índice FAISS...")
        index.add(embeddings.astype('float32'))
        
        # Salva índice
        os.makedirs(output_path, exist_ok=True)
        faiss.write_index(index, os.path.join(output_path, "index.faiss"))
        relevant_concepts.to_csv(os.path.join(output_path, "concepts.csv"), index=False)
        
        # Salva metadados
        metadata = {
            "model_name": self.model_name,
            "device": self.device,
            "total_concepts": len(relevant_concepts),
            "embedding_dimension": dimension,
            "sample_size": sample_size
        }
        
        with open(os.path.join(output_path, "metadata.pkl"), 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"✅ Índice PubMedBERT GPU salvo em: {output_path}")
        print(f"📊 Conceitos processados: {len(relevant_concepts)}")
        print(f"🎯 Dispositivo usado: {self.device}")
        
    def _filter_by_specialty(self, indices: np.ndarray, scores: np.ndarray, specialty: str) -> List[Tuple]:
        """Filtra resultados por especialidade"""
        filtered = []
        for idx, score in zip(indices, scores):
            concept = self.concepts_df.iloc[idx]
            concept_specialty = self.medical_filters.detect_specialty(concept['term'])
            if concept_specialty == specialty:
                filtered.append((idx, score))
        return filtered
        
    def _load_snomed_data(self, snomed_data_path: str) -> pd.DataFrame:
        """Carrega dados SNOMED CT"""
        print("📂 Carregando dados SNOMED CT...")
        
        # Carrega conceitos
        concepts_file = os.path.join(snomed_data_path, "Snapshot", "Terminology", "sct2_Concept_Snapshot_INT_20250801.txt")
        concepts_df = pd.read_csv(concepts_file, sep='\t', low_memory=False)
        
        # Carrega descrições
        descriptions_file = os.path.join(snomed_data_path, "Snapshot", "Terminology", "sct2_Description_Snapshot-en_INT_20250801.txt")
        descriptions_df = pd.read_csv(descriptions_file, sep='\t', low_memory=False)
        
        # Filtra descrições ativas em inglês
        descriptions_df = descriptions_df[
            (descriptions_df['active'] == 1) & 
            (descriptions_df['languageCode'] == 'en')
        ]
        
        # Merge conceitos com descrições
        merged_df = concepts_df.merge(
            descriptions_df[['conceptId', 'term']], 
            left_on='id', 
            right_on='conceptId', 
            how='inner'
        )
        
        print(f"📊 Carregados {len(merged_df)} conceitos SNOMED")
        return merged_df
        
    def get_gpu_info(self) -> Dict:
        """Retorna informações da GPU"""
        if self.device == "cuda" and torch.cuda.is_available():
            return {
                "device": self.device,
                "gpu_name": torch.cuda.get_device_name(0),
                "memory_allocated": torch.cuda.memory_allocated(0) / 1024**3,  # GB
                "memory_reserved": torch.cuda.memory_reserved(0) / 1024**3,    # GB
                "memory_total": torch.cuda.get_device_properties(0).total_memory / 1024**3  # GB
            }
        else:
            return {"device": self.device, "gpu_available": False}
