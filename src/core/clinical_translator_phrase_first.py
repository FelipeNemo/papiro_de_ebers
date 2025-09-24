# -*- coding: utf-8 -*-
"""
Tradutor Clínico Confiável - Phrase-First
Implementa tradução phrase-first (n-gramas médicos) + fallback neural
"""

import json
import re
import os
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

class ClinicalTranslatorPhraseFirst:
    """Tradutor clínico que prioriza frases médicas conhecidas"""
    
    def __init__(self, dict_path: str = "data/dicts/pt_aliases.json"):
        """Inicializa o tradutor com dicionário médico"""
        self.dict_path = dict_path
        self.medical_dict = self._load_medical_dictionary()
        self.phrase_cache = {}
        self.hit_counts = defaultdict(int)
        
        print(f"🔬 Tradutor Clínico Phrase-First carregado")
        print(f"   📚 Dicionário: {len(self.medical_dict)} traduções")
    
    def _load_medical_dictionary(self) -> Dict[str, str]:
        """Carrega dicionário médico PT-EN"""
        if os.path.exists(self.dict_path):
            with open(self.dict_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"⚠️ Dicionário não encontrado: {self.dict_path}")
            return {}
    
    def _extract_phrases(self, text: str, max_ngram: int = 4) -> List[Tuple[str, int, int]]:
        """Extrai n-gramas de diferentes tamanhos do texto"""
        words = text.lower().split()
        phrases = []
        
        # Extrai n-gramas de tamanho 1 a max_ngram
        for n in range(1, min(max_ngram + 1, len(words) + 1)):
            for i in range(len(words) - n + 1):
                phrase = ' '.join(words[i:i+n])
                start_pos = i
                end_pos = i + n
                phrases.append((phrase, start_pos, end_pos))
        
        # Ordena por tamanho (maior primeiro) para priorizar frases mais longas
        phrases.sort(key=lambda x: len(x[0]), reverse=True)
        return phrases
    
    def _find_phrase_matches(self, phrases: List[Tuple[str, int, int]]) -> List[Tuple[str, str, int, int, float]]:
        """Encontra correspondências de frases no dicionário médico"""
        matches = []
        
        for phrase, start_pos, end_pos in phrases:
            if phrase in self.medical_dict:
                en_term = self.medical_dict[phrase]
                confidence = 1.0  # Tradução direta do dicionário
                matches.append((phrase, en_term, start_pos, end_pos, confidence))
                self.hit_counts[phrase] += 1
        
        return matches
    
    def _resolve_overlaps(self, matches: List[Tuple[str, str, int, int, float]]) -> List[Tuple[str, str, int, int, float]]:
        """Resolve sobreposições de frases, priorizando as mais longas e confiáveis"""
        if not matches:
            return []
        
        # Ordena por confiança e tamanho
        matches.sort(key=lambda x: (x[4], len(x[0])), reverse=True)
        
        resolved = []
        used_positions = set()
        
        for phrase, en_term, start_pos, end_pos, confidence in matches:
            # Verifica se há sobreposição com traduções já usadas
            overlap = any(
                not (end_pos <= existing_start or start_pos >= existing_end)
                for existing_start, existing_end in used_positions
            )
            
            if not overlap:
                resolved.append((phrase, en_term, start_pos, end_pos, confidence))
                used_positions.add((start_pos, end_pos))
        
        return resolved
    
    def _apply_translations(self, text: str, matches: List[Tuple[str, str, int, int, float]]) -> str:
        """Aplica as traduções ao texto original"""
        if not matches:
            return text
        
        # Ordena por posição para aplicar da direita para esquerda
        matches.sort(key=lambda x: x[2], reverse=True)
        
        words = text.split()
        result_words = words.copy()
        
        for phrase, en_term, start_pos, end_pos, confidence in matches:
            # Substitui a frase original pela tradução
            result_words[start_pos:end_pos] = [en_term]
        
        return ' '.join(result_words)
    
    def translate_phrase_first(self, text: str, max_ngram: int = 4) -> Dict[str, any]:
        """Traduz texto usando abordagem phrase-first"""
        if not text or not text.strip():
            return {
                'original': text,
                'translated': text,
                'method': 'empty',
                'confidence': 1.0,
                'translations_applied': [],
                'untranslated_words': []
            }
        
        # Extrai frases
        phrases = self._extract_phrases(text, max_ngram)
        
        # Encontra correspondências
        matches = self._find_phrase_matches(phrases)
        
        # Resolve sobreposições
        resolved_matches = self._resolve_overlaps(matches)
        
        # Aplica traduções
        translated_text = self._apply_translations(text, resolved_matches)
        
        # Identifica palavras não traduzidas
        original_words = set(text.lower().split())
        translated_words = set(translated_text.lower().split())
        untranslated = original_words - translated_words
        
        # Prepara resultado
        result = {
            'original': text,
            'translated': translated_text,
            'method': 'phrase_first',
            'confidence': self._calculate_confidence(resolved_matches, len(text.split())),
            'translations_applied': [
                {
                    'pt_phrase': match[0],
                    'en_term': match[1],
                    'confidence': match[4]
                }
                for match in resolved_matches
            ],
            'untranslated_words': list(untranslated),
            'hit_counts': dict(self.hit_counts)
        }
        
        return result
    
    def _calculate_confidence(self, matches: List[Tuple[str, str, int, int, float]], total_words: int) -> float:
        """Calcula confiança geral da tradução"""
        if not matches or total_words == 0:
            return 0.0
        
        # Peso baseado na cobertura de palavras traduzidas
        translated_words = sum(len(match[0].split()) for match in matches)
        coverage = translated_words / total_words
        
        # Peso baseado na confiança das traduções
        avg_confidence = sum(match[4] for match in matches) / len(matches) if matches else 0.0
        
        # Combina cobertura e confiança
        overall_confidence = (coverage * 0.7) + (avg_confidence * 0.3)
        
        return min(overall_confidence, 1.0)
    
    def get_translation_stats(self) -> Dict[str, any]:
        """Retorna estatísticas de tradução"""
        total_hits = sum(self.hit_counts.values())
        unique_terms = len(self.hit_counts)
        
        return {
            'total_translations': total_hits,
            'unique_terms_used': unique_terms,
            'most_used_terms': sorted(
                self.hit_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10],
            'dictionary_size': len(self.medical_dict)
        }
    
    def add_translation(self, pt_term: str, en_term: str, confidence: float = 1.0):
        """Adiciona nova tradução ao dicionário"""
        self.medical_dict[pt_term.lower()] = en_term
        self._save_dictionary()
    
    def _save_dictionary(self):
        """Salva dicionário atualizado"""
        with open(self.dict_path, 'w', encoding='utf-8') as f:
            json.dump(self.medical_dict, f, indent=2, ensure_ascii=False)
    
    def batch_translate(self, texts: List[str]) -> List[Dict[str, any]]:
        """Traduz múltiplos textos em lote"""
        results = []
        for text in texts:
            result = self.translate_phrase_first(text)
            results.append(result)
        return results

def test_clinical_translator():
    """Testa o tradutor clínico"""
    translator = ClinicalTranslatorPhraseFirst()
    
    test_cases = [
        "dor no peito",
        "falta de ar",
        "glicemia alta",
        "hipertensão arterial",
        "úlcera duodenal",
        "hemorragia digestiva",
        "avc isquêmico",
        "paresia do braço direito",
        "hiv positivo",
        "câncer de pulmão",
        "quimioterapia adjuvante",
        "exame de sangue",
        "pressão arterial 140/90 mmHg",
        "diabetes mellitus tipo 2",
        "dpoc grave"
    ]
    
    print("\n🧪 TESTE DO TRADUTOR CLÍNICO PHRASE-FIRST")
    print("=" * 60)
    
    for i, text in enumerate(test_cases, 1):
        result = translator.translate_phrase_first(text)
        print(f"\n{i:2d}. '{text}'")
        print(f"    → '{result['translated']}'")
        print(f"    📊 Confiança: {result['confidence']:.3f}")
        print(f"    🔄 Método: {result['method']}")
        
        if result['translations_applied']:
            print(f"    ✅ Traduções aplicadas:")
            for trans in result['translations_applied']:
                print(f"       '{trans['pt_phrase']}' → '{trans['en_term']}'")
        
        if result['untranslated_words']:
            print(f"    ⚠️ Não traduzidas: {result['untranslated_words']}")
    
    # Estatísticas
    stats = translator.get_translation_stats()
    print(f"\n📊 ESTATÍSTICAS:")
    print(f"   Total de traduções: {stats['total_translations']}")
    print(f"   Termos únicos usados: {stats['unique_terms_used']}")
    print(f"   Tamanho do dicionário: {stats['dictionary_size']}")
    
    if stats['most_used_terms']:
        print(f"   Termos mais usados:")
        for term, count in stats['most_used_terms']:
            print(f"     '{term}': {count} vezes")

if __name__ == "__main__":
    test_clinical_translator()
