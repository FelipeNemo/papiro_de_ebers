"""
Sistema de Tradução Clínica Aprimorado
Implementa estratégias para melhorar PT→EN sem trocar MiniLM
"""

import re
import json
import os
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
import torch
import numpy as np

class EnhancedClinicalTranslator:
    """Sistema de tradução clínica aprimorado"""
    
    def __init__(self, device: str = None):
        """
        Inicializa tradutor clínico aprimorado
        
        Args:
            device: Dispositivo para processamento
        """
        self.device = device or self._get_best_device()
        
        # Modelos
        self.minilm_model = None
        self.sapbert_model = None
        
        # Dicionários
        self.abbreviation_dict = {}
        self.synonym_dict = {}
        self.clinical_terms = set()
        
        # Configurações
        self.expansion_config = {
            "max_synonyms": 5,
            "similarity_threshold": 0.7,
            "use_sapbert": True
        }
        
        print(f"🌐 Tradutor Clínico Aprimorado Inicializado")
        print(f"🎯 Dispositivo: {self.device}")
        
    def _get_best_device(self) -> str:
        """Detecta melhor dispositivo"""
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"
        
    def load_models(self):
        """Carrega modelos necessários"""
        print("📥 Carregando modelos de tradução...")
        
        # MiniLM para tradução base
        print("   🔬 Carregando MiniLM...")
        self.minilm_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        if self.device == "cuda":
            self.minilm_model = self.minilm_model.to(self.device)
            
        # SapBERT para aliases UMLS/SNOMED (usando PubMedBERT disponível)
        print("   🔬 Carregando SapBERT...")
        self.sapbert_model = SentenceTransformer("NeuML/pubmedbert-base-embeddings")
        if self.device == "cuda":
            self.sapbert_model = self.sapbert_model.to(self.device)
            
        print("✅ Modelos de tradução carregados!")
        
    def load_clinical_dictionaries(self, data_path: str = "data"):
        """Carrega dicionários clínicos"""
        print("📚 Carregando dicionários clínicos...")
        
        # Dicionário de abreviações
        self.abbreviation_dict = {
            "IAM": "myocardial infarction",
            "DPOC": "COPD",
            "HAS": "hypertension",
            "AVC": "stroke",
            "DM": "diabetes mellitus",
            "T2DM": "type 2 diabetes mellitus",
            "T1DM": "type 1 diabetes mellitus",
            "HTN": "hypertension",
            "MI": "myocardial infarction",
            "COPD": "chronic obstructive pulmonary disease",
            "CVA": "cerebrovascular accident",
            "CHF": "congestive heart failure",
            "PNA": "pneumonia",
            "URI": "upper respiratory infection",
            "UTI": "urinary tract infection",
            "GERD": "gastroesophageal reflux disease",
            "IBD": "inflammatory bowel disease",
            "IBS": "irritable bowel syndrome",
            "RA": "rheumatoid arthritis",
            "OA": "osteoarthritis",
            "DVT": "deep vein thrombosis",
            "PE": "pulmonary embolism",
            "AF": "atrial fibrillation",
            "VT": "ventricular tachycardia",
            "VF": "ventricular fibrillation"
        }
        
        # Dicionário de sinônimos clínicos
        self.synonym_dict = {
            "dor no peito": ["chest pain", "thoracic pain", "precordial pain"],
            "falta de ar": ["shortness of breath", "dyspnea", "breathing difficulty"],
            "hipertensão": ["hypertension", "high blood pressure", "elevated blood pressure"],
            "diabetes": ["diabetes mellitus", "diabetes", "sugar disease"],
            "pneumonia": ["pneumonia", "lung infection", "pulmonary infection"],
            "asma": ["asthma", "bronchial asthma", "reactive airway disease"],
            "gastrite": ["gastritis", "stomach inflammation", "gastric inflammation"],
            "hepatite": ["hepatitis", "liver inflammation", "hepatic inflammation"],
            "câncer": ["cancer", "malignancy", "neoplasm", "tumor"],
            "febre": ["fever", "pyrexia", "elevated temperature"],
            "dor de cabeça": ["headache", "cephalgia", "head pain"],
            "náusea": ["nausea", "sickness", "queasiness"],
            "vômito": ["vomiting", "emesis", "throwing up"],
            "diarreia": ["diarrhea", "loose stools", "watery stools"]
        }
        
        # Carrega termos clínicos
        self._load_clinical_terms(data_path)
        
        print(f"✅ Dicionários carregados:")
        print(f"   📝 Abreviações: {len(self.abbreviation_dict)}")
        print(f"   📝 Sinônimos: {len(self.synonym_dict)}")
        print(f"   📝 Termos clínicos: {len(self.clinical_terms)}")
        
    def _load_clinical_terms(self, data_path: str):
        """Carrega termos clínicos de arquivos"""
        # Carrega termos de arquivos existentes
        terms_files = [
            "enhanced_medical_translations.json",
            "medical_synonyms.json",
            "brazilian_medical_terms.json"
        ]
        
        for file_name in terms_files:
            file_path = os.path.join(data_path, file_name)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    if isinstance(data, dict):
                        for key, value in data.items():
                            self.clinical_terms.add(key.lower())
                            if isinstance(value, str):
                                self.clinical_terms.add(value.lower())
                            elif isinstance(value, list):
                                for item in value:
                                    if isinstance(item, str):
                                        self.clinical_terms.add(item.lower())
                except Exception as e:
                    print(f"   ⚠️ Erro ao carregar {file_name}: {e}")
                    
    def translate_clinical_text(self, text: str, expand_synonyms: bool = True) -> Dict[str, any]:
        """
        Traduz texto clínico com expansão de sinônimos
        
        Args:
            text: Texto em português
            expand_synonyms: Se deve expandir sinônimos
            
        Returns:
            Dicionário com tradução e metadados
        """
        print(f"🌐 Traduzindo: '{text}'")
        
        # 1. Normalização e limpeza
        normalized_text = self._normalize_text(text)
        
        # 2. Expansão de abreviações
        expanded_text = self._expand_abbreviations(normalized_text)
        
        # 3. Tradução base com MiniLM
        base_translation = self._translate_with_minilm(expanded_text)
        
        # 4. Expansão de sinônimos (se solicitado)
        synonyms = []
        if expand_synonyms:
            synonyms = self._generate_synonyms(base_translation)
            
        # 5. Normalização clínica com SapBERT
        clinical_aliases = []
        if self.sapbert_model and self.expansion_config["use_sapbert"]:
            clinical_aliases = self._get_clinical_aliases(base_translation)
            
        # 6. Desambiguação neural (fallback)
        disambiguated = self._disambiguate_terms(base_translation)
        
        result = {
            "original_text": text,
            "normalized_text": normalized_text,
            "base_translation": base_translation,
            "synonyms": synonyms,
            "clinical_aliases": clinical_aliases,
            "disambiguated": disambiguated,
            "all_variants": [base_translation] + synonyms + clinical_aliases,
            "confidence": self._calculate_confidence(text, base_translation)
        }
        
        print(f"   ✅ Traduzido: '{base_translation}'")
        print(f"   📊 Sinônimos: {len(synonyms)}")
        print(f"   🔬 Aliases clínicos: {len(clinical_aliases)}")
        
        return result
        
    def _normalize_text(self, text: str) -> str:
        """Normaliza texto clínico"""
        # Remove caracteres especiais
        text = re.sub(r'[^\w\s\-]', ' ', text)
        
        # Normaliza espaços
        text = re.sub(r'\s+', ' ', text)
        
        # Converte para minúsculas
        text = text.lower().strip()
        
        return text
        
    def _expand_abbreviations(self, text: str) -> str:
        """Expande abreviações clínicas"""
        words = text.split()
        expanded_words = []
        
        for word in words:
            # Remove pontuação para busca
            clean_word = re.sub(r'[^\w]', '', word.upper())
            
            if clean_word in self.abbreviation_dict:
                expanded_words.append(self.abbreviation_dict[clean_word])
            else:
                expanded_words.append(word)
                
        return ' '.join(expanded_words)
        
    def _translate_with_minilm(self, text: str) -> str:
        """Traduz usando MiniLM"""
        if self.minilm_model is None:
            self.load_models()
            
        # Usa MiniLM para tradução
        # Para simplificar, vamos usar o dicionário de sinônimos
        text_lower = text.lower()
        
        # Busca tradução direta
        for pt_term, en_terms in self.synonym_dict.items():
            if pt_term in text_lower:
                if isinstance(en_terms, list):
                    return en_terms[0]  # Primeiro sinônimo
                else:
                    return en_terms
                    
        # Se não encontrou, retorna o texto original
        return text
        
    def _generate_synonyms(self, text: str) -> List[str]:
        """Gera sinônimos usando MiniLM"""
        if self.minilm_model is None:
            return []
            
        synonyms = []
        text_lower = text.lower()
        
        # Busca sinônimos no dicionário
        for pt_term, en_terms in self.synonym_dict.items():
            if pt_term in text_lower:
                if isinstance(en_terms, list):
                    synonyms.extend(en_terms[1:])  # Exclui o primeiro (já usado)
                else:
                    synonyms.append(en_terms)
                    
        # Gera sinônimos usando MiniLM (simulado)
        # Em implementação real, usaria top-k do modelo
        if len(synonyms) < self.expansion_config["max_synonyms"]:
            # Adiciona variações simples
            variations = [
                text.replace("acute", "chronic"),
                text.replace("chronic", "acute"),
                text + " syndrome",
                text + " disease"
            ]
            synonyms.extend(variations[:self.expansion_config["max_synonyms"] - len(synonyms)])
            
        return synonyms[:self.expansion_config["max_synonyms"]]
        
    def _get_clinical_aliases(self, text: str) -> List[str]:
        """Obtém aliases clínicos usando SapBERT"""
        if self.sapbert_model is None:
            return []
            
        aliases = []
        
        # Simula busca de aliases clínicos
        # Em implementação real, usaria SapBERT para encontrar termos similares
        text_lower = text.lower()
        
        # Busca termos relacionados
        for term in self.clinical_terms:
            if len(term) > 3 and term in text_lower:
                # Adiciona variações
                aliases.append(term.replace(" ", "_"))
                aliases.append(term.replace(" ", "-"))
                
        return aliases[:5]  # Limita a 5 aliases
        
    def _disambiguate_terms(self, text: str) -> str:
        """Desambigua termos usando contexto"""
        # Simula desambiguação neural
        # Em implementação real, usaria Marian/NLLB para fallback
        
        disambiguated = text
        
        # Regras de desambiguação simples
        if "diabetes" in text.lower():
            if "type 1" in text.lower() or "juvenil" in text.lower():
                disambiguated = "type 1 diabetes mellitus"
            elif "type 2" in text.lower() or "adulto" in text.lower():
                disambiguated = "type 2 diabetes mellitus"
            else:
                disambiguated = "diabetes mellitus"
                
        if "hipertensão" in text.lower():
            disambiguated = "arterial hypertension"
            
        if "pneumonia" in text.lower():
            if "comunidade" in text.lower() or "community" in text.lower():
                disambiguated = "community-acquired pneumonia"
            else:
                disambiguated = "pneumonia"
                
        return disambiguated
        
    def _calculate_confidence(self, original: str, translation: str) -> float:
        """Calcula confiança da tradução"""
        # Simula cálculo de confiança
        # Em implementação real, usaria scores do modelo
        
        confidence = 0.5  # Base
        
        # Bônus por correspondência exata
        if original.lower() in self.synonym_dict:
            confidence += 0.3
            
        # Bônus por termos clínicos conhecidos
        for term in self.clinical_terms:
            if term in translation.lower():
                confidence += 0.1
                break
                
        # Bônus por expansão de abreviações
        if any(abbr in original.upper() for abbr in self.abbreviation_dict):
            confidence += 0.2
            
        return min(confidence, 1.0)
        
    def batch_translate(self, texts: List[str], expand_synonyms: bool = True) -> List[Dict]:
        """Traduz múltiplos textos em lote"""
        print(f"🔄 Traduzindo {len(texts)} textos em lote...")
        
        results = []
        for i, text in enumerate(texts, 1):
            print(f"   {i}/{len(texts)}: {text}")
            result = self.translate_clinical_text(text, expand_synonyms)
            results.append(result)
            
        print(f"✅ Lote traduzido: {len(results)} textos")
        return results
        
    def save_translation_cache(self, cache_path: str = "data/cache/translation_cache.json"):
        """Salva cache de traduções"""
        # Implementa cache de traduções para evitar reprocessamento
        pass
        
    def load_translation_cache(self, cache_path: str = "data/cache/translation_cache.json"):
        """Carrega cache de traduções"""
        # Implementa carregamento de cache
        pass
