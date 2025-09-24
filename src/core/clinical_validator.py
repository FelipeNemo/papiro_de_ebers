"""
Sistema de Validação Clínica para Verificar Relevância dos Conceitos SNOMED
"""

import re
from typing import Dict, List, Tuple, Optional
from .medical_translator import MedicalTranslator
from .medical_filters import MedicalFilters

class ClinicalValidator:
    """Sistema de validação clínica para conceitos SNOMED"""
    
    def __init__(self):
        self.medical_translator = MedicalTranslator()
        self.medical_filters = MedicalFilters()
        
        # Padrões de validação clínica
        self.clinical_patterns = {
            'symptom_syndromes': [
                r'acute\s+\w+\s+syndrome',
                r'chronic\s+\w+\s+disorder',
                r'\w+\s+deficiency\s+syndrome',
                r'\w+\s+overdose\s+syndrome'
            ],
            'anatomical_structures': [
                r'\w+\s+of\s+the\s+\w+',
                r'\w+\s+muscle',
                r'\w+\s+nerve',
                r'\w+\s+artery',
                r'\w+\s+vein',
                r'\w+\s+bone',
                r'\w+\s+joint'
            ],
            'pathological_conditions': [
                r'\w+\s+inflammation',
                r'\w+\s+infection',
                r'\w+\s+tumor',
                r'\w+\s+carcinoma',
                r'\w+\s+malignancy',
                r'\w+\s+benign\s+\w+'
            ],
            'clinical_procedures': [
                r'\w+\s+surgery',
                r'\w+\s+procedure',
                r'\w+\s+examination',
                r'\w+\s+test',
                r'\w+\s+therapy',
                r'\w+\s+treatment'
            ]
        }
        
        # Termos de alta confiabilidade clínica
        self.high_confidence_terms = {
            'cardiology': [
                'myocardial infarction', 'heart failure', 'angina pectoris',
                'atrial fibrillation', 'ventricular tachycardia', 'cardiac arrest',
                'hypertensive heart disease', 'coronary artery disease'
            ],
            'pulmonology': [
                'pneumonia', 'asthma', 'chronic obstructive pulmonary disease',
                'pulmonary embolism', 'respiratory failure', 'pneumothorax',
                'tuberculosis', 'bronchitis'
            ],
            'gastroenterology': [
                'peptic ulcer', 'gastroenteritis', 'hepatitis', 'cirrhosis',
                'pancreatitis', 'appendicitis', 'cholecystitis', 'diverticulitis',
                'inflammatory bowel disease'
            ],
            'neurology': [
                'stroke', 'dementia', 'epilepsy', 'migraine', 'parkinson disease',
                'alzheimer disease', 'seizure', 'meningitis', 'encephalitis',
                'multiple sclerosis'
            ],
            'endocrinology': [
                'diabetes mellitus', 'hypoglycemia', 'hyperglycemia',
                'thyroid disorder', 'insulin resistance', 'diabetic ketoacidosis',
                'metabolic syndrome', 'obesity'
            ]
        }
        
        # Termos de baixa confiabilidade (evitar)
        self.low_confidence_terms = [
            'finding', 'observation', 'assessment', 'evaluation',
            'screening', 'monitoring', 'follow-up', 'routine',
            'general', 'unspecified', 'other', 'miscellaneous'
        ]
        
    def validate_concept(self, concept: Dict, query: str, specialty: str = None) -> Dict:
        """
        Valida um conceito SNOMED baseado em critérios clínicos
        
        Args:
            concept: Conceito SNOMED para validar
            query: Query original em português
            specialty: Especialidade médica detectada
            
        Returns:
            Dicionário com validação e score de confiança
        """
        term = concept.get('term', '').lower()
        concept_id = concept.get('conceptId', '')
        
        validation_result = {
            'concept_id': concept_id,
            'term': term,
            'is_valid': True,
            'confidence_score': 0.0,
            'validation_factors': {},
            'warnings': [],
            'recommendations': []
        }
        
        # 1. Validação de relevância clínica
        clinical_relevance = self._validate_clinical_relevance(term, specialty)
        validation_result['validation_factors']['clinical_relevance'] = clinical_relevance
        
        # 2. Validação de especificidade
        specificity = self._validate_specificity(term, query)
        validation_result['validation_factors']['specificity'] = specificity
        
        # 3. Validação de consistência terminológica
        terminological_consistency = self._validate_terminological_consistency(term)
        validation_result['validation_factors']['terminological_consistency'] = terminological_consistency
        
        # 4. Validação de prioridade clínica
        clinical_priority = self._validate_clinical_priority(term, specialty)
        validation_result['validation_factors']['clinical_priority'] = clinical_priority
        
        # 5. Validação de qualidade do termo
        term_quality = self._validate_term_quality(term)
        validation_result['validation_factors']['term_quality'] = term_quality
        
        # Calcula score de confiança geral
        confidence_score = self._calculate_confidence_score(validation_result['validation_factors'])
        validation_result['confidence_score'] = confidence_score
        
        # Aplica regras de validação
        validation_result = self._apply_validation_rules(validation_result, term, specialty)
        
        return validation_result
        
    def _validate_clinical_relevance(self, term: str, specialty: str) -> float:
        """Valida relevância clínica do termo"""
        if not specialty or specialty not in self.high_confidence_terms:
            return 0.5  # Score neutro se especialidade não conhecida
            
        high_confidence_terms = self.high_confidence_terms[specialty]
        
        # Verifica se o termo está na lista de alta confiança
        for high_term in high_confidence_terms:
            if high_term.lower() in term:
                return 1.0  # Score máximo para termos de alta confiança
                
        # Verifica padrões clínicos
        for pattern_type, patterns in self.clinical_patterns.items():
            for pattern in patterns:
                if re.search(pattern, term, re.IGNORECASE):
                    return 0.8  # Score alto para padrões clínicos reconhecidos
                    
        return 0.3  # Score baixo para outros termos
        
    def _validate_specificity(self, term: str, query: str) -> float:
        """Valida especificidade do termo em relação à query"""
        translated_query = self.medical_translator.translate_text(query).lower()
        
        # Conta palavras em comum
        query_words = set(translated_query.split())
        term_words = set(term.split())
        
        if not query_words:
            return 0.0
            
        # Calcula similaridade de palavras
        common_words = query_words.intersection(term_words)
        word_similarity = len(common_words) / len(query_words)
        
        # Bonus para termos mais específicos
        specificity_bonus = min(len(term_words) / 15, 0.3)  # Máximo 30% de bonus
        
        return min(word_similarity + specificity_bonus, 1.0)
        
    def _validate_terminological_consistency(self, term: str) -> float:
        """Valida consistência terminológica do termo"""
        # Verifica se o termo está em inglês (padrão SNOMED)
        if not term.isascii():
            return 0.2  # Score baixo para termos não em inglês
            
        # Verifica se contém palavras-chave médicas
        medical_keywords = ['disease', 'disorder', 'syndrome', 'condition', 'finding', 'procedure']
        keyword_count = sum(1 for keyword in medical_keywords if keyword in term)
        
        if keyword_count > 0:
            return 0.8  # Score alto para termos com palavras-chave médicas
            
        # Verifica se contém termos de baixa confiança
        for low_term in self.low_confidence_terms:
            if low_term in term:
                return 0.3  # Score baixo para termos de baixa confiança
                
        return 0.6  # Score médio para outros termos
        
    def _validate_clinical_priority(self, term: str, specialty: str) -> float:
        """Valida prioridade clínica do termo"""
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
        
    def _validate_term_quality(self, term: str) -> float:
        """Valida qualidade geral do termo"""
        # Verifica comprimento do termo
        if len(term) < 5:
            return 0.2  # Score baixo para termos muito curtos
        elif len(term) > 100:
            return 0.3  # Score baixo para termos muito longos
            
        # Verifica se contém caracteres especiais excessivos
        special_chars = sum(1 for char in term if not char.isalnum() and char != ' ')
        if special_chars > len(term) * 0.2:  # Mais de 20% de caracteres especiais
            return 0.3
            
        # Verifica se contém números (pode indicar códigos)
        if any(char.isdigit() for char in term):
            return 0.6  # Score médio para termos com números
            
        return 0.8  # Score alto para termos de boa qualidade
        
    def _calculate_confidence_score(self, validation_factors: Dict) -> float:
        """Calcula score de confiança baseado nos fatores de validação"""
        weights = {
            'clinical_relevance': 0.3,
            'specificity': 0.25,
            'terminological_consistency': 0.2,
            'clinical_priority': 0.15,
            'term_quality': 0.1
        }
        
        total_score = 0
        total_weight = 0
        
        for factor, score in validation_factors.items():
            if factor in weights:
                total_score += score * weights[factor]
                total_weight += weights[factor]
                
        return total_score / total_weight if total_weight > 0 else 0.0
        
    def _apply_validation_rules(self, validation_result: Dict, term: str, specialty: str) -> Dict:
        """Aplica regras de validação e gera recomendações"""
        confidence_score = validation_result['confidence_score']
        
        # Regra 1: Score mínimo de confiança
        if confidence_score < 0.3:
            validation_result['is_valid'] = False
            validation_result['warnings'].append("Score de confiança muito baixo")
            validation_result['recommendations'].append("Considerar remover este conceito")
            
        # Regra 2: Verifica termos de baixa confiança
        for low_term in self.low_confidence_terms:
            if low_term in term:
                validation_result['warnings'].append(f"Termo de baixa confiança detectado: {low_term}")
                validation_result['recommendations'].append("Verificar relevância clínica")
                
        # Regra 3: Verifica especificidade
        if validation_result['validation_factors']['specificity'] < 0.2:
            validation_result['warnings'].append("Especificidade muito baixa")
            validation_result['recommendations'].append("Considerar termos mais específicos")
            
        # Regra 4: Verifica relevância clínica
        if validation_result['validation_factors']['clinical_relevance'] < 0.3:
            validation_result['warnings'].append("Relevância clínica baixa")
            validation_result['recommendations'].append("Verificar se o conceito é clinicamente relevante")
            
        return validation_result
        
    def validate_concept_list(self, concepts: List[Dict], query: str, specialty: str = None) -> List[Dict]:
        """
        Valida uma lista de conceitos SNOMED
        
        Args:
            concepts: Lista de conceitos para validar
            query: Query original em português
            specialty: Especialidade médica detectada
            
        Returns:
            Lista de conceitos validados com scores de confiança
        """
        validated_concepts = []
        
        for concept in concepts:
            validation = self.validate_concept(concept, query, specialty)
            
            # Adiciona informações de validação ao conceito
            concept['validation'] = validation
            concept['is_valid'] = validation['is_valid']
            concept['confidence_score'] = validation['confidence_score']
            
            validated_concepts.append(concept)
            
        return validated_concepts
        
    def filter_valid_concepts(self, concepts: List[Dict], min_confidence: float = 0.3) -> List[Dict]:
        """
        Filtra conceitos baseado no score de confiança
        
        Args:
            concepts: Lista de conceitos para filtrar
            min_confidence: Score mínimo de confiança
            
        Returns:
            Lista de conceitos válidos
        """
        valid_concepts = []
        
        for concept in concepts:
            if concept.get('is_valid', False) and concept.get('confidence_score', 0) >= min_confidence:
                valid_concepts.append(concept)
                
        return valid_concepts
