"""
Tradutor Médico Português-Inglês Melhorado
Mapeia termos médicos em português para inglês para melhor busca no SNOMED CT
"""

import re
from typing import Dict, List, Tuple

class MedicalTranslator:
    """Classe para tradução de termos médicos português-inglês"""
    
    def __init__(self):
        # Dicionário principal de tradução (expandido)
        self.translation_dict = {
            # Cardiologia
            "infarto": "myocardial infarction",
            "infarto agudo do miocárdio": "acute myocardial infarction",
            "infarto do miocárdio": "myocardial infarction",
            "miocárdio": "myocardium",
            "cardíaco": "cardiac",
            "cardíaca": "cardiac",
            "coração": "heart",
            "coronário": "coronary",
            "coronária": "coronary",
            "angina": "angina",
            "angina pectoris": "angina pectoris",
            "arritmia": "arrhythmia",
            "fibrilação": "fibrillation",
            "fibrilação atrial": "atrial fibrillation",
            "taquicardia": "tachycardia",
            "bradicardia": "bradycardia",
            "hipertensão": "hypertension",
            "pressão arterial": "blood pressure",
            "pressão alta": "high blood pressure",
            "insuficiência cardíaca": "heart failure",
            "insuficiência cardíaca congestiva": "congestive heart failure",
            "edema": "edema",
            "edema pulmonar": "pulmonary edema",
            "trombo": "thrombus",
            "trombose": "thrombosis",
            "embolia": "embolism",
            "isquemia": "ischemia",
            "isquêmico": "ischemic",
            "isquêmica": "ischemic",
            "dor no peito": "chest pain",
            "dor torácica": "chest pain",
            "falta de ar": "shortness of breath",
            "dispneia": "dyspnea",
            "síncope": "syncope",
            "desmaio": "fainting",
            "palpitação": "palpitation",
            "murmúrio": "murmur",
            "sopro": "murmur",
            "estenose": "stenosis",
            "regurgitação": "regurgitation",
            "insuficiência": "insufficiency",
            "prolapso": "prolapse",
            "valvulopatia": "valvular disease",
            "miocardiopatia": "cardiomyopathy",
            "pericardite": "pericarditis",
            "endocardite": "endocarditis",
            
            # Endocrinologia
            "diabetes": "diabetes",
            "diabetes mellitus": "diabetes mellitus",
            "diabetes tipo 1": "type 1 diabetes",
            "diabetes tipo 2": "type 2 diabetes",
            "diabetes descompensado": "decompensated diabetes",
            "hiperglicemia": "hyperglycemia",
            "hipoglicemia": "hypoglycemia",
            "cetoacidose": "ketoacidosis",
            "insulina": "insulin",
            "glicemia": "glycemia",
            "hemoglobina glicada": "glycated hemoglobin",
            "hba1c": "hba1c",
            "tireoide": "thyroid",
            "hipertireoidismo": "hyperthyroidism",
            "hipotireoidismo": "hypothyroidism",
            "hormônio": "hormone",
            "metabolismo": "metabolism",
            "obesidade": "obesity",
            "sobrepeso": "overweight",
            "diabetes insulino-dependente": "insulin-dependent diabetes",
            "diabetes não insulino-dependente": "non-insulin-dependent diabetes",
            "glicemia": "blood glucose",
            "glicose": "glucose",
            "hiperglicemia": "hyperglycemia",
            "hipoglicemia": "hypoglycemia",
            "insulina": "insulin",
            "resistência à insulina": "insulin resistance",
            "tireoide": "thyroid",
            "tireóide": "thyroid",
            "hipotireoidismo": "hypothyroidism",
            "hipertireoidismo": "hyperthyroidism",
            "hormônio": "hormone",
            "metabolismo": "metabolism",
            "obesidade": "obesity",
            "sobrepeso": "overweight",
            
            # Pneumologia
            "pulmão": "lung",
            "pulmonar": "pulmonary",
            "respiratório": "respiratory",
            "respiração": "breathing",
            "dispneia": "dyspnea",
            "falta de ar": "shortness of breath",
            "asfixia": "asphyxia",
            "dpoc": "chronic obstructive pulmonary disease",
            "doença pulmonar obstrutiva crônica": "chronic obstructive pulmonary disease",
            "asma": "asthma",
            "asma brônquica": "bronchial asthma",
            "bronquite": "bronchitis",
            "bronquite crônica": "chronic bronchitis",
            "enfisema": "emphysema",
            "pneumonia": "pneumonia",
            "pneumonia atípica": "atypical pneumonia",
            "tuberculose": "tuberculosis",
            "tosse": "cough",
            "tosse seca": "dry cough",
            "tosse produtiva": "productive cough",
            "tosse persistente": "persistent cough",
            "expectoração": "sputum",
            "hemoptise": "hemoptysis",
            "febre": "fever",
            "febre alta": "high fever",
            "hipertermia": "hyperthermia",
            "hipotermia": "hypothermia",
            "calafrio": "chills",
            "sudorese": "sweating",
            "diaforese": "diaphoresis",
            "oxigênio": "oxygen",
            "ventilação": "ventilation",
            "ventilador": "ventilator",
            
            # Gastroenterologia
            "estômago": "stomach",
            "gástrico": "gastric",
            "gástrica": "gastric",
            "duodeno": "duodenum",
            "duodenal": "duodenal",
            "úlcera": "ulcer",
            "úlcera péptica": "peptic ulcer",
            "úlcera gástrica": "gastric ulcer",
            "úlcera duodenal": "duodenal ulcer",
            "hemorragia": "hemorrhage",
            "sangramento": "bleeding",
            "sangramento digestivo": "gastrointestinal bleeding",
            "hemorragia digestiva": "gastrointestinal hemorrhage",
            "hematêmese": "hematemesis",
            "melena": "melena",
            "hematochezia": "hematochezia",
            "fígado": "liver",
            "hepático": "hepatic",
            "hepatite": "hepatitis",
            "cirrose": "cirrhosis",
            "pâncreas": "pancreas",
            "pancreático": "pancreatic",
            "pancreatite": "pancreatitis",
            "intestino": "intestine",
            "intestinal": "intestinal",
            "cólon": "colon",
            "colônico": "colonic",
            "apêndice": "appendix",
            "apendicite": "appendicitis",
            "diverticulite": "diverticulitis",
            "síndrome do intestino irritável": "irritable bowel syndrome",
            "doença de crohn": "crohn's disease",
            "colite ulcerativa": "ulcerative colitis",
            
            # Neurologia
            "cérebro": "brain",
            "cerebral": "cerebral",
            "neurológico": "neurological",
            "neurológica": "neurological",
            "avc": "stroke",
            "acidente vascular cerebral": "cerebrovascular accident",
            "derrame": "stroke",
            "convulsão": "seizure",
            "epilepsia": "epilepsy",
            "cefaleia": "headache",
            "enxaqueca": "migraine",
            "tontura": "dizziness",
            "vertigem": "vertigo",
            "desmaio": "syncope",
            "síncope": "syncope",
            "coma": "coma",
            "paralisia": "paralysis",
            "paralisia facial": "facial paralysis",
            "hemiplegia": "hemiplegia",
            "paraplegia": "paraplegia",
            "tetraplegia": "tetraplegia",
            "tremor": "tremor",
            "parkinson": "parkinson's disease",
            "alzheimer": "alzheimer's disease",
            "demência": "dementia",
            "esclerose múltipla": "multiple sclerosis",
            
            # Nefrologia
            "rim": "kidney",
            "renal": "renal",
            "nefrite": "nephritis",
            "insuficiência renal": "renal failure",
            "doença renal crônica": "chronic kidney disease",
            "diálise": "dialysis",
            "hemodiálise": "hemodialysis",
            "transplante renal": "kidney transplant",
            "cálculo renal": "kidney stone",
            "nefrolitíase": "nephrolithiasis",
            "uremia": "uremia",
            "creatinina": "creatinine",
            "uréia": "urea",
            "proteinúria": "proteinuria",
            "hematúria": "hematuria",
            "poliúria": "polyuria",
            "oligúria": "oliguria",
            "anúria": "anuria",
            
            # Geral
            "dor": "pain",
            "febre": "fever",
            "hipertermia": "hyperthermia",
            "hipotermia": "hypothermia",
            "náusea": "nausea",
            "náuseas": "nausea",
            "vômito": "vomiting",
            "vômitos": "vomiting",
            "diarreia": "diarrhea",
            "diarreia aguda": "acute diarrhea",
            "diarreia crônica": "chronic diarrhea",
            "constipação": "constipation",
            "dor abdominal": "abdominal pain",
            "dor no abdome": "abdominal pain",
            "anemia": "anemia",
            "leucemia": "leukemia",
            "linfoma": "lymphoma",
            "câncer": "cancer",
            "tumor": "tumor",
            "neoplasia": "neoplasia",
            "maligno": "malignant",
            "benigno": "benign",
            "metástase": "metastasis",
            "quimioterapia": "chemotherapy",
            "radioterapia": "radiotherapy",
            "cirurgia": "surgery",
            "operatório": "surgical",
            "pós-operatório": "postoperative",
            "complicação": "complication",
            "infecção": "infection",
            "inflamação": "inflammation",
            "crônico": "chronic",
            "agudo": "acute",
            "subagudo": "subacute",
            "síndrome": "syndrome",
            "doença": "disease",
            "distúrbio": "disorder",
            "deficiência": "deficiency",
            "insuficiência": "insufficiency",
            "falência": "failure",
            
            # Neurologia
            "cérebro": "brain",
            "cerebral": "cerebral",
            "neurológico": "neurological",
            "neurológica": "neurological",
            "demência": "dementia",
            "alzheimer": "alzheimer",
            "avc": "stroke",
            "acidente vascular cerebral": "cerebrovascular accident",
            "convulsão": "seizure",
            "epilepsia": "epilepsy",
            "enxaqueca": "migraine",
            "dor de cabeça": "headache",
            "confusão": "confusion",
            "memória": "memory",
            "cognitivo": "cognitive",
            "cognitiva": "cognitive",
            "parkinson": "parkinson",
            "tremor": "tremor",
            "paralisia": "paralysis",
            "parestesia": "paresthesia",
            "formigamento": "tingling",
            
            # Dermatologia
            "pele": "skin",
            "cutâneo": "cutaneous",
            "cutânea": "cutaneous",
            "dermatológico": "dermatological",
            "dermatológica": "dermatological",
            "erupção": "rash",
            "lesão": "lesion",
            "dermatite": "dermatitis",
            "eczema": "eczema",
            "psoríase": "psoriasis",
            "melanoma": "melanoma",
            "carcinoma": "carcinoma",
            "neoplasia": "neoplasia",
            "tumor": "tumor",
            "câncer de pele": "skin cancer",
            "verruga": "wart",
            "sarda": "freckle",
            "mancha": "spot",
            
            # Ortopedia
            "osso": "bone",
            "ósseo": "osseous",
            "óssea": "osseous",
            "esquelético": "skeletal",
            "esquelética": "skeletal",
            "musculoesquelético": "musculoskeletal",
            "musculoesquelética": "musculoskeletal",
            "fratura": "fracture",
            "luxação": "dislocation",
            "artrite": "arthritis",
            "osteoartrite": "osteoarthritis",
            "osteoporose": "osteoporosis",
            "articulação": "joint",
            "músculo": "muscle",
            "tendão": "tendon",
            "ligamento": "ligament",
            "cartilagem": "cartilage",
            "coluna": "spine",
            "vertebral": "vertebral",
            "hérnia": "hernia",
            "hérnia de disco": "disc herniation",
            
            # Urologia
            "rim": "kidney",
            "renal": "renal",
            "urinário": "urinary",
            "urinária": "urinary",
            "bexiga": "bladder",
            "próstata": "prostate",
            "nefrite": "nephritis",
            "nefrose": "nephrosis",
            "incontinência": "incontinence",
            "infecção urinária": "urinary tract infection",
            "cálculo": "calculus",
            "pedra": "stone",
            "litíase": "lithiasis",
            "uretra": "urethra",
            "ureter": "ureter",
            
            # Ginecologia
            "gravidez": "pregnancy",
            "grávida": "pregnant",
            "obstétrico": "obstetric",
            "obstétrica": "obstetric",
            "ginecológico": "gynecological",
            "ginecológica": "gynecological",
            "menstrual": "menstrual",
            "menstruação": "menstruation",
            "ovário": "ovary",
            "ovariano": "ovarian",
            "ovariana": "ovarian",
            "útero": "uterus",
            "uterino": "uterine",
            "uterina": "uterine",
            "cervical": "cervical",
            "vaginal": "vaginal",
            "mama": "breast",
            "mamário": "mammary",
            "mamária": "mammary",
            "mastite": "mastitis",
            "endometriose": "endometriosis",
            "mioma": "fibroid",
            
            # Pediatria
            "pediátrico": "pediatric",
            "pediátrica": "pediatric",
            "criança": "child",
            "infantil": "pediatric",
            "bebê": "baby",
            "recém-nascido": "newborn",
            "neonatal": "neonatal",
            "adolescente": "adolescent",
            "desenvolvimento": "development",
            "crescimento": "growth",
            "vacinação": "vaccination",
            "imunização": "immunization",
            "vacina": "vaccine",
            "amamentação": "breastfeeding",
            "aleitamento": "breastfeeding"
        }
        
        # Dicionário de sinônimos e variações
        self.synonyms = {
            # Variações de dor
            "dor": ["dolor", "ache", "pain"],
            "dores": ["dolores", "aches", "pains"],
            
            # Variações de febre
            "febre": ["fever", "pyrexia", "hyperthermia"],
            "febres": ["fevers", "pyrexias", "hyperthermias"],
            
            # Variações de náusea
            "náusea": ["nausea", "sickness", "queasiness"],
            "náuseas": ["nauseas", "sicknesses", "queasinesses"],
            
            # Variações de vômito
            "vômito": ["vomiting", "emesis", "throwing up"],
            "vômitos": ["vomitings", "emeses", "throwing ups"],
            
            # Variações de diarreia
            "diarreia": ["diarrhea", "loose stools", "bowel movement"],
            "diarreias": ["diarrheas", "loose stools", "bowel movements"],
            
            # Variações de tosse
            "tosse": ["cough", "coughing", "hacking"],
            "tosses": ["coughs", "coughings", "hackings"],
            
            # Variações de falta de ar
            "falta de ar": ["shortness of breath", "dyspnea", "breathlessness"],
        }
        
        # Padrões de tradução mais complexos
        self.pattern_translations = [
            (r"dor\s+no\s+peito", "chest pain"),
            (r"dor\s+torácica", "chest pain"),
            (r"dor\s+abdominal", "abdominal pain"),
            (r"dor\s+de\s+cabeça", "headache"),
            (r"falta\s+de\s+ar", "shortness of breath"),
            (r"dificuldade\s+para\s+respirar", "difficulty breathing"),
            (r"pressão\s+alta", "high blood pressure"),
            (r"pressão\s+baixa", "low blood pressure"),
            (r"açúcar\s+alto", "high blood sugar"),
            (r"açúcar\s+baixo", "low blood sugar"),
            (r"batimento\s+cardíaco", "heartbeat"),
            (r"ritmo\s+cardíaco", "heart rhythm"),
            (r"frequência\s+cardíaca", "heart rate"),
            (r"pressão\s+arterial", "blood pressure"),
            (r"temperatura\s+corporal", "body temperature"),
            (r"peso\s+corporal", "body weight"),
            (r"índice\s+de\s+massa\s+corporal", "body mass index"),
            (r"imc", "body mass index")
        ]
    
    def translate_term(self, term: str) -> str:
        """Traduz um termo médico do português para inglês com sinônimos"""
        term_lower = term.lower().strip()
        
        # Primeiro tenta tradução exata
        if term_lower in self.translation_dict:
            return self.translation_dict[term_lower]
        
        # Depois tenta padrões complexos
        for pattern, translation in self.pattern_translations:
            if re.search(pattern, term_lower):
                return translation
        
        # Busca por sinônimos
        for key, synonyms in self.synonyms.items():
            if term_lower == key or term_lower in synonyms:
                return self.translation_dict.get(key, term)
        
        # Se não encontrou, retorna o termo original
        return term
    
    def translate_text(self, text: str) -> str:
        """Traduz um texto médico do português para inglês com contexto"""
        # Primeiro, tenta traduzir frases completas (mais específicas)
        translated_text = self._translate_phrases(text)
        
        # Depois, traduz palavras individuais
        words = translated_text.split()
        translated_words = []
        
        for word in words:
            # Remove pontuação para tradução
            clean_word = re.sub(r'[^\w\s]', '', word)
            translated = self.translate_term(clean_word)
            translated_words.append(translated)
        
        return " ".join(translated_words)
    
    def _translate_phrases(self, text: str) -> str:
        """Traduz frases médicas específicas primeiro"""
        # Ordena por tamanho (mais específicas primeiro)
        phrases = sorted(self.translation_dict.keys(), key=len, reverse=True)
        
        translated_text = text.lower()
        
        for phrase in phrases:
            if phrase in translated_text:
                translated_text = translated_text.replace(phrase, self.translation_dict[phrase])
        
        return translated_text
    
    def get_medical_keywords(self, text: str) -> List[str]:
        """Extrai palavras-chave médicas de um texto e as traduz"""
        words = text.lower().split()
        medical_keywords = []
        
        for word in words:
            clean_word = re.sub(r'[^\w\s]', '', word)
            if clean_word in self.translation_dict:
                medical_keywords.append(self.translate_term(clean_word))
        
        return medical_keywords

# Instância global do tradutor
medical_translator = MedicalTranslator()

def translate_medical_term(term: str) -> str:
    """Função utilitária para traduzir termo médico"""
    return medical_translator.translate_term(term)

def translate_medical_text(text: str) -> str:
    """Função utilitária para traduzir texto médico"""
    return medical_translator.translate_text(text)

def get_medical_keywords(text: str) -> List[str]:
    """Função utilitária para extrair palavras-chave médicas"""
    return medical_translator.get_medical_keywords(text)
