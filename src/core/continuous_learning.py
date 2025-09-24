"""
Sistema de Aprendizado Contínuo para Melhorar Performance ao Longo do Tempo
"""

import json
import os
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from .medical_translator import MedicalTranslator
from .medical_filters import MedicalFilters
from evaluation.quality_assessor import QualityAssessor

class ContinuousLearning:
    """Sistema de aprendizado contínuo para melhorar performance"""
    
    def __init__(self, learning_data_path: str = "data/learning"):
        self.learning_data_path = learning_data_path
        self.medical_translator = MedicalTranslator()
        self.medical_filters = MedicalFilters()
        self.quality_assessor = QualityAssessor()
        
        # Dados de aprendizado
        self.learning_data = {
            'queries': [],
            'results': [],
            'feedback': [],
            'performance_metrics': []
        }
        
        # Parâmetros de aprendizado
        self.learning_params = {
            'min_samples_for_learning': 10,
            'learning_rate': 0.1,
            'decay_factor': 0.95,
            'confidence_threshold': 0.7
        }
        
        # Modelos de aprendizado
        self.learned_patterns = {
            'query_specialty_mapping': {},
            'term_translation_improvements': {},
            'quality_predictors': {},
            'performance_trends': {}
        }
        
        # Carrega dados existentes
        self._load_learning_data()
        
    def _load_learning_data(self):
        """Carrega dados de aprendizado existentes"""
        os.makedirs(self.learning_data_path, exist_ok=True)
        
        data_file = os.path.join(self.learning_data_path, "learning_data.json")
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    self.learning_data = json.load(f)
                print(f"📚 Dados de aprendizado carregados: {len(self.learning_data['queries'])} queries")
            except Exception as e:
                print(f"⚠️ Erro ao carregar dados de aprendizado: {e}")
                
    def _save_learning_data(self):
        """Salva dados de aprendizado"""
        data_file = os.path.join(self.learning_data_path, "learning_data.json")
        
        try:
            # Converte tipos numpy para tipos Python nativos
            def convert_numpy_types(obj):
                if isinstance(obj, dict):
                    return {k: convert_numpy_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy_types(item) for item in obj]
                elif hasattr(obj, 'item'):  # numpy scalar
                    return obj.item()
                elif hasattr(obj, 'tolist'):  # numpy array
                    return obj.tolist()
                else:
                    return obj
            
            converted_data = convert_numpy_types(self.learning_data)
            
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(converted_data, f, ensure_ascii=False, indent=2)
            print(f"💾 Dados de aprendizado salvos: {len(self.learning_data['queries'])} queries")
        except Exception as e:
            print(f"❌ Erro ao salvar dados de aprendizado: {e}")
            
    def record_query_result(self, query: str, results: List[Dict], specialty: str = None, quality_score: float = None):
        """
        Registra resultado de uma query para aprendizado
        
        Args:
            query: Query em português
            results: Lista de conceitos encontrados
            specialty: Especialidade detectada
            quality_score: Score de qualidade dos resultados
        """
        query_record = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'specialty': specialty,
            'num_results': len(results),
            'quality_score': quality_score,
            'results': results
        }
        
        self.learning_data['queries'].append(query_record)
        
        # Salva dados periodicamente
        if len(self.learning_data['queries']) % 10 == 0:
            self._save_learning_data()
            
    def record_feedback(self, query: str, concept_id: str, feedback_type: str, feedback_value: float):
        """
        Registra feedback do usuário sobre um conceito
        
        Args:
            query: Query original
            concept_id: ID do conceito SNOMED
            feedback_type: Tipo de feedback (relevance, accuracy, etc.)
            feedback_value: Valor do feedback (0-1)
        """
        feedback_record = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'concept_id': concept_id,
            'feedback_type': feedback_type,
            'feedback_value': feedback_value
        }
        
        self.learning_data['feedback'].append(feedback_record)
        
    def analyze_performance_trends(self) -> Dict:
        """Analisa tendências de performance ao longo do tempo"""
        if len(self.learning_data['queries']) < self.learning_params['min_samples_for_learning']:
            return {'status': 'insufficient_data', 'message': 'Dados insuficientes para análise'}
            
        # Converte timestamps para análise temporal
        queries_df = pd.DataFrame(self.learning_data['queries'])
        queries_df['timestamp'] = pd.to_datetime(queries_df['timestamp'])
        queries_df['date'] = queries_df['timestamp'].dt.date
        
        # Análise de tendências
        trends = {
            'quality_trend': self._analyze_quality_trend(queries_df),
            'specialty_distribution': self._analyze_specialty_distribution(queries_df),
            'query_patterns': self._analyze_query_patterns(queries_df),
            'performance_metrics': self._calculate_performance_metrics(queries_df)
        }
        
        return trends
        
    def _analyze_quality_trend(self, queries_df: pd.DataFrame) -> Dict:
        """Analisa tendência de qualidade ao longo do tempo"""
        if 'quality_score' not in queries_df.columns:
            return {'status': 'no_quality_data'}
            
        # Remove valores nulos
        quality_data = queries_df.dropna(subset=['quality_score'])
        
        if len(quality_data) < 5:
            return {'status': 'insufficient_quality_data'}
            
        # Calcula média móvel de qualidade
        quality_data = quality_data.sort_values('timestamp')
        quality_data['quality_ma'] = quality_data['quality_score'].rolling(window=5, min_periods=1).mean()
        
        # Calcula tendência
        recent_quality = quality_data['quality_ma'].tail(10).mean()
        overall_quality = quality_data['quality_score'].mean()
        
        trend_direction = 'improving' if recent_quality > overall_quality else 'declining'
        
        return {
            'overall_quality': overall_quality,
            'recent_quality': recent_quality,
            'trend_direction': trend_direction,
            'quality_improvement': recent_quality - overall_quality
        }
        
    def _analyze_specialty_distribution(self, queries_df: pd.DataFrame) -> Dict:
        """Analisa distribuição de especialidades"""
        if 'specialty' not in queries_df.columns:
            return {'status': 'no_specialty_data'}
            
        specialty_counts = queries_df['specialty'].value_counts()
        
        return {
            'distribution': specialty_counts.to_dict(),
            'most_common': specialty_counts.index[0] if len(specialty_counts) > 0 else None,
            'total_specialties': len(specialty_counts)
        }
        
    def _analyze_query_patterns(self, queries_df: pd.DataFrame) -> Dict:
        """Analisa padrões nas queries"""
        # Análise de comprimento das queries
        queries_df['query_length'] = queries_df['query'].str.len()
        
        # Análise de palavras-chave médicas
        medical_keywords = ['dor', 'febre', 'diabetes', 'hipertensão', 'asma', 'pneumonia']
        keyword_analysis = {}
        
        for keyword in medical_keywords:
            keyword_analysis[keyword] = queries_df['query'].str.contains(keyword, case=False).sum()
            
        return {
            'avg_query_length': queries_df['query_length'].mean(),
            'keyword_frequency': keyword_analysis,
            'total_queries': len(queries_df)
        }
        
    def _calculate_performance_metrics(self, queries_df: pd.DataFrame) -> Dict:
        """Calcula métricas de performance"""
        metrics = {
            'total_queries': len(queries_df),
            'avg_results_per_query': queries_df['num_results'].mean(),
            'queries_with_quality_score': queries_df['quality_score'].notna().sum()
        }
        
        if 'quality_score' in queries_df.columns:
            quality_data = queries_df.dropna(subset=['quality_score'])
            if len(quality_data) > 0:
                metrics.update({
                    'avg_quality_score': quality_data['quality_score'].mean(),
                    'quality_std': quality_data['quality_score'].std(),
                    'high_quality_queries': (quality_data['quality_score'] >= 7.0).sum(),
                    'low_quality_queries': (quality_data['quality_score'] < 4.0).sum()
                })
                
        return metrics
        
    def learn_from_feedback(self) -> Dict:
        """Aprende com feedback dos usuários"""
        if len(self.learning_data['feedback']) < 5:
            return {'status': 'insufficient_feedback', 'message': 'Feedback insuficiente para aprendizado'}
            
        feedback_df = pd.DataFrame(self.learning_data['feedback'])
        
        # Aprende padrões de feedback
        learned_patterns = {
            'concept_feedback': self._learn_concept_feedback_patterns(feedback_df),
            'query_feedback': self._learn_query_feedback_patterns(feedback_df),
            'improvement_suggestions': self._generate_improvement_suggestions(feedback_df)
        }
        
        return learned_patterns
        
    def _learn_concept_feedback_patterns(self, feedback_df: pd.DataFrame) -> Dict:
        """Aprende padrões de feedback por conceito"""
        concept_feedback = feedback_df.groupby('concept_id').agg({
            'feedback_value': ['mean', 'count', 'std']
        }).round(3)
        
        concept_feedback.columns = ['avg_feedback', 'feedback_count', 'feedback_std']
        
        # Identifica conceitos com feedback consistentemente baixo
        low_feedback_concepts = concept_feedback[
            (concept_feedback['avg_feedback'] < 0.3) & 
            (concept_feedback['feedback_count'] >= 3)
        ]
        
        return {
            'concept_scores': concept_feedback.to_dict('index'),
            'low_feedback_concepts': low_feedback_concepts.to_dict('index'),
            'total_concepts_with_feedback': len(concept_feedback)
        }
        
    def _learn_query_feedback_patterns(self, feedback_df: pd.DataFrame) -> Dict:
        """Aprende padrões de feedback por query"""
        query_feedback = feedback_df.groupby('query').agg({
            'feedback_value': ['mean', 'count']
        }).round(3)
        
        query_feedback.columns = ['avg_feedback', 'feedback_count']
        
        return {
            'query_scores': query_feedback.to_dict('index'),
            'total_queries_with_feedback': len(query_feedback)
        }
        
    def _generate_improvement_suggestions(self, feedback_df: pd.DataFrame) -> List[str]:
        """Gera sugestões de melhoria baseadas no feedback"""
        suggestions = []
        
        # Analisa feedback por tipo
        feedback_by_type = feedback_df.groupby('feedback_type')['feedback_value'].mean()
        
        if 'relevance' in feedback_by_type and feedback_by_type['relevance'] < 0.5:
            suggestions.append("Melhorar algoritmo de relevância de conceitos")
            
        if 'accuracy' in feedback_by_type and feedback_by_type['accuracy'] < 0.5:
            suggestions.append("Melhorar precisão da tradução médica")
            
        # Analisa conceitos com feedback baixo
        low_feedback_concepts = feedback_df[feedback_df['feedback_value'] < 0.3]['concept_id'].value_counts()
        if len(low_feedback_concepts) > 0:
            suggestions.append(f"Revisar {len(low_feedback_concepts)} conceitos com feedback baixo")
            
        return suggestions
        
    def optimize_translation_dictionary(self) -> Dict:
        """Otimiza dicionário de tradução baseado no aprendizado"""
        if len(self.learning_data['queries']) < self.learning_params['min_samples_for_learning']:
            return {'status': 'insufficient_data'}
            
        # Analisa queries que resultaram em baixa qualidade
        low_quality_queries = [
            q for q in self.learning_data['queries'] 
            if q.get('quality_score', 0) < 4.0
        ]
        
        if not low_quality_queries:
            return {'status': 'no_improvements_needed'}
            
        # Extrai termos que podem precisar de melhor tradução
        translation_improvements = self._extract_translation_improvements(low_quality_queries)
        
        return {
            'translation_improvements': translation_improvements,
            'low_quality_queries_analyzed': len(low_quality_queries),
            'suggested_improvements': len(translation_improvements)
        }
        
    def _extract_translation_improvements(self, low_quality_queries: List[Dict]) -> List[Dict]:
        """Extrai melhorias de tradução de queries de baixa qualidade"""
        improvements = []
        
        for query_data in low_quality_queries:
            query = query_data['query']
            translated_query = self.medical_translator.translate_text(query)
            
            # Identifica palavras que podem precisar de melhor tradução
            query_words = query.lower().split()
            translated_words = translated_query.lower().split()
            
            for i, (pt_word, en_word) in enumerate(zip(query_words, translated_words)):
                if pt_word != en_word and pt_word not in self.medical_translator.translation_dict:
                    improvements.append({
                        'portuguese_term': pt_word,
                        'current_translation': en_word,
                        'context': query,
                        'quality_score': query_data.get('quality_score', 0)
                    })
                    
        return improvements
        
    def generate_learning_report(self) -> str:
        """Gera relatório de aprendizado contínuo"""
        trends = self.analyze_performance_trends()
        feedback_analysis = self.learn_from_feedback()
        translation_optimization = self.optimize_translation_dictionary()
        
        report = f"""
# Relatório de Aprendizado Contínuo

## 📊 Análise de Performance
- **Total de queries**: {trends.get('performance_metrics', {}).get('total_queries', 0)}
- **Queries com score de qualidade**: {trends.get('performance_metrics', {}).get('queries_with_quality_score', 0)}
- **Qualidade média**: {trends.get('performance_metrics', {}).get('avg_quality_score', 0):.2f}

## 📈 Tendências de Qualidade
"""
        
        if 'quality_trend' in trends and trends['quality_trend'].get('status') != 'no_quality_data':
            quality_trend = trends['quality_trend']
            report += f"""
- **Qualidade geral**: {quality_trend.get('overall_quality', 0):.2f}
- **Qualidade recente**: {quality_trend.get('recent_quality', 0):.2f}
- **Tendência**: {quality_trend.get('trend_direction', 'N/A')}
- **Melhoria**: {quality_trend.get('quality_improvement', 0):.2f}
"""
        
        report += f"""
## 🏥 Distribuição de Especialidades
"""
        
        if 'specialty_distribution' in trends and trends['specialty_distribution'].get('status') != 'no_specialty_data':
            specialty_dist = trends['specialty_distribution']
            report += f"- **Especialidade mais comum**: {specialty_dist.get('most_common', 'N/A')}\n"
            report += f"- **Total de especialidades**: {specialty_dist.get('total_specialties', 0)}\n"
            
            for specialty, count in specialty_dist.get('distribution', {}).items():
                report += f"  - {specialty}: {count} queries\n"
        
        report += f"""
## 🔄 Análise de Feedback
"""
        
        if feedback_analysis.get('status') != 'insufficient_feedback':
            report += f"- **Conceitos com feedback**: {feedback_analysis.get('concept_feedback', {}).get('total_concepts_with_feedback', 0)}\n"
            report += f"- **Queries com feedback**: {feedback_analysis.get('query_feedback', {}).get('total_queries_with_feedback', 0)}\n"
            
            suggestions = feedback_analysis.get('improvement_suggestions', [])
            if suggestions:
                report += "\n**Sugestões de melhoria:**\n"
                for suggestion in suggestions:
                    report += f"- {suggestion}\n"
        
        report += f"""
## 🔧 Otimização de Tradução
"""
        
        if translation_optimization.get('status') != 'insufficient_data':
            report += f"- **Queries de baixa qualidade analisadas**: {translation_optimization.get('low_quality_queries_analyzed', 0)}\n"
            report += f"- **Melhorias sugeridas**: {translation_optimization.get('suggested_improvements', 0)}\n"
        
        return report
