# -*- coding: utf-8 -*-
"""
Sistema Híbrido Melhorado - P0 Hotfix
Implementa geração híbrida de candidatos + re-rank calibrado
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import time

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.clinical_translator_phrase_first import ClinicalTranslatorPhraseFirst
from src.core.cached_pubmedbert_search import CachedPubMedBERTSearch
from sentence_transformers import SentenceTransformer
import faiss

class HybridSearchImproved:
    """Sistema híbrido melhorado com geração de candidatos e re-rank calibrado"""
    
    def __init__(self, 
                 cache_size: int = 1000,
                 dict_path: str = "data/dicts/pt_aliases.json"):
        """Inicializa o sistema híbrido melhorado"""
        self.cache_size = cache_size
        self.dict_path = dict_path
        
        # Componentes
        self.translator = ClinicalTranslatorPhraseFirst(dict_path)
        self.pubmedbert_search = None
        self.sapbert_model = None
        self.faiss_index = None
        self.bm25_index = None
        
        # Cache de resultados
        self.search_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Estatísticas
        self.search_stats = defaultdict(int)
        
        print("🔬 Sistema Híbrido Melhorado inicializado")
        print(f"   📚 Cache: {cache_size} entradas")
        print(f"   🔤 Dicionário: {dict_path}")
    
    def load_models(self):
        """Carrega todos os modelos necessários"""
        print("🔄 Carregando modelos...")
        
        # Carrega PubMedBERT
        print("   📊 Carregando PubMedBERT...")
        self.pubmedbert_search = CachedPubMedBERTSearch(cache_size=self.cache_size)
        self.pubmedbert_search.load_model()
        self.pubmedbert_search.load_index("data/final_indices/snomed_pubmedbert_index")
        
        # Carrega SapBERT para aliases
        print("   🔬 Carregando SapBERT...")
        self.sapbert_model = SentenceTransformer("NeuML/pubmedbert-base-embeddings")
        
        # Carrega índice FAISS
        print("   🗂️ Carregando índice FAISS...")
        self.faiss_index = faiss.read_index("data/final_indices/snomed_pubmedbert_index/index.faiss")
        
        # Carrega índice BM25
        print("   📚 Carregando índice BM25...")
        self._load_bm25_index()
        
        print("✅ Todos os modelos carregados!")
    
    def _load_bm25_index(self):
        """Carrega índice BM25 com campo rico"""
        try:
            # Tenta carregar do índice existente primeiro
            concepts_path = "data/final_indices/snomed_pubmedbert_index/concepts.csv"
            if os.path.exists(concepts_path):
                print("   📖 Carregando índice BM25 do cache...")
                concepts_df = pd.read_csv(concepts_path)
                self.bm25_index = self._build_simple_bm25_index(concepts_df)
                print(f"   ✅ Índice BM25 criado com {len(self.bm25_index)} conceitos")
                return
            
            # Fallback para dados SNOMED originais
            descriptions_path = "SnomedCT_InternationalRF2_PRODUCTION_20250801T120000Z/Snapshot/Terminology/sct2_Description_Snapshot-en_INT_20250801.txt"
            concepts_path = "SnomedCT_InternationalRF2_PRODUCTION_20250801T120000Z/Snapshot/Terminology/sct2_Concept_Snapshot_INT_20250801.txt"
            
            if os.path.exists(descriptions_path) and os.path.exists(concepts_path):
                print("   📖 Carregando dados SNOMED para BM25...")
                
                # Carrega conceitos ativos
                concepts = pd.read_csv(concepts_path, sep='\t', low_memory=False)
                active_concepts = concepts[concepts['active'] == 1]
                
                # Carrega descrições ativas
                descriptions = pd.read_csv(descriptions_path, sep='\t', low_memory=False)
                active_descriptions = descriptions[descriptions['active'] == 1]
                
                # Cria índice BM25 rico
                self.bm25_index = self._build_rich_bm25_index(active_concepts, active_descriptions)
                print(f"   ✅ Índice BM25 criado com {len(self.bm25_index)} conceitos")
            else:
                print("   ⚠️ Arquivos SNOMED não encontrados, usando índice vazio")
                self.bm25_index = {}
                
        except Exception as e:
            print(f"   ⚠️ Erro ao carregar BM25: {e}")
            self.bm25_index = {}
    
    def _build_rich_bm25_index(self, concepts: pd.DataFrame, descriptions: pd.DataFrame) -> Dict[str, Any]:
        """Constrói índice BM25 rico com aliases PT"""
        print("   🔨 Construindo índice BM25 rico...")
        
        # Agrupa descrições por conceito
        concept_descriptions = descriptions.groupby('conceptId').agg({
            'term': lambda x: ' | '.join(str(item) for item in x.unique() if pd.notna(item)),
            'typeId': lambda x: list(x.unique())
        }).reset_index()
        
        # Merge com conceitos
        rich_index = concepts.merge(concept_descriptions, on='conceptId', how='left')
        
        # Cria campo rico para cada conceito
        bm25_docs = {}
        for _, row in rich_index.iterrows():
            concept_id = row['conceptId']
            preferred_term = row.get('term', '')
            semantic_tag = row.get('semanticTag', '')
            
            # Constrói campo rico: preferredTerm | synonyms | definition | semanticTag
            rich_text = f"{preferred_term} | {semantic_tag}"
            
            # Adiciona aliases PT se disponíveis
            pt_aliases = self._get_pt_aliases_for_concept(preferred_term)
            if pt_aliases:
                rich_text += f" | {pt_aliases}"
            
            bm25_docs[concept_id] = {
                'text': rich_text,
                'preferred_term': preferred_term,
                'semantic_tag': semantic_tag,
                'concept_id': concept_id
            }
        
        return bm25_docs
    
    def _build_simple_bm25_index(self, concepts_df: pd.DataFrame) -> Dict[str, Any]:
        """Constrói índice BM25 simples a partir do CSV de conceitos"""
        print("   🔨 Construindo índice BM25 simples...")
        
        bm25_docs = {}
        for idx, row in concepts_df.iterrows():
            concept_id = row.get('concept_id', idx)
            term = row.get('term', '')
            semantic_tag = row.get('semantic_tag', '')
            
            # Constrói campo rico: term | semantic_tag | aliases PT
            rich_text = f"{term} | {semantic_tag}"
            
            # Adiciona aliases PT se disponíveis
            pt_aliases = self._get_pt_aliases_for_concept(term)
            if pt_aliases:
                rich_text += f" | {pt_aliases}"
            
            bm25_docs[concept_id] = {
                'text': rich_text,
                'preferred_term': term,
                'semantic_tag': semantic_tag,
                'concept_id': concept_id
            }
        
        return bm25_docs
    
    def _get_pt_aliases_for_concept(self, en_term: str) -> str:
        """Encontra aliases PT para um termo EN"""
        pt_aliases = []
        en_term_lower = en_term.lower()
        
        # Busca no dicionário reverso
        for pt_term, en_translation in self.translator.medical_dict.items():
            if en_translation.lower() in en_term_lower or en_term_lower in en_translation.lower():
                pt_aliases.append(pt_term)
        
        return ' | '.join(pt_aliases) if pt_aliases else ''
    
    def _get_term_by_index(self, idx: int) -> str:
        """Busca o termo correspondente ao índice"""
        try:
            # Carrega o arquivo de conceitos se não estiver carregado
            if not hasattr(self, '_concepts_df'):
                concepts_path = "data/final_indices/snomed_pubmedbert_index/concepts.csv"
                if os.path.exists(concepts_path):
                    self._concepts_df = pd.read_csv(concepts_path)
                else:
                    return f"concept_{idx}"
            
            # Busca o termo pelo índice
            if idx < len(self._concepts_df):
                return self._concepts_df.iloc[idx].get('term', f"concept_{idx}")
            else:
                return f"concept_{idx}"
                
        except Exception as e:
            print(f"   ⚠️ Erro ao buscar termo para índice {idx}: {e}")
            return f"concept_{idx}"
    
    def _bm25_search(self, query: str, top_k: int = 200) -> List[Dict[str, Any]]:
        """Busca BM25 no índice rico"""
        if not self.bm25_index:
            return []
        
        query_lower = query.lower()
        results = []
        
        for concept_id, doc in self.bm25_index.items():
            text = doc['text'].lower()
            
            # Calcula score BM25 simples (frequência de termos)
            query_terms = query_lower.split()
            text_terms = text.split()
            
            score = 0
            for term in query_terms:
                term_count = text_terms.count(term)
                if term_count > 0:
                    # Score BM25 melhorado para termos médicos
                    tf = term_count
                    doc_len = len(text_terms)
                    
                    # IDF baseado na frequência do termo no corpus
                    idf = 1.0
                    if term in ['pain', 'blood', 'pressure', 'acute', 'chronic', 'disease', 'disorder']:
                        idf = 1.5  # Boost para termos médicos comuns
                    elif term in ['glucose', 'hypertension', 'infarction', 'stroke', 'cancer']:
                        idf = 2.0  # Boost para termos médicos específicos
                    
                    # Score BM25 com boost para termos médicos
                    bm25_score = (tf * idf) / (tf + 1.2 * (0.25 + 0.75 * doc_len / 100))
                    
                    # Boost adicional para correspondências exatas
                    if term in text:
                        bm25_score *= 1.2
                    
                    # Boost para termos no início do documento
                    if text.startswith(term):
                        bm25_score *= 1.1
                    
                    score += bm25_score
            
            if score > 0:
                results.append({
                    'concept_id': concept_id,
                    'term': doc['preferred_term'],
                    'score': score,
                    'text': doc['text'],
                    'semantic_tag': doc['semantic_tag'],
                    'method': 'bm25'
                })
        
        # Ordena por score e retorna top-k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def _sapbert_search(self, query: str, top_k: int = 100) -> List[Dict[str, Any]]:
        """Busca SapBERT para aliases"""
        if not self.sapbert_model or not self.faiss_index:
            return []
        
        try:
            # Gera embedding da query
            query_embedding = self.sapbert_model.encode([query])
            
            # Busca no índice FAISS
            scores, indices = self.faiss_index.search(query_embedding, top_k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx != -1:  # Índice válido
                    # Busca o termo correspondente no índice
                    term = self._get_term_by_index(idx)
                    results.append({
                        'concept_id': str(idx),
                        'term': term,
                        'score': float(score),
                        'method': 'sapbert'
                    })
            
            return results
            
        except Exception as e:
            print(f"   ⚠️ Erro na busca SapBERT: {e}")
            return []
    
    def _faiss_search(self, query: str, top_k: int = 200) -> List[Dict[str, Any]]:
        """Busca FAISS PubMedBERT"""
        if not self.faiss_index:
            return []
        
        try:
            # Usa o modelo PubMedBERT para gerar embedding
            query_embedding = self.pubmedbert_search.gpu_search.model.encode([query])
            
            # Busca no índice FAISS
            scores, indices = self.faiss_index.search(query_embedding, top_k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx != -1:  # Índice válido
                    # Busca o termo correspondente no índice
                    term = self._get_term_by_index(idx)
                    results.append({
                        'concept_id': str(idx),
                        'term': term,
                        'score': float(score),
                        'method': 'faiss_pubmedbert'
                    })
            
            return results
            
        except Exception as e:
            print(f"   ⚠️ Erro na busca FAISS: {e}")
            return []
    
    def _dedupe_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicatas dos candidatos"""
        seen = set()
        deduped = []
        
        for candidate in candidates:
            concept_id = candidate.get('concept_id')
            if concept_id not in seen:
                seen.add(concept_id)
                deduped.append(candidate)
        
        return deduped
    
    def _z_score_normalize(self, scores: List[float]) -> List[float]:
        """Normaliza scores usando z-score"""
        if not scores:
            return []
        
        scores_array = np.array(scores, dtype=float)
        mean = np.mean(scores_array)
        std = np.std(scores_array)
        
        if std == 0:
            return [0.0] * len(scores)
        
        return ((scores_array - mean) / std).tolist()
    
    def _calculate_rule_bonus(self, query: str, result: Dict[str, Any]) -> float:
        """Calcula bônus baseado em regras clínicas melhoradas"""
        bonus = 0.0
        query_lower = query.lower()
        result_text = result.get('term', '').lower()
        semantic_tag = result.get('semantic_tag', '').lower()
        
        # Bônus para correspondência exata de termos médicos
        medical_terms = ['glucose', 'blood', 'pressure', 'pain', 'acute', 'chronic', 'disease', 'disorder', 'syndrome']
        for term in medical_terms:
            if term in query_lower and term in result_text:
                bonus += 0.05
        
        # Bônus para finding/disorder compatível
        if any(term in query_lower for term in ['dor', 'pain', 'sintoma', 'symptom', 'ache']):
            if any(term in result_text for term in ['pain', 'disorder', 'finding', 'symptom', 'ache', 'syndrome']):
                bonus += 0.04
        
        # Bônus para termos cardiovasculares
        if any(term in query_lower for term in ['pressão', 'pressure', 'hipertensão', 'hypertension', 'cardíaco', 'cardiac']):
            if any(term in result_text for term in ['blood pressure', 'hypertension', 'cardiac', 'heart', 'vascular', 'arterial']):
                bonus += 0.06
        
        # Bônus para termos respiratórios
        if any(term in query_lower for term in ['respiratório', 'respiratory', 'pulmonar', 'pulmonary', 'ar', 'breath']):
            if any(term in result_text for term in ['respiratory', 'pulmonary', 'lung', 'breathing', 'airway', 'obstructive']):
                bonus += 0.06
        
        # Bônus para terms digestivos
        if any(term in query_lower for term in ['digestivo', 'digestive', 'gástrico', 'gastric', 'úlcera', 'ulcer']):
            if any(term in result_text for term in ['digestive', 'gastric', 'ulcer', 'gastrointestinal', 'stomach', 'duodenal']):
                bonus += 0.06
        
        # Bônus para terms neurológicos
        if any(term in query_lower for term in ['neurológico', 'neurological', 'cerebral', 'avc', 'stroke']):
            if any(term in result_text for term in ['neurological', 'cerebral', 'stroke', 'cerebrovascular', 'brain']):
                bonus += 0.06
        
        # Bônus para specificity alta
        if len(result_text.split()) > 3:  # Termos mais específicos
            bonus += 0.03
        
        # Bônus para termos com alta especificidade médica
        if any(term in result_text for term in ['disorder', 'disease', 'syndrome', 'condition', 'finding']):
            bonus += 0.02
        
        # Bônus para correspondência de especialidade
        if 'cardiology' in semantic_tag and any(term in query_lower for term in ['cardíaco', 'heart', 'pressão', 'pressure']):
            bonus += 0.04
        elif 'pulmonology' in semantic_tag and any(term in query_lower for term in ['respiratório', 'respiratory', 'pulmonar', 'pulmonary']):
            bonus += 0.04
        elif 'gastroenterology' in semantic_tag and any(term in query_lower for term in ['digestivo', 'digestive', 'gástrico', 'gastric']):
            bonus += 0.04
        
        # Penalidade para incompatibilidade (simplificada)
        if 'pediatric' in semantic_tag and 'adult' in query_lower:
            bonus -= 0.03
        
        return min(bonus, 0.15)  # Limita o bônus máximo
    
    def search_hybrid(self, query: str, top_k: int = 5, specialty: Optional[str] = None) -> Dict[str, Any]:
        """Busca híbrida com geração de candidatos e re-rank calibrado"""
        start_time = time.time()
        
        # Verifica cache
        cache_key = f"{query}_{top_k}_{specialty}"
        if cache_key in self.search_cache:
            self.cache_hits += 1
            return self.search_cache[cache_key]
        
        self.cache_misses += 1
        
        # 1. Tradução phrase-first
        translation_result = self.translator.translate_phrase_first(query)
        translated_query = translation_result['translated']
        
        print(f"🔍 Busca híbrida: '{query}' → '{translated_query}'")
        
        # 2. Geração de candidatos híbrida
        print("   📊 Gerando candidatos...")
        
        # BM25 (campo rico)
        bm25_results = self._bm25_search(translated_query, top_k=200)
        print(f"      BM25: {len(bm25_results)} candidatos")
        
        # SapBERT kNN
        sapbert_results = self._sapbert_search(translated_query, top_k=100)
        print(f"      SapBERT: {len(sapbert_results)} candidatos")
        
        # FAISS PubMedBERT
        faiss_results = self._faiss_search(translated_query, top_k=200)
        print(f"      FAISS: {len(faiss_results)} candidatos")
        
        # 3. União e deduplicação
        all_candidates = bm25_results + sapbert_results + faiss_results
        candidates = self._dedupe_candidates(all_candidates)
        candidates = candidates[:300]  # Limita a 300 candidatos
        
        print(f"      Total após dedupe: {len(candidates)} candidatos")
        
        # 4. Re-rank calibrado
        print("   🎯 Re-ranking calibrado...")
        
        # Extrai scores por fonte
        bm25_scores = [c.get('score', 0.0) for c in candidates if c.get('method') == 'bm25']
        sapbert_scores = [c.get('score', 0.0) for c in candidates if c.get('method') == 'sapbert']
        faiss_scores = [c.get('score', 0.0) for c in candidates if c.get('method') == 'faiss_pubmedbert']
        
        # Normaliza scores
        bm25_z = self._z_score_normalize(bm25_scores) if bm25_scores else [0.0] * len(candidates)
        sapbert_z = self._z_score_normalize(sapbert_scores) if sapbert_scores else [0.0] * len(candidates)
        faiss_z = self._z_score_normalize(faiss_scores) if faiss_scores else [0.0] * len(candidates)
        
        # Calcula score final calibrado
        final_results = []
        for i, candidate in enumerate(candidates):
            # Scores normalizados baseados no método
            method = candidate.get('method', 'unknown')
            if method == 'bm25':
                bm25_score = bm25_z[min(i, len(bm25_z)-1)] if bm25_z else 0.0
                sapbert_score = 0.0
                faiss_score = 0.0
            elif method == 'sapbert':
                bm25_score = 0.0
                sapbert_score = sapbert_z[min(i, len(sapbert_z)-1)] if sapbert_z else 0.0
                faiss_score = 0.0
            elif method == 'faiss_pubmedbert':
                bm25_score = 0.0
                sapbert_score = 0.0
                faiss_score = faiss_z[min(i, len(faiss_z)-1)] if faiss_z else 0.0
            else:
                bm25_score = 0.0
                sapbert_score = 0.0
                faiss_score = 0.0
            
            # Score final calibrado
            final_score = (
                0.45 * faiss_score +      # PubMedBERT (principal)
                0.20 * bm25_score +       # BM25
                0.10 * sapbert_score +    # SapBERT
                0.05 * self._calculate_rule_bonus(query, candidate)  # Regras clínicas
            )
            
            final_results.append({
                'concept_id': candidate.get('concept_id'),
                'term': candidate.get('term', ''),
                'similarity_score': final_score,
                'method': candidate.get('method', 'hybrid'),
                'bm25_score': bm25_score,
                'sapbert_score': sapbert_score,
                'faiss_score': faiss_score,
                'rule_bonus': self._calculate_rule_bonus(query, candidate)
            })
        
        # Ordena por score final
        final_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Retorna top-k
        top_results = final_results[:top_k]
        
        search_time = time.time() - start_time
        
        # Prepara resultado
        result = {
            'query': query,
            'translated_query': translated_query,
            'translation_confidence': translation_result['confidence'],
            'results': top_results,
            'total_candidates': len(candidates),
            'search_time': search_time,
            'method': 'hybrid_improved',
            'cache_hit': False
        }
        
        # Salva no cache
        self.search_cache[cache_key] = result
        
        # Atualiza estatísticas
        self.search_stats['total_searches'] += 1
        self.search_stats['avg_search_time'] = (
            (self.search_stats['avg_search_time'] * (self.search_stats['total_searches'] - 1) + search_time) 
            / self.search_stats['total_searches']
        )
        
        print(f"   ✅ Busca concluída em {search_time:.3f}s")
        print(f"   📊 Resultados: {len(top_results)}")
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do sistema"""
        return {
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0,
            'search_stats': dict(self.search_stats),
            'translation_stats': self.translator.get_translation_stats()
        }

def test_hybrid_search_improved():
    """Testa o sistema híbrido melhorado"""
    print("🧪 TESTE DO SISTEMA HÍBRIDO MELHORADO")
    print("=" * 60)
    
    # Inicializa sistema
    hybrid_search = HybridSearchImproved()
    hybrid_search.load_models()
    
    # Testa com termos problemáticos identificados
    test_queries = [
        "dor no peito",
        "falta de ar",
        "glicemia alta",
        "hipertensão arterial",
        "úlcera duodenal",
        "hemorragia digestiva",
        "avc isquêmico",
        "paresia do braço",
        "hiv positivo",
        "câncer de pulmão"
    ]
    
    print(f"\n🔍 Testando {len(test_queries)} consultas...")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i:2d}. '{query}'")
        
        result = hybrid_search.search_hybrid(query, top_k=3)
        
        print(f"    Traduzido: '{result['translated_query']}'")
        print(f"    Confiança tradução: {result['translation_confidence']:.3f}")
        print(f"    Candidatos: {result['total_candidates']}")
        print(f"    Tempo: {result['search_time']:.3f}s")
        
        print(f"    Top 3 resultados:")
        for j, res in enumerate(result['results'][:3], 1):
            print(f"      {j}. {res['term']} (score: {res['similarity_score']:.3f})")
            print(f"         Método: {res['method']}, BM25: {res['bm25_score']:.3f}, FAISS: {res['faiss_score']:.3f}")
    
    # Estatísticas finais
    stats = hybrid_search.get_stats()
    print(f"\n📊 ESTATÍSTICAS FINAIS:")
    print(f"   Cache hit rate: {stats['cache_hit_rate']:.1%}")
    print(f"   Buscas totais: {stats['search_stats']['total_searches']}")
    print(f"   Tempo médio: {stats['search_stats']['avg_search_time']:.3f}s")
    print(f"   Traduções: {stats['translation_stats']['total_translations']}")

if __name__ == "__main__":
    test_hybrid_search_improved()
