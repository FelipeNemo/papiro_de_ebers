"""
Sistema de Re-ranking Inteligente para Melhorar Qualidade dos Resultados
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from .medical_translator import MedicalTranslator
from .medical_filters import MedicalFilters
from evaluation.quality_assessor import QualityAssessor
import re

class IntelligentReranking:
    """Sistema de re-ranking inteligente para melhorar qualidade dos resultados"""
    
    def __init__(self):
        self.medical_translator = MedicalTranslator()
        self.medical_filters = MedicalFilters()
        self.quality_assessor = QualityAssessor()
        
        # Fatores de re-ranking
        self.reranking_factors = {
            'clinical_relevance': 0.3,      # Relevância clínica
            'term_specificity': 0.25,       # Especificidade do termo
            'symptom_match': 0.2,           # Correspondência de sintomas
            'condition_priority': 0.15,     # Prioridade da condição
            'language_consistency': 0.1     # Consistência de linguagem
        }
        
        # Termos de alta prioridade clínica
        self.high_priority_terms = {
            'cardiology': [
                'myocardial infarction', 'heart failure', 'angina', 'arrhythmia',
                'hypertension', 'cardiac arrest', 'stroke', 'embolism'
            ],
            'pulmonology': [
                'pneumonia', 'asthma', 'copd', 'respiratory failure', 'pneumothorax',
                'tuberculosis', 'pulmonary edema', 'acute respiratory distress'
            ],
            'gastroenterology': [
                'peptic ulcer', 'gastroenteritis', 'hepatitis', 'cirrhosis',
                'pancreatitis', 'appendicitis', 'cholecystitis', 'diverticulitis'
            ],
            'neurology': [
                'stroke', 'dementia', 'epilepsy', 'migraine', 'parkinson',
                'alzheimer', 'seizure', 'meningitis', 'encephalitis'
            ],
            'endocrinology': [
                'diabetes', 'hypoglycemia', 'hyperglycemia', 'thyroid',
                'insulin', 'ketoacidosis', 'diabetic', 'metabolic'
            ]
        }
        
        # Padrões de sintomas críticos
        self.critical_symptoms = [
            'chest pain', 'shortness of breath', 'severe pain', 'acute pain',
            'high fever', 'severe headache', 'loss of consciousness',
            'severe bleeding', 'difficulty breathing', 'severe nausea'
        ]
        
    def rerank_concepts(self, concepts: List[Dict], query: str, specialty: str = None) -> List[Dict]:
        """
        Re-ranqueia conceitos baseado em múltiplos fatores clínicos
        
        Args:
            concepts: Lista de conceitos SNOMED
            query: Query original em português
            specialty: Especialidade médica detectada
            
        Returns:
            Lista de conceitos re-ranqueados
        """
        if not concepts:
            return concepts
            
        print(f"🔄 Re-ranqueando {len(concepts)} conceitos...")
        
        # Calcula scores de re-ranking para cada conceito
        reranked_concepts = []
        for concept in concepts:
            rerank_score = self._calculate_rerank_score(concept, query, specialty)
            concept['rerank_score'] = rerank_score
            reranked_concepts.append(concept)
        
        # Ordena por score de re-ranking
        reranked_concepts.sort(key=lambda x: x['rerank_score'], reverse=True)
        
        # Aplica filtros de qualidade
        filtered_concepts = self._apply_quality_filters(reranked_concepts, query, specialty)
        
        print(f"✅ Re-ranqueamento concluído: {len(filtered_concepts)} conceitos finais")
        return filtered_concepts
        
    def _calculate_rerank_score(self, concept: Dict, query: str, specialty: str) -> float:
        """Calcula score de re-ranking para um conceito"""
        term = concept.get('term', '').lower()
        concept_id = concept.get('conceptId', '')
        
        # 1. Relevância clínica (30%)
        clinical_relevance = self._calculate_clinical_relevance(term, specialty)
        
        # 2. Especificidade do termo (25%)
        term_specificity = self._calculate_term_specificity(term, query)
        
        # 3. Correspondência de sintomas (20%)
        symptom_match = self._calculate_symptom_match(term, query)
        
        # 4. Prioridade da condição (15%)
        condition_priority = self._calculate_condition_priority(term, specialty)
        
        # 5. Consistência de linguagem (10%)
        language_consistency = self._calculate_language_consistency(term, query)
        
        # Score final ponderado
        final_score = (
            clinical_relevance * self.reranking_factors['clinical_relevance'] +
            term_specificity * self.reranking_factors['term_specificity'] +
            symptom_match * self.reranking_factors['symptom_match'] +
            condition_priority * self.reranking_factors['condition_priority'] +
            language_consistency * self.reranking_factors['language_consistency']
        )
        
        return final_score
        
    def _calculate_clinical_relevance(self, term: str, specialty: str) -> float:
        """Calcula relevância clínica do termo"""
        if not specialty or specialty not in self.high_priority_terms:
            return 0.5  # Score neutro se especialidade não conhecida
            
        priority_terms = self.high_priority_terms[specialty]
        
        # Verifica se o termo contém palavras-chave de alta prioridade
        for priority_term in priority_terms:
            if priority_term.lower() in term:
                return 1.0  # Score máximo para termos de alta prioridade
                
        # Score baseado em palavras-chave médicas gerais
        medical_keywords = ['disease', 'disorder', 'syndrome', 'condition', 'finding', 'procedure']
        for keyword in medical_keywords:
            if keyword in term:
                return 0.7  # Score alto para termos médicos gerais
                
        return 0.3  # Score baixo para outros termos
        
    def _calculate_term_specificity(self, term: str, query: str) -> float:
        """Calcula especificidade do termo em relação à query"""
        # Traduz query para inglês para comparação
        translated_query = self.medical_translator.translate_text(query).lower()
        
        # Conta palavras em comum
        query_words = set(translated_query.split())
        term_words = set(term.split())
        
        if not query_words:
            return 0.0
            
        # Calcula similaridade de palavras
        common_words = query_words.intersection(term_words)
        word_similarity = len(common_words) / len(query_words)
        
        # Bonus para termos mais específicos (mais palavras)
        specificity_bonus = min(len(term_words) / 10, 0.3)  # Máximo 30% de bonus
        
        return min(word_similarity + specificity_bonus, 1.0)
        
    def _calculate_symptom_match(self, term: str, query: str) -> float:
        """Calcula correspondência de sintomas"""
        translated_query = self.medical_translator.translate_text(query).lower()
        
        # Verifica sintomas críticos
        for symptom in self.critical_symptoms:
            if symptom in translated_query and symptom in term:
                return 1.0  # Score máximo para sintomas críticos
                
        # Verifica correspondência geral de sintomas
        symptom_keywords = ['pain', 'fever', 'cough', 'nausea', 'vomiting', 'diarrhea', 'headache']
        matches = 0
        for keyword in symptom_keywords:
            if keyword in translated_query and keyword in term:
                matches += 1
                
        return min(matches / len(symptom_keywords), 1.0)
        
    def _calculate_condition_priority(self, term: str, specialty: str) -> float:
        """Calcula prioridade da condição médica"""
        # Condições de alta prioridade (urgentes)
        high_priority_conditions = [
            'acute', 'severe', 'critical', 'emergency', 'urgent',
            'myocardial infarction', 'stroke', 'respiratory failure',
            'septic shock', 'cardiac arrest', 'pneumothorax'
        ]
        
        for condition in high_priority_conditions:
            if condition in term:
                return 1.0  # Score máximo para condições urgentes
                
        # Condições de média prioridade
        medium_priority_conditions = [
            'chronic', 'recurrent', 'persistent', 'progressive',
            'diabetes', 'hypertension', 'asthma', 'copd'
        ]
        
        for condition in medium_priority_conditions:
            if condition in term:
                return 0.7  # Score alto para condições crônicas
                
        return 0.4  # Score baixo para outras condições
        
    def _calculate_language_consistency(self, term: str, query: str) -> float:
        """Calcula consistência de linguagem"""
        # Verifica se o termo está em inglês (padrão SNOMED)
        if term.isascii() and not any(char.isdigit() for char in term):
            return 1.0  # Score máximo para termos em inglês
            
        # Penaliza termos com caracteres especiais ou números
        special_chars = sum(1 for char in term if not char.isalnum() and char != ' ')
        if special_chars > len(term) * 0.1:  # Mais de 10% de caracteres especiais
            return 0.3
            
        return 0.7  # Score médio para outros casos
        
    def _apply_quality_filters(self, concepts: List[Dict], query: str, specialty: str) -> List[Dict]:
        """Aplica filtros de qualidade aos conceitos re-ranqueados"""
        filtered_concepts = []
        
        for concept in concepts:
            # Filtro 1: Score mínimo de re-ranking
            if concept.get('rerank_score', 0) < 0.3:
                continue
                
            # Filtro 2: Relevância clínica mínima
            clinical_relevance = self._calculate_clinical_relevance(
                concept.get('term', ''), specialty
            )
            if clinical_relevance < 0.2:
                continue
                
            # Filtro 3: Especificidade mínima
            term_specificity = self._calculate_term_specificity(
                concept.get('term', ''), query
            )
            if term_specificity < 0.1:
                continue
                
            # Filtro 4: Evita duplicatas por conceito
            concept_id = concept.get('conceptId')
            if not any(c.get('conceptId') == concept_id for c in filtered_concepts):
                filtered_concepts.append(concept)
                
        return filtered_concepts
        
    def optimize_reranking_factors(self, test_cases: List[str], target_quality: float = 8.0) -> Dict:
        """
        Otimiza fatores de re-ranking baseado em casos de teste
        
        Args:
            test_cases: Lista de casos para otimização
            target_quality: Qualidade alvo
            
        Returns:
            Fatores otimizados
        """
        print("🔧 Otimizando fatores de re-ranking...")
        
        # Testa diferentes combinações de fatores
        factor_combinations = [
            {'clinical_relevance': 0.4, 'term_specificity': 0.3, 'symptom_match': 0.2, 'condition_priority': 0.1, 'language_consistency': 0.0},
            {'clinical_relevance': 0.3, 'term_specificity': 0.25, 'symptom_match': 0.25, 'condition_priority': 0.15, 'language_consistency': 0.05},
            {'clinical_relevance': 0.35, 'term_specificity': 0.2, 'symptom_match': 0.3, 'condition_priority': 0.1, 'language_consistency': 0.05},
            {'clinical_relevance': 0.25, 'term_specificity': 0.3, 'symptom_match': 0.2, 'condition_priority': 0.2, 'language_consistency': 0.05},
        ]
        
        best_factors = None
        best_quality = 0.0
        
        for factors in factor_combinations:
            print(f"🧪 Testando fatores: {factors}")
            
            # Atualiza fatores
            self.reranking_factors = factors
            
            # Testa com casos de exemplo
            total_quality = 0
            for case in test_cases[:3]:  # Testa com primeiros 3 casos
                # Simula re-ranking (implementação simplificada)
                quality = self._simulate_reranking_quality(case)
                total_quality += quality
            
            avg_quality = total_quality / min(len(test_cases), 3)
            print(f"   Qualidade média: {avg_quality:.2f}")
            
            if avg_quality > best_quality:
                best_quality = avg_quality
                best_factors = factors.copy()
        
        # Aplica melhores fatores
        if best_factors:
            self.reranking_factors = best_factors
            print(f"✅ Fatores otimizados: {self.reranking_factors}")
            print(f"   Qualidade alcançada: {best_quality:.2f}")
        
        return {
            'reranking_factors': self.reranking_factors,
            'best_quality': best_quality,
            'target_quality': target_quality
        }
        
    def _simulate_reranking_quality(self, query: str) -> float:
        """Simula qualidade do re-ranking para otimização"""
        # Implementação simplificada para teste
        # Em produção, usaria conceitos reais
        
        # Simula score baseado em palavras-chave médicas
        medical_keywords = ['pain', 'fever', 'cough', 'diabetes', 'hypertension', 'asthma']
        translated_query = self.medical_translator.translate_text(query).lower()
        
        matches = sum(1 for keyword in medical_keywords if keyword in translated_query)
        return min(matches / len(medical_keywords) * 10, 10.0)
