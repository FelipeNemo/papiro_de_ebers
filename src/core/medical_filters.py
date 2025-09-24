"""
Filtros Médicos Melhorados
Detecta especialidades médicas e filtra conceitos SNOMED com maior precisão
"""

import re
import pandas as pd
from typing import Dict, List, Tuple

class MedicalFilters:
    """Classe para filtros médicos especializados"""
    
    def __init__(self):
        # Mapeamento de palavras-chave para especialidades (melhorado)
        self.specialty_keywords = {
            "cardiology": [
                "coração", "cardíaco", "cardíaca", "infarto", "angina", "arritmia", 
                "hipertensão", "pressão", "coronária", "insuficiência cardíaca",
                "miocárdio", "fibrilação", "taquicardia", "bradicardia", "edema",
                "trombo", "trombose", "embolia", "isquemia", "dor torácica",
                "dor no peito", "dor precordial", "palpitação", "síncope"
            ],
            "endocrinology": [
                "diabetes", "glicemia", "glicose", "insulina", "tireoide", "tireóide",
                "hormônio", "metabolismo", "obesidade", "sobrepeso", "hiperglicemia",
                "hipoglicemia", "resistência à insulina", "hipotireoidismo", "hipertireoidismo",
                "açúcar", "glicemia", "hemoglobina glicada", "hba1c"
            ],
            "pulmonology": [
                "pulmão", "pulmonar", "respiratório", "respiração", "dispneia",
                "falta de ar", "dpoc", "asma", "bronquite", "enfisema", "pneumonia",
                "tuberculose", "tosse", "expectoração", "hemoptise", "oxigênio",
                "ventilação", "ventilador", "saturação", "oximetria"
            ],
            "gastroenterology": [
                "estômago", "gástrico", "gástrica", "duodeno", "duodenal", "úlcera",
                "hemorragia", "sangramento", "sangramento digestivo", "hematêmese",
                "melena", "hematochezia", "fígado", "hepático", "hepatite", "cirrose",
                "pâncreas", "pancreático", "pancreatite", "intestino", "intestinal",
                "cólon", "colônico", "apêndice", "apendicite", "diverticulite"
            ],
            "neurology": [
                "cérebro", "cerebral", "neurológico", "neurológica", "avc", "derrame",
                "convulsão", "epilepsia", "cefaleia", "enxaqueca", "tontura", "vertigem",
                "desmaio", "síncope", "coma", "paralisia", "hemiplegia", "paraplegia",
                "tetraplegia", "tremor", "parkinson", "alzheimer", "demência",
                "esclerose múltipla", "acidente vascular cerebral"
            ],
            "nephrology": [
                "rim", "renal", "nefrite", "insuficiência renal", "doença renal crônica",
                "diálise", "hemodiálise", "transplante renal", "cálculo renal",
                "nefrolitíase", "uremia", "creatinina", "uréia", "proteinúria",
                "hematúria", "poliúria", "oligúria", "anúria"
            ]
        }
        
        # Mapeamento de conceitos SNOMED para especialidades (expandido)
        self.snomed_specialty_map = {
            # Cardiologia
            "myocardial infarction": "cardiology",
            "acute myocardial infarction": "cardiology",
            "angina": "cardiology",
            "angina pectoris": "cardiology",
            "heart failure": "cardiology",
            "congestive heart failure": "cardiology",
            "hypertension": "cardiology",
            "atrial fibrillation": "cardiology",
            "arrhythmia": "cardiology",
            "tachycardia": "cardiology",
            "bradycardia": "cardiology",
            "cardiac": "cardiology",
            "coronary": "cardiology",
            "ischemia": "cardiology",
            "thrombosis": "cardiology",
            "embolism": "cardiology",
            
            # Endocrinologia
            "diabetes mellitus": "endocrinology",
            "type 1 diabetes": "endocrinology",
            "type 2 diabetes": "endocrinology",
            "hyperglycemia": "endocrinology",
            "hypoglycemia": "endocrinology",
            "diabetic": "endocrinology",
            "insulin": "endocrinology",
            "thyroid": "endocrinology",
            "hypothyroidism": "endocrinology",
            "hyperthyroidism": "endocrinology",
            "obesity": "endocrinology",
            "overweight": "endocrinology",
            
            # Pneumologia
            "chronic obstructive pulmonary disease": "pulmonology",
            "copd": "pulmonology",
            "asthma": "pulmonology",
            "bronchitis": "pulmonology",
            "chronic bronchitis": "pulmonology",
            "emphysema": "pulmonology",
            "pneumonia": "pulmonology",
            "tuberculosis": "pulmonology",
            "pulmonary": "pulmonology",
            "respiratory": "pulmonology",
            "dyspnea": "pulmonology",
            "lung": "pulmonology",
            
            # Gastroenterologia
            "peptic ulcer": "gastroenterology",
            "gastric ulcer": "gastroenterology",
            "duodenal ulcer": "gastroenterology",
            "ulcer": "gastroenterology",
            "hemorrhage": "gastroenterology",
            "bleeding": "gastroenterology",
            "gastrointestinal": "gastroenterology",
            "hepatitis": "gastroenterology",
            "cirrhosis": "gastroenterology",
            "pancreatitis": "gastroenterology",
            "appendicitis": "gastroenterology",
            "diverticulitis": "gastroenterology",
            "gastric": "gastroenterology",
            "duodenal": "gastroenterology",
            "hepatic": "gastroenterology",
            "pancreatic": "gastroenterology",
            
            # Neurologia
            "stroke": "neurology",
            "cerebrovascular accident": "neurology",
            "seizure": "neurology",
            "epilepsy": "neurology",
            "headache": "neurology",
            "migraine": "neurology",
            "dizziness": "neurology",
            "vertigo": "neurology",
            "syncope": "neurology",
            "coma": "neurology",
            "paralysis": "neurology",
            "hemiplegia": "neurology",
            "paraplegia": "neurology",
            "tetraplegia": "neurology",
            "tremor": "neurology",
            "parkinson": "neurology",
            "alzheimer": "neurology",
            "dementia": "neurology",
            "multiple sclerosis": "neurology",
            
            # Nefrologia
            "kidney": "nephrology",
            "renal": "nephrology",
            "nephritis": "nephrology",
            "renal failure": "nephrology",
            "chronic kidney disease": "nephrology",
            "dialysis": "nephrology",
            "hemodialysis": "nephrology",
            "kidney transplant": "nephrology",
            "kidney stone": "nephrology",
            "nephrolithiasis": "nephrology",
            "uremia": "nephrology",
            "creatinine": "nephrology",
            "urea": "nephrology",
            "proteinuria": "nephrology",
            "hematuria": "nephrology"
        }
    
    def get_specialty_keywords(self, specialty: str) -> List[str]:
        """Retorna palavras-chave para uma especialidade"""
        return self.specialty_keywords.get(specialty, [])
    
    def get_specialty_patterns(self, specialty: str) -> List[str]:
        """Retorna padrões regex para uma especialidade"""
        keywords = self.get_specialty_keywords(specialty)
        return [f"\\b{re.escape(kw)}\\b" for kw in keywords]
    
    def detect_specialty(self, text: str) -> str:
        """Detecta a especialidade médica mais provável com base em palavras-chave no texto"""
        text_lower = text.lower()
        scores = {specialty: 0 for specialty in self.specialty_keywords}
        
        for specialty, keywords in self.specialty_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[specialty] += 1
        
        # Retorna a especialidade com a maior pontuação, ou 'general' se nenhuma for detectada
        best_specialty = max(scores, key=scores.get)
        if scores[best_specialty] > 0:
            return best_specialty
        return "general"
    
    def filter_snomed_concepts(self, concepts: List[Dict], text: str, specialty: str) -> List[Dict]:
        """Filtra conceitos SNOMED para manter apenas os relevantes para a especialidade"""
        if specialty == "general":
            return concepts
        
        patterns = self.get_specialty_patterns(specialty)
        filtered_concepts = []
        
        for concept in concepts:
            term = concept.get("term", "").lower()
            for pattern in patterns:
                if re.search(pattern, term, re.IGNORECASE):
                    filtered_concepts.append(concept)
                    break
        
        # Se não encontrou conceitos específicos, retorna os originais
        return filtered_concepts if filtered_concepts else concepts
    
    def score_concept_relevance(self, concept: Dict, text: str, specialty: str) -> float:
        """Calcula score de relevância de um conceito para o texto e especialidade"""
        term = concept.get("term", "").lower()
        text_lower = text.lower()
        
        score = 0
        
        # Score baseado em palavras-chave da especialidade
        keywords = self.get_specialty_keywords(specialty)
        for keyword in keywords:
            if keyword in text_lower and keyword in term:
                score += 3  # Match exato
            elif keyword in text_lower:
                score += 1  # Palavra-chave no texto
            elif keyword in term:
                score += 1  # Palavra-chave no conceito
        
        # Score baseado em padrões SNOMED
        patterns = self.get_specialty_patterns(specialty)
        for pattern in patterns:
            if re.search(pattern, term, re.IGNORECASE):
                score += 2
        
        # Score baseado em palavras comuns
        common_words = set(text_lower.split()) & set(term.split())
        score += len(common_words) * 0.5
        
        # Bonus para FSN (Fully Specified Name)
        if "disorder" in term or "disease" in term:
            score += 0.5
        
        return score

# Instância global dos filtros
medical_filters = MedicalFilters()

def get_medical_specialty(text: str) -> str:
    """Função utilitária para detectar especialidade médica"""
    return medical_filters.detect_specialty(text)

def filter_snomed_concepts(concepts: List[Dict], text: str, specialty: str) -> List[Dict]:
    """Função utilitária para filtrar conceitos SNOMED"""
    return medical_filters.filter_snomed_concepts(concepts, text, specialty)

def score_concept_relevance(concept: Dict, text: str, specialty: str) -> float:
    """Função utilitária para calcular score de relevância"""
    return medical_filters.score_concept_relevance(concept, text, specialty)
