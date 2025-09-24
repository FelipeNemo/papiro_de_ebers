"""
Sistema de Avaliação de Qualidade Melhorado
Avalia a qualidade dos mapeamentos SNOMED com critérios clínicos mais realistas
"""

import re
from typing import Dict, List, Tuple
from core.medical_filters import get_medical_specialty

class QualityAssessor:
    """Classe para avaliação de qualidade dos mapeamentos SNOMED"""
    
    def __init__(self):
        # Critérios de qualidade por especialidade
        self.quality_criteria = {
            "cardiology": {
                "primary_conditions": ["myocardial infarction", "angina", "heart failure", "hypertension"],
                "secondary_conditions": ["arrhythmia", "tachycardia", "bradycardia", "ischemia"],
                "keywords": ["infarto", "cardíaco", "coração", "angina", "hipertensão", "insuficiência cardíaca"],
                "weight_primary": 4.0,
                "weight_secondary": 2.0,
                "weight_keywords": 1.0
            },
            "endocrinology": {
                "primary_conditions": ["diabetes mellitus", "hyperglycemia", "hypoglycemia"],
                "secondary_conditions": ["thyroid", "obesity", "insulin resistance"],
                "keywords": ["diabetes", "glicemia", "insulina", "tireoide", "obesidade"],
                "weight_primary": 4.0,
                "weight_secondary": 2.0,
                "weight_keywords": 1.0
            },
            "pulmonology": {
                "primary_conditions": ["chronic obstructive pulmonary disease", "asthma", "pneumonia"],
                "secondary_conditions": ["bronchitis", "emphysema", "tuberculosis"],
                "keywords": ["dpoc", "pulmonar", "respiratório", "asma", "pneumonia"],
                "weight_primary": 4.0,
                "weight_secondary": 2.0,
                "weight_keywords": 1.0
            },
            "gastroenterology": {
                "primary_conditions": ["peptic ulcer", "gastric ulcer", "duodenal ulcer"],
                "secondary_conditions": ["hepatitis", "cirrhosis", "pancreatitis"],
                "keywords": ["úlcera", "gástrico", "duodenal", "hemorragia", "fígado"],
                "weight_primary": 4.0,
                "weight_secondary": 2.0,
                "weight_keywords": 1.0
            },
            "neurology": {
                "primary_conditions": ["stroke", "cerebrovascular accident", "epilepsy"],
                "secondary_conditions": ["headache", "migraine", "dementia", "parkinson"],
                "keywords": ["avc", "derrame", "convulsão", "epilepsia", "cérebro"],
                "weight_primary": 4.0,
                "weight_secondary": 2.0,
                "weight_keywords": 1.0
            },
            "nephrology": {
                "primary_conditions": ["chronic kidney disease", "renal failure", "dialysis"],
                "secondary_conditions": ["nephritis", "kidney stone", "uremia"],
                "keywords": ["rim", "renal", "diálise", "creatinina", "insuficiência renal"],
                "weight_primary": 4.0,
                "weight_secondary": 2.0,
                "weight_keywords": 1.0
            }
        }
    
    def assess_mapping_quality(self, text: str, concept: Dict, specialty: str) -> Dict:
        """
        Avalia a qualidade de um mapeamento SNOMED
        Retorna: score (0-10), relevância (0-1), adequação (0-1), justificativa
        """
        if not concept:
            return {
                "score": 0.0,
                "relevance": 0.0,
                "adequacy": 0.0,
                "justification": "Nenhum conceito selecionado"
            }
        
        term = concept.get("term", "").lower()
        text_lower = text.lower()
        
        # Obtém critérios para a especialidade
        criteria = self.quality_criteria.get(specialty, self.quality_criteria["cardiology"])
        
        # 1. Avaliação de Relevância (0-1)
        relevance_score = self._calculate_relevance(text_lower, term, criteria)
        
        # 2. Avaliação de Adequação (0-1)
        adequacy_score = self._calculate_adequacy(text_lower, term, criteria, specialty)
        
        # 3. Score Final (0-10)
        final_score = (relevance_score + adequacy_score) * 5
        
        # 4. Justificativa
        justification = self._generate_justification(text_lower, term, criteria, final_score)
        
        return {
            "score": round(final_score, 2),
            "relevance": round(relevance_score, 2),
            "adequacy": round(adequacy_score, 2),
            "justification": justification
        }
    
    def _calculate_relevance(self, text: str, term: str, criteria: Dict) -> float:
        """Calcula score de relevância baseado em palavras-chave"""
        score = 0
        total_weight = 0
        
        # Verifica condições primárias
        for condition in criteria["primary_conditions"]:
            if any(word in term for word in condition.split()):
                score += criteria["weight_primary"]
                total_weight += criteria["weight_primary"]
        
        # Verifica condições secundárias
        for condition in criteria["secondary_conditions"]:
            if any(word in term for word in condition.split()):
                score += criteria["weight_secondary"]
                total_weight += criteria["weight_secondary"]
        
        # Verifica palavras-chave no texto
        for keyword in criteria["keywords"]:
            if keyword in text:
                score += criteria["weight_keywords"]
                total_weight += criteria["weight_keywords"]
        
        return min(score / total_weight, 1.0) if total_weight > 0 else 0.0
    
    def _calculate_adequacy(self, text: str, term: str, criteria: Dict, specialty: str) -> float:
        """Calcula score de adequação baseado no contexto clínico"""
        score = 0
        
        # Verifica se o conceito faz sentido para o contexto
        if specialty == "cardiology" and any(kw in text for kw in ["infarto", "cardíaco", "coração"]):
            if any(term in concept for concept in ["myocardial infarction", "heart failure", "angina"]):
                score = 1.0
            elif any(term in concept for concept in ["cardiac", "coronary", "ischemia"]):
                score = 0.8
            else:
                score = 0.3
        
        elif specialty == "endocrinology" and any(kw in text for kw in ["diabetes", "glicemia", "insulina"]):
            if any(term in concept for concept in ["diabetes mellitus", "hyperglycemia", "hypoglycemia"]):
                score = 1.0
            elif any(term in concept for concept in ["insulin", "glucose", "diabetic"]):
                score = 0.8
            else:
                score = 0.3
        
        elif specialty == "pulmonology" and any(kw in text for kw in ["dpoc", "pulmonar", "respiratório"]):
            if any(term in concept for concept in ["chronic obstructive pulmonary disease", "asthma", "pneumonia"]):
                score = 1.0
            elif any(term in concept for concept in ["pulmonary", "respiratory", "lung"]):
                score = 0.8
            else:
                score = 0.3
        
        elif specialty == "gastroenterology" and any(kw in text for kw in ["úlcera", "gástrico", "duodenal"]):
            if any(term in concept for concept in ["peptic ulcer", "gastric ulcer", "duodenal ulcer"]):
                score = 1.0
            elif any(term in concept for concept in ["ulcer", "gastric", "duodenal"]):
                score = 0.8
            else:
                score = 0.3
        
        else:
            # Avaliação genérica
            common_words = set(text.split()) & set(term.split())
            score = min(len(common_words) / 5, 1.0)
        
        return score
    
    def _generate_justification(self, text: str, term: str, criteria: Dict, score: float) -> str:
        """Gera justificativa para o score"""
        if score >= 8:
            return "Excelente mapeamento - conceito altamente relevante e adequado"
        elif score >= 6:
            return "Bom mapeamento - conceito relevante com boa adequação"
        elif score >= 4:
            return "Mapeamento regular - conceito parcialmente relevante"
        elif score >= 2:
            return "Mapeamento fraco - conceito pouco relevante"
        else:
            return "Mapeamento inadequado - conceito não relevante para o contexto"

# Instância global do avaliador
quality_assessor = QualityAssessor()

def assess_mapping_quality(text: str, concept: Dict, specialty: str) -> Dict:
    """Função utilitária para avaliar qualidade do mapeamento"""
    return quality_assessor.assess_mapping_quality(text, concept, specialty)
