"""
Sistema Híbrido em Duas Camadas para Qualidade ≥8/10
Camada 1: Recall (BM25 + SapBERT + PubMedBERT)
Camada 2: Precisão (Cross-encoder + Heurísticas clínicas)
"""

import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer
from sentence_transformers.cross_encoder import CrossEncoder
import faiss
from typing import List, Dict, Tuple, Optional
import os
import json
from collections import defaultdict
import re

from .config import EMBEDDING_MODEL
from .medical_translator import MedicalTranslator
from .medical_filters import MedicalFilters

class HybridTwoLayerSearch:
    """Sistema híbrido em duas camadas para máxima qualidade"""
    
    def __init__(self, device: str = None):
        """
        Inicializa sistema híbrido
        
        Args:
            device: Dispositivo para processamento
        """
        self.device = device or self._get_best_device()
        
        # Modelos
        self.pubmedbert_model = None
        self.sapbert_model = None
        self.cross_encoder = None
        
        # Índices
        self.bm25_index = None
        self.sapbert_index = None
        self.pubmedbert_index = None
        
        # Dados
        self.concepts_df = None
        self.vocabulary = None
        
        # Configurações
        self.recall_config = {
            "bm25_top_k": 200,
            "sapbert_top_k": 100,
            "pubmedbert_top_k": 200,
            "max_candidates": 300
        }
        
        self.precision_config = {
            "cross_encoder_weight": 0.20,
            "pubmedbert_weight": 0.45,
            "bm25_weight": 0.20,
            "sapbert_weight": 0.10,
            "rule_bonus_weight": 0.05
        }
        
        # Tradutor e filtros
        self.translator = MedicalTranslator()
        self.medical_filters = MedicalFilters()
        
        print(f"🚀 Sistema Híbrido em Duas Camadas Inicializado")
        print(f"🎯 Dispositivo: {self.device}")
        
    def _get_best_device(self) -> str:
        """Detecta melhor dispositivo"""
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"
        
    def load_models(self):
        """Carrega todos os modelos necessários"""
        print("📥 Carregando modelos...")
        
        # PubMedBERT para embeddings
        print("   🔬 Carregando PubMedBERT...")
        self.pubmedbert_model = SentenceTransformer(EMBEDDING_MODEL)
        if self.device == "cuda":
            self.pubmedbert_model = self.pubmedbert_model.to(self.device)
            
        # SapBERT para sinônimos/aliases (usando PubMedBERT disponível)
        print("   🔬 Carregando SapBERT...")
        self.sapbert_model = SentenceTransformer("NeuML/pubmedbert-base-embeddings")
        if self.device == "cuda":
            self.sapbert_model = self.sapbert_model.to(self.device)
            
        # Cross-encoder biomédico
        print("   🔬 Carregando Cross-encoder...")
        self.cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-12-v2")
        if self.device == "cuda":
            self.cross_encoder = self.cross_encoder.to(self.device)
            
        print("✅ Todos os modelos carregados!")
        
    def build_rich_snomed_index(self, snomed_data_path: str, output_path: str = "data/indices/rich_snomed_index"):
        """Constrói índice SNOMED rico com múltiplos campos"""
        print("🔨 Construindo índice SNOMED rico...")
        
        # Carrega dados SNOMED
        concepts_file = os.path.join(snomed_data_path, "Snapshot", "Terminology", "sct2_Concept_Snapshot_INT_20250801.txt")
        descriptions_file = os.path.join(snomed_data_path, "Snapshot", "Terminology", "sct2_Description_Snapshot-en_INT_20250801.txt")
        relationships_file = os.path.join(snomed_data_path, "Snapshot", "Terminology", "sct2_Relationship_Snapshot_INT_20250801.txt")
        
        # Carrega conceitos
        concepts_df = pd.read_csv(concepts_file, sep='\t', low_memory=False)
        descriptions_df = pd.read_csv(descriptions_file, sep='\t', low_memory=False)
        relationships_df = pd.read_csv(relationships_file, sep='\t', low_memory=False)
        
        # Filtra conceitos ativos e totalmente definidos
        active_concepts = concepts_df[
            (concepts_df['active'] == 1) & 
            (concepts_df['definitionStatusId'] == 900000000000073002)
        ]
        
        # Filtra descrições ativas em inglês
        active_descriptions = descriptions_df[
            (descriptions_df['active'] == 1) & 
            (descriptions_df['languageCode'] == 'en')
        ]
        
        # Agrupa descrições por conceito
        concept_descriptions = active_descriptions.groupby('conceptId').agg({
            'term': lambda x: ' | '.join(str(item) for item in x.unique() if pd.notna(item)),
            'typeId': lambda x: list(x.unique())
        }).reset_index()
        
        # Merge conceitos com descrições
        rich_concepts = active_concepts.merge(
            concept_descriptions, 
            left_on='id', 
            right_on='conceptId', 
            how='inner'
        )
        
        # Adiciona informações de relacionamentos (pais)
        parent_relationships = relationships_df[
            (relationships_df['active'] == 1) & 
            (relationships_df['typeId'] == 116680003)  # IS-A relationship
        ]
        
        # Constrói texto rico para cada conceito
        print("📝 Construindo textos ricos...")
        rich_texts = []
        
        for _, concept in rich_concepts.iterrows():
            # Texto base
            preferred_term = concept['term']
            
            # Adiciona sinônimos
            synonyms = concept['term'].split(' | ')
            synonyms_text = ' '.join(synonyms[1:]) if len(synonyms) > 1 else ''
            
            # Adiciona tipo semântico
            semantic_tag = concept.get('semanticTag', '')
            
            # Adiciona pais (2 níveis)
            concept_id = concept['id']
            parents = parent_relationships[parent_relationships['sourceId'] == concept_id]
            parent_terms = []
            for _, parent in parents.head(2).iterrows():
                parent_desc = active_descriptions[active_descriptions['conceptId'] == parent['destinationId']]
                if not parent_desc.empty:
                    parent_terms.append(parent_desc.iloc[0]['term'])
            parents_text = ' '.join(parent_terms)
            
            # Constrói texto rico
            rich_text = f"{preferred_term} {synonyms_text} {semantic_tag} {parents_text}".strip()
            
            rich_texts.append({
                'conceptId': concept_id,
                'preferredTerm': preferred_term,
                'synonyms': synonyms_text,
                'semanticTag': semantic_tag,
                'parents': parents_text,
                'richText': rich_text,
                'typeId': concept['typeId'],
                'definitionStatusId': concept['definitionStatusId']
            })
        
        # Converte para DataFrame
        rich_df = pd.DataFrame(rich_texts)
        
        # Salva índice rico
        os.makedirs(output_path, exist_ok=True)
        rich_df.to_csv(os.path.join(output_path, "rich_concepts.csv"), index=False)
        
        print(f"✅ Índice rico construído: {len(rich_df)} conceitos")
        print(f"💾 Salvo em: {output_path}")
        
        return rich_df
        
    def build_hybrid_indices(self, rich_concepts_df: pd.DataFrame, output_path: str = "data/indices/hybrid_indices"):
        """Constrói índices híbridos (BM25, SapBERT, PubMedBERT)"""
        print("🔨 Construindo índices híbridos...")
        
        os.makedirs(output_path, exist_ok=True)
        
        # 1. BM25 Index (simulado com TF-IDF)
        print("   📊 Construindo índice BM25...")
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 2),
            stop_words='english'
        )
        
        # Treina BM25
        bm25_matrix = vectorizer.fit_transform(rich_concepts_df['richText'])
        
        # Salva BM25
        import pickle
        with open(os.path.join(output_path, "bm25_vectorizer.pkl"), 'wb') as f:
            pickle.dump(vectorizer, f)
        np.save(os.path.join(output_path, "bm25_matrix.npy"), bm25_matrix.toarray())
        
        # 2. SapBERT Index
        print("   🔬 Construindo índice SapBERT...")
        if self.sapbert_model is None:
            self.load_models()
            
        sapbert_embeddings = self.sapbert_model.encode(
            rich_concepts_df['richText'].tolist(),
            convert_to_tensor=True,
            device=self.device,
            show_progress_bar=True
        )
        
        # Normaliza embeddings
        sapbert_embeddings = torch.nn.functional.normalize(sapbert_embeddings, p=2, dim=1)
        
        # Cria índice FAISS para SapBERT
        sapbert_index = faiss.IndexFlatIP(sapbert_embeddings.shape[1])
        sapbert_index.add(sapbert_embeddings.cpu().numpy().astype('float32'))
        faiss.write_index(sapbert_index, os.path.join(output_path, "sapbert_index.faiss"))
        
        # 3. PubMedBERT Index
        print("   🔬 Construindo índice PubMedBERT...")
        pubmedbert_embeddings = self.pubmedbert_model.encode(
            rich_concepts_df['richText'].tolist(),
            convert_to_tensor=True,
            device=self.device,
            show_progress_bar=True
        )
        
        # Normaliza embeddings
        pubmedbert_embeddings = torch.nn.functional.normalize(pubmedbert_embeddings, p=2, dim=1)
        
        # Cria índice FAISS para PubMedBERT
        pubmedbert_index = faiss.IndexFlatIP(pubmedbert_embeddings.shape[1])
        pubmedbert_index.add(pubmedbert_embeddings.cpu().numpy().astype('float32'))
        faiss.write_index(pubmedbert_index, os.path.join(output_path, "pubmedbert_index.faiss"))
        
        # Salva conceitos
        rich_concepts_df.to_csv(os.path.join(output_path, "concepts.csv"), index=False)
        
        print("✅ Índices híbridos construídos!")
        
        return {
            "bm25_vectorizer": vectorizer,
            "bm25_matrix": bm25_matrix,
            "sapbert_index": sapbert_index,
            "pubmedbert_index": pubmedbert_index,
            "concepts_df": rich_concepts_df
        }
        
    def load_hybrid_indices(self, indices_path: str = "data/indices/hybrid_indices"):
        """Carrega índices híbridos"""
        print("📂 Carregando índices híbridos...")
        
        # Carrega BM25
        import pickle
        with open(os.path.join(indices_path, "bm25_vectorizer.pkl"), 'rb') as f:
            self.bm25_vectorizer = pickle.load(f)
        self.bm25_matrix = np.load(os.path.join(indices_path, "bm25_matrix.npy"))
        
        # Carrega SapBERT
        self.sapbert_index = faiss.read_index(os.path.join(indices_path, "sapbert_index.faiss"))
        
        # Carrega PubMedBERT
        self.pubmedbert_index = faiss.read_index(os.path.join(indices_path, "pubmedbert_index.faiss"))
        
        # Carrega conceitos
        self.concepts_df = pd.read_csv(os.path.join(indices_path, "concepts.csv"))
        
        print("✅ Índices híbridos carregados!")
        
    def layer1_recall(self, query: str, specialty: str = None) -> List[Dict]:
        """
        Camada 1: Geração de candidatos (recall alto)
        
        Args:
            query: Query de busca
            specialty: Especialidade médica
            
        Returns:
            Lista de candidatos com scores
        """
        print(f"🔍 Camada 1 - Recall: '{query}'")
        
        # Traduz query para inglês
        translated_query = self.translator.translate_text(query)
        print(f"   🌐 Traduzido: '{translated_query}'")
        
        candidates = []
        
        # 1. BM25 (preferredTerm | synonyms | definition | semanticTag)
        print("   📊 BM25...")
        bm25_scores = self._bm25_search(translated_query, self.recall_config["bm25_top_k"])
        candidates.extend(bm25_scores)
        
        # 2. SapBERT (sinônimos/aliases difíceis)
        print("   🔬 SapBERT...")
        sapbert_scores = self._sapbert_search(translated_query, self.recall_config["sapbert_top_k"])
        candidates.extend(sapbert_scores)
        
        # 3. PubMedBERT (semântica clínica)
        print("   🔬 PubMedBERT...")
        pubmedbert_scores = self._pubmedbert_search(translated_query, self.recall_config["pubmedbert_top_k"])
        candidates.extend(pubmedbert_scores)
        
        # União + dedupe
        print("   🔗 União e deduplicação...")
        unique_candidates = self._dedupe_candidates(candidates)
        
        # Limita candidatos
        top_candidates = unique_candidates[:self.recall_config["max_candidates"]]
        
        print(f"   ✅ {len(top_candidates)} candidatos gerados")
        return top_candidates
        
    def layer2_precision(self, query: str, candidates: List[Dict], specialty: str = None) -> List[Dict]:
        """
        Camada 2: Re-ranking (precisão)
        
        Args:
            query: Query de busca
            candidates: Candidatos da camada 1
            specialty: Especialidade médica
            
        Returns:
            Resultados re-ranqueados
        """
        print(f"🎯 Camada 2 - Precisão: {len(candidates)} candidatos")
        
        if not candidates:
            return []
            
        # Carrega modelos se necessário
        if self.pubmedbert_model is None:
            self.load_models()
            
        translated_query = self.translator.translate_text(query)
        
        # Calcula scores para cada candidato
        for candidate in candidates:
            concept_text = candidate['richText']
            
            # 1. PubMedBERT (cosine similarity)
            pubmedbert_score = self._calculate_pubmedbert_score(translated_query, concept_text)
            
            # 2. Cross-encoder
            cross_encoder_score = self._calculate_cross_encoder_score(translated_query, concept_text)
            
            # 3. BM25 score (já calculado)
            bm25_score = candidate.get('bm25_score', 0.0)
            
            # 4. SapBERT score (já calculado)
            sapbert_score = candidate.get('sapbert_score', 0.0)
            
            # 5. Heurísticas clínicas
            rule_bonus = self._calculate_clinical_rules(query, candidate, specialty)
            
            # Armazena scores
            candidate['pubmedbert_score'] = pubmedbert_score
            candidate['cross_encoder_score'] = cross_encoder_score
            candidate['rule_bonus'] = rule_bonus
            
        # Normaliza scores (z-score)
        print("   📊 Normalizando scores...")
        self._normalize_scores(candidates)
        
        # Combina scores
        print("   🧮 Combinando scores...")
        for candidate in candidates:
            final_score = (
                self.precision_config["pubmedbert_weight"] * candidate.get('pubmedbert_score_norm', 0) +
                self.precision_config["cross_encoder_weight"] * candidate.get('cross_encoder_score_norm', 0) +
                self.precision_config["bm25_weight"] * candidate.get('bm25_score_norm', 0) +
                self.precision_config["sapbert_weight"] * candidate.get('sapbert_score_norm', 0) +
                self.precision_config["rule_bonus_weight"] * candidate.get('rule_bonus', 0)
            )
            candidate['final_score'] = final_score
            
        # Ordena por score final
        candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        print(f"   ✅ Re-ranking concluído")
        return candidates
        
    def search(self, query: str, specialty: str = None, top_k: int = 10) -> List[Dict]:
        """
        Busca híbrida completa
        
        Args:
            query: Query de busca
            specialty: Especialidade médica
            top_k: Número de resultados
            
        Returns:
            Resultados finais
        """
        print(f"🔍 Busca Híbrida: '{query}' (especialidade: {specialty})")
        
        # Camada 1: Recall
        candidates = self.layer1_recall(query, specialty)
        
        # Camada 2: Precisão
        results = self.layer2_precision(query, candidates, specialty)
        
        # Retorna top-k
        final_results = results[:top_k]
        
        print(f"✅ {len(final_results)} resultados finais")
        return final_results
        
    def _bm25_search(self, query: str, top_k: int) -> List[Dict]:
        """Busca BM25"""
        query_vector = self.bm25_vectorizer.transform([query])
        scores = (query_vector * self.bm25_matrix.T).toarray().flatten()
        
        # Top-k scores
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                concept = self.concepts_df.iloc[idx]
                results.append({
                    'conceptId': concept['conceptId'],
                    'preferredTerm': concept['preferredTerm'],
                    'richText': concept['richText'],
                    'bm25_score': float(scores[idx]),
                    'source': 'bm25'
                })
                
        return results
        
    def _sapbert_search(self, query: str, top_k: int) -> List[Dict]:
        """Busca SapBERT"""
        query_embedding = self.sapbert_model.encode([query], convert_to_tensor=True, device=self.device)
        query_embedding = torch.nn.functional.normalize(query_embedding, p=2, dim=1)
        
        scores, indices = self.sapbert_index.search(query_embedding.cpu().numpy(), top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if score > 0:
                concept = self.concepts_df.iloc[idx]
                results.append({
                    'conceptId': concept['conceptId'],
                    'preferredTerm': concept['preferredTerm'],
                    'richText': concept['richText'],
                    'sapbert_score': float(score),
                    'source': 'sapbert'
                })
                
        return results
        
    def _pubmedbert_search(self, query: str, top_k: int) -> List[Dict]:
        """Busca PubMedBERT"""
        query_embedding = self.pubmedbert_model.encode([query], convert_to_tensor=True, device=self.device)
        query_embedding = torch.nn.functional.normalize(query_embedding, p=2, dim=1)
        
        scores, indices = self.pubmedbert_index.search(query_embedding.cpu().numpy(), top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if score > 0:
                concept = self.concepts_df.iloc[idx]
                results.append({
                    'conceptId': concept['conceptId'],
                    'preferredTerm': concept['preferredTerm'],
                    'richText': concept['richText'],
                    'pubmedbert_score': float(score),
                    'source': 'pubmedbert'
                })
                
        return results
        
    def _dedupe_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """Remove duplicatas dos candidatos"""
        seen = set()
        unique_candidates = []
        
        for candidate in candidates:
            concept_id = candidate['conceptId']
            if concept_id not in seen:
                seen.add(concept_id)
                unique_candidates.append(candidate)
                
        return unique_candidates
        
    def _calculate_pubmedbert_score(self, query: str, concept_text: str) -> float:
        """Calcula score PubMedBERT"""
        query_emb = self.pubmedbert_model.encode([query], convert_to_tensor=True, device=self.device)
        concept_emb = self.pubmedbert_model.encode([concept_text], convert_to_tensor=True, device=self.device)
        
        similarity = torch.cosine_similarity(query_emb, concept_emb).item()
        return similarity
        
    def _calculate_cross_encoder_score(self, query: str, concept_text: str) -> float:
        """Calcula score cross-encoder"""
        score = self.cross_encoder.predict([(query, concept_text)])[0]
        return float(score)
        
    def _calculate_clinical_rules(self, query: str, candidate: Dict, specialty: str) -> float:
        """Calcula bônus de regras clínicas"""
        bonus = 0.0
        
        # Specificity boost
        if len(candidate['preferredTerm'].split()) >= 3:
            bonus += 0.02
            
        # Semantic tag match
        semantic_tag = candidate.get('semanticTag', '')
        if specialty and specialty.lower() in semantic_tag.lower():
            bonus += 0.03
            
        # Finding/Disorder match
        if any(word in query.lower() for word in ['sintoma', 'symptom', 'dor', 'pain']):
            if 'finding' in semantic_tag.lower() or 'disorder' in semantic_tag.lower():
                bonus += 0.02
                
        return bonus
        
    def _normalize_scores(self, candidates: List[Dict]):
        """Normaliza scores usando z-score"""
        # PubMedBERT
        pubmedbert_scores = [c.get('pubmedbert_score', 0) for c in candidates]
        if pubmedbert_scores:
            mean_pb = np.mean(pubmedbert_scores)
            std_pb = np.std(pubmedbert_scores)
            for candidate in candidates:
                candidate['pubmedbert_score_norm'] = (candidate.get('pubmedbert_score', 0) - mean_pb) / max(std_pb, 1e-8)
                
        # Cross-encoder
        cross_scores = [c.get('cross_encoder_score', 0) for c in candidates]
        if cross_scores:
            mean_ce = np.mean(cross_scores)
            std_ce = np.std(cross_scores)
            for candidate in candidates:
                candidate['cross_encoder_score_norm'] = (candidate.get('cross_encoder_score', 0) - mean_ce) / max(std_ce, 1e-8)
                
        # BM25
        bm25_scores = [c.get('bm25_score', 0) for c in candidates]
        if bm25_scores:
            mean_bm25 = np.mean(bm25_scores)
            std_bm25 = np.std(bm25_scores)
            for candidate in candidates:
                candidate['bm25_score_norm'] = (candidate.get('bm25_score', 0) - mean_bm25) / max(std_bm25, 1e-8)
                
        # SapBERT
        sapbert_scores = [c.get('sapbert_score', 0) for c in candidates]
        if sapbert_scores:
            mean_sb = np.mean(sapbert_scores)
            std_sb = np.std(sapbert_scores)
            for candidate in candidates:
                candidate['sapbert_score_norm'] = (candidate.get('sapbert_score', 0) - mean_sb) / max(std_sb, 1e-8)
