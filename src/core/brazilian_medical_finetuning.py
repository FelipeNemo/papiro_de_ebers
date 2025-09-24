"""
Sistema de Fine-tuning para Termos Médicos Brasileiros
Fase 4: Adaptação do PubMedBERT para terminologia brasileira
"""

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sentence_transformers import SentenceTransformer, InputExample, losses
from sentence_transformers.evaluation import EmbeddingSimilarityEvaluator
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import json
import os
from .config import EMBEDDING_MODEL

class BrazilianMedicalDataset(Dataset):
    """Dataset para fine-tuning com termos médicos brasileiros"""
    
    def __init__(self, data_path: str = "data/brazilian_medical_terms.json"):
        """
        Inicializa dataset com termos médicos brasileiros
        
        Args:
            data_path: Caminho para dados de treinamento
        """
        self.data_path = data_path
        self.examples = []
        self.load_data()
        
    def load_data(self):
        """Carrega dados de treinamento"""
        if os.path.exists(self.data_path):
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.examples = [InputExample(**example) for example in data]
        else:
            # Cria dados de exemplo se não existir
            self.create_sample_data()
            
    def create_sample_data(self):
        """Cria dados de exemplo para fine-tuning"""
        sample_data = [
            # Termos cardiovasculares
            {"texts": ["dor no peito", "chest pain"], "label": 1.0},
            {"texts": ["infarto do miocárdio", "myocardial infarction"], "label": 1.0},
            {"texts": ["hipertensão arterial", "arterial hypertension"], "label": 1.0},
            {"texts": ["insuficiência cardíaca", "heart failure"], "label": 1.0},
            {"texts": ["arritmia cardíaca", "cardiac arrhythmia"], "label": 1.0},
            
            # Termos respiratórios
            {"texts": ["falta de ar", "shortness of breath"], "label": 1.0},
            {"texts": ["pneumonia", "pneumonia"], "label": 1.0},
            {"texts": ["asma", "asthma"], "label": 1.0},
            {"texts": ["bronquite", "bronchitis"], "label": 1.0},
            {"texts": ["enfisema pulmonar", "pulmonary emphysema"], "label": 1.0},
            
            # Termos endocrinológicos
            {"texts": ["diabetes mellitus", "diabetes mellitus"], "label": 1.0},
            {"texts": ["diabetes tipo 1", "type 1 diabetes"], "label": 1.0},
            {"texts": ["diabetes tipo 2", "type 2 diabetes"], "label": 1.0},
            {"texts": ["hipoglicemia", "hypoglycemia"], "label": 1.0},
            {"texts": ["hiperglicemia", "hyperglycemia"], "label": 1.0},
            
            # Termos neurológicos
            {"texts": ["acidente vascular cerebral", "cerebrovascular accident"], "label": 1.0},
            {"texts": ["AVC", "stroke"], "label": 1.0},
            {"texts": ["epilepsia", "epilepsy"], "label": 1.0},
            {"texts": ["enxaqueca", "migraine"], "label": 1.0},
            {"texts": ["demência", "dementia"], "label": 1.0},
            
            # Termos gastrointestinais
            {"texts": ["gastrite", "gastritis"], "label": 1.0},
            {"texts": ["úlcera gástrica", "gastric ulcer"], "label": 1.0},
            {"texts": ["hepatite", "hepatitis"], "label": 1.0},
            {"texts": ["cirrose hepática", "liver cirrhosis"], "label": 1.0},
            {"texts": ["pancreatite", "pancreatitis"], "label": 1.0},
            
            # Termos oncológicos
            {"texts": ["câncer", "cancer"], "label": 1.0},
            {"texts": ["tumor maligno", "malignant tumor"], "label": 1.0},
            {"texts": ["metástase", "metastasis"], "label": 1.0},
            {"texts": ["quimioterapia", "chemotherapy"], "label": 1.0},
            {"texts": ["radioterapia", "radiotherapy"], "label": 1.0},
            
            # Termos gerais
            {"texts": ["febre", "fever"], "label": 1.0},
            {"texts": ["dor de cabeça", "headache"], "label": 1.0},
            {"texts": ["náusea", "nausea"], "label": 1.0},
            {"texts": ["vômito", "vomiting"], "label": 1.0},
            {"texts": ["diarreia", "diarrhea"], "label": 1.0},
            
            # Exemplos de baixa similaridade
            {"texts": ["dor no peito", "diabetes mellitus"], "label": 0.1},
            {"texts": ["hipertensão", "pneumonia"], "label": 0.1},
            {"texts": ["asma", "gastrite"], "label": 0.1},
            {"texts": ["câncer", "febre"], "label": 0.2},
            {"texts": ["AVC", "diarreia"], "label": 0.1},
        ]
        
        # Salva dados de exemplo
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2, ensure_ascii=False)
            
        self.examples = [InputExample(**example) for example in sample_data]
        print(f"📊 Dataset criado com {len(self.examples)} exemplos")
        
    def __len__(self):
        return len(self.examples)
        
    def __getitem__(self, idx):
        return self.examples[idx]

class BrazilianMedicalFineTuner:
    """Sistema de fine-tuning para termos médicos brasileiros"""
    
    def __init__(self, model_name: str = None, device: str = None):
        """
        Inicializa sistema de fine-tuning
        
        Args:
            model_name: Nome do modelo base
            device: Dispositivo para treinamento
        """
        self.model_name = model_name or EMBEDDING_MODEL
        self.device = device or self._get_best_device()
        self.model = None
        self.dataset = None
        
        print(f"🔬 Inicializando Fine-tuning para Termos Brasileiros")
        print(f"🎯 Modelo base: {self.model_name}")
        print(f"💻 Dispositivo: {self.device}")
        
    def _get_best_device(self) -> str:
        """Detecta melhor dispositivo"""
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"
        
    def load_model(self):
        """Carrega modelo base"""
        print(f"📥 Carregando modelo: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        
        if self.device == "cuda":
            self.model = self.model.to(self.device)
            print(f"✅ Modelo movido para GPU: {torch.cuda.get_device_name(0)}")
        else:
            print("✅ Modelo carregado na CPU")
            
    def prepare_dataset(self, data_path: str = "data/brazilian_medical_terms.json"):
        """Prepara dataset para treinamento"""
        print("📊 Preparando dataset...")
        self.dataset = BrazilianMedicalDataset(data_path)
        print(f"✅ Dataset preparado: {len(self.dataset)} exemplos")
        
    def create_training_data(self, output_path: str = "data/brazilian_medical_terms.json"):
        """Cria dados de treinamento expandidos"""
        print("🔨 Criando dados de treinamento expandidos...")
        
        # Dados expandidos com mais termos médicos brasileiros
        expanded_data = [
            # Cardiologia
            {"texts": ["dor no peito", "chest pain"], "label": 1.0},
            {"texts": ["dor torácica", "chest pain"], "label": 1.0},
            {"texts": ["angina", "angina"], "label": 1.0},
            {"texts": ["infarto agudo do miocárdio", "acute myocardial infarction"], "label": 1.0},
            {"texts": ["IAM", "myocardial infarction"], "label": 1.0},
            {"texts": ["hipertensão arterial sistêmica", "systemic arterial hypertension"], "label": 1.0},
            {"texts": ["pressão alta", "high blood pressure"], "label": 1.0},
            {"texts": ["insuficiência cardíaca congestiva", "congestive heart failure"], "label": 1.0},
            {"texts": ["arritmia", "arrhythmia"], "label": 1.0},
            {"texts": ["fibrilação atrial", "atrial fibrillation"], "label": 1.0},
            
            # Pneumologia
            {"texts": ["falta de ar", "shortness of breath"], "label": 1.0},
            {"texts": ["dispneia", "dyspnea"], "label": 1.0},
            {"texts": ["pneumonia adquirida na comunidade", "community-acquired pneumonia"], "label": 1.0},
            {"texts": ["asma brônquica", "bronchial asthma"], "label": 1.0},
            {"texts": ["bronquite crônica", "chronic bronchitis"], "label": 1.0},
            {"texts": ["enfisema", "emphysema"], "label": 1.0},
            {"texts": ["DPOC", "COPD"], "label": 1.0},
            {"texts": ["tuberculose", "tuberculosis"], "label": 1.0},
            {"texts": ["câncer de pulmão", "lung cancer"], "label": 1.0},
            
            # Endocrinologia
            {"texts": ["diabetes mellitus tipo 1", "type 1 diabetes mellitus"], "label": 1.0},
            {"texts": ["diabetes mellitus tipo 2", "type 2 diabetes mellitus"], "label": 1.0},
            {"texts": ["diabetes descompensado", "uncontrolled diabetes"], "label": 1.0},
            {"texts": ["hipoglicemia", "hypoglycemia"], "label": 1.0},
            {"texts": ["hiperglicemia", "hyperglycemia"], "label": 1.0},
            {"texts": ["cetoacidose diabética", "diabetic ketoacidosis"], "label": 1.0},
            {"texts": ["neuropatia diabética", "diabetic neuropathy"], "label": 1.0},
            {"texts": ["retinopatia diabética", "diabetic retinopathy"], "label": 1.0},
            {"texts": ["pé diabético", "diabetic foot"], "label": 1.0},
            
            # Neurologia
            {"texts": ["acidente vascular cerebral", "cerebrovascular accident"], "label": 1.0},
            {"texts": ["AVC isquêmico", "ischemic stroke"], "label": 1.0},
            {"texts": ["AVC hemorrágico", "hemorrhagic stroke"], "label": 1.0},
            {"texts": ["epilepsia", "epilepsy"], "label": 1.0},
            {"texts": ["convulsão", "seizure"], "label": 1.0},
            {"texts": ["enxaqueca", "migraine"], "label": 1.0},
            {"texts": ["cefaleia", "headache"], "label": 1.0},
            {"texts": ["demência", "dementia"], "label": 1.0},
            {"texts": ["Alzheimer", "Alzheimer's disease"], "label": 1.0},
            {"texts": ["Parkinson", "Parkinson's disease"], "label": 1.0},
            
            # Gastroenterologia
            {"texts": ["gastrite", "gastritis"], "label": 1.0},
            {"texts": ["úlcera péptica", "peptic ulcer"], "label": 1.0},
            {"texts": ["refluxo gastroesofágico", "gastroesophageal reflux"], "label": 1.0},
            {"texts": ["hepatite viral", "viral hepatitis"], "label": 1.0},
            {"texts": ["cirrose", "cirrhosis"], "label": 1.0},
            {"texts": ["pancreatite aguda", "acute pancreatitis"], "label": 1.0},
            {"texts": ["doença de Crohn", "Crohn's disease"], "label": 1.0},
            {"texts": ["colite ulcerativa", "ulcerative colitis"], "label": 1.0},
            {"texts": ["síndrome do intestino irritável", "irritable bowel syndrome"], "label": 1.0},
            
            # Oncologia
            {"texts": ["câncer", "cancer"], "label": 1.0},
            {"texts": ["neoplasia maligna", "malignant neoplasm"], "label": 1.0},
            {"texts": ["tumor", "tumor"], "label": 1.0},
            {"texts": ["metástase", "metastasis"], "label": 1.0},
            {"texts": ["quimioterapia", "chemotherapy"], "label": 1.0},
            {"texts": ["radioterapia", "radiotherapy"], "label": 1.0},
            {"texts": ["imunoterapia", "immunotherapy"], "label": 1.0},
            {"texts": ["câncer de mama", "breast cancer"], "label": 1.0},
            {"texts": ["câncer de próstata", "prostate cancer"], "label": 1.0},
            {"texts": ["câncer de cólon", "colon cancer"], "label": 1.0},
            
            # Sintomas gerais
            {"texts": ["febre", "fever"], "label": 1.0},
            {"texts": ["hipertermia", "hyperthermia"], "label": 1.0},
            {"texts": ["dor de cabeça", "headache"], "label": 1.0},
            {"texts": ["cefaleia", "headache"], "label": 1.0},
            {"texts": ["náusea", "nausea"], "label": 1.0},
            {"texts": ["vômito", "vomiting"], "label": 1.0},
            {"texts": ["diarreia", "diarrhea"], "label": 1.0},
            {"texts": ["constipação", "constipation"], "label": 1.0},
            {"texts": ["fadiga", "fatigue"], "label": 1.0},
            {"texts": ["astenia", "asthenia"], "label": 1.0},
            
            # Exemplos de baixa similaridade
            {"texts": ["dor no peito", "diabetes"], "label": 0.1},
            {"texts": ["hipertensão", "pneumonia"], "label": 0.1},
            {"texts": ["asma", "gastrite"], "label": 0.1},
            {"texts": ["câncer", "febre"], "label": 0.2},
            {"texts": ["AVC", "diarreia"], "label": 0.1},
            {"texts": ["epilepsia", "hipertensão"], "label": 0.1},
            {"texts": ["pneumonia", "gastrite"], "label": 0.1},
            {"texts": ["diabetes", "asma"], "label": 0.1},
        ]
        
        # Salva dados expandidos
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(expanded_data, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Dados de treinamento criados: {len(expanded_data)} exemplos")
        
    def fine_tune(self, epochs: int = 3, batch_size: int = 16, 
                  output_path: str = "models/brazilian_pubmedbert"):
        """
        Executa fine-tuning do modelo
        
        Args:
            epochs: Número de épocas
            batch_size: Tamanho do lote
            output_path: Caminho para salvar modelo
        """
        if self.model is None:
            self.load_model()
            
        if self.dataset is None:
            self.prepare_dataset()
            
        print(f"🚀 Iniciando fine-tuning...")
        print(f"   📊 Épocas: {epochs}")
        print(f"   📦 Batch size: {batch_size}")
        print(f"   💾 Saída: {output_path}")
        
        # Prepara dados de treinamento
        train_examples = self.dataset.examples
        
        # Divide em treino e validação
        split_idx = int(0.8 * len(train_examples))
        train_data = train_examples[:split_idx]
        val_data = train_examples[split_idx:]
        
        print(f"   📊 Treino: {len(train_data)} exemplos")
        print(f"   📊 Validação: {len(val_data)} exemplos")
        
        # Configura loss function
        train_loss = losses.CosineSimilarityLoss(self.model)
        
        # Configura evaluator
        evaluator = EmbeddingSimilarityEvaluator.from_input_examples(
            val_data, name='brazilian_medical_eval'
        )
        
        # Executa fine-tuning
        self.model.fit(
            train_objectives=[(train_data, train_loss)],
            evaluator=evaluator,
            epochs=epochs,
            evaluation_steps=100,
            warmup_steps=100,
            output_path=output_path,
            save_best_model=True,
            show_progress_bar=True
        )
        
        print(f"✅ Fine-tuning concluído!")
        print(f"💾 Modelo salvo em: {output_path}")
        
    def evaluate_model(self, test_data_path: str = None) -> Dict:
        """
        Avalia modelo fine-tuned
        
        Args:
            test_data_path: Caminho para dados de teste
            
        Returns:
            Métricas de avaliação
        """
        if test_data_path and os.path.exists(test_data_path):
            test_dataset = BrazilianMedicalDataset(test_data_path)
        else:
            test_dataset = self.dataset
            
        print("🧪 Avaliando modelo fine-tuned...")
        
        # Testa similaridade em pares conhecidos
        test_pairs = [
            ("dor no peito", "chest pain"),
            ("infarto do miocárdio", "myocardial infarction"),
            ("hipertensão arterial", "arterial hypertension"),
            ("falta de ar", "shortness of breath"),
            ("diabetes mellitus", "diabetes mellitus"),
            ("pneumonia", "pneumonia"),
            ("asma", "asthma"),
            ("gastrite", "gastritis"),
            ("hepatite", "hepatitis"),
            ("câncer", "cancer")
        ]
        
        similarities = []
        for pt_term, en_term in test_pairs:
            # Gera embeddings
            pt_embedding = self.model.encode([pt_term])
            en_embedding = self.model.encode([en_term])
            
            # Calcula similaridade
            similarity = torch.cosine_similarity(
                torch.tensor(pt_embedding), 
                torch.tensor(en_embedding)
            ).item()
            
            similarities.append(similarity)
            print(f"   {pt_term} ↔ {en_term}: {similarity:.3f}")
        
        avg_similarity = np.mean(similarities)
        print(f"\n📊 Similaridade média: {avg_similarity:.3f}")
        
        return {
            "average_similarity": avg_similarity,
            "similarities": similarities,
            "test_pairs": test_pairs
        }
        
    def save_model(self, output_path: str = "models/brazilian_pubmedbert"):
        """Salva modelo fine-tuned"""
        if self.model is None:
            print("❌ Modelo não carregado")
            return
            
        os.makedirs(output_path, exist_ok=True)
        self.model.save(output_path)
        print(f"💾 Modelo salvo em: {output_path}")
        
    def load_fine_tuned_model(self, model_path: str = "models/brazilian_pubmedbert"):
        """Carrega modelo fine-tuned"""
        if os.path.exists(model_path):
            self.model = SentenceTransformer(model_path)
            if self.device == "cuda":
                self.model = self.model.to(self.device)
            print(f"✅ Modelo fine-tuned carregado: {model_path}")
            return True
        else:
            print(f"❌ Modelo não encontrado: {model_path}")
            return False
