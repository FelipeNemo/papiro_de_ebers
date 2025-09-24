# -*- coding: utf-8 -*-
"""
Teste Rápido das Melhorias P1
Testa apenas alguns termos críticos para verificar as melhorias
"""

import os
import sys
import time

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.hybrid_search_improved import HybridSearchImproved

def quick_test_improvements():
    """Teste rápido das melhorias implementadas"""
    print("🚀 TESTE RÁPIDO DAS MELHORIAS P1")
    print("=" * 50)
    
    # Inicializa sistema
    print("1️⃣ Carregando sistema melhorado...")
    hybrid_search = HybridSearchImproved()
    hybrid_search.load_models()
    print("✅ Sistema carregado!")
    
    # Testa apenas termos críticos
    test_terms = [
        "dor no peito",
        "falta de ar", 
        "glicemia alta",
        "hipertensão arterial",
        "dpoc",
        "avc",
        "úlcera duodenal"
    ]
    
    print(f"\n2️⃣ Testando {len(test_terms)} termos críticos...")
    
    results = []
    for i, term in enumerate(test_terms, 1):
        print(f"\n   {i}. Testando: '{term}'")
        
        try:
            start_time = time.time()
            search_result = hybrid_search.search_hybrid(term, top_k=3)
            search_time = time.time() - start_time
            
            results_list = search_result.get('results', [])
            
            print(f"      ⏱️ Tempo: {search_time:.3f}s")
            print(f"      🎯 Resultados: {len(results_list)}")
            print(f"      🔄 Traduzido: '{search_result.get('translated_query', '')}'")
            print(f"      📊 Confiança tradução: {search_result.get('translation_confidence', 0):.3f}")
            
            if results_list:
                print(f"      📋 Top 3 resultados:")
                for j, result in enumerate(results_list[:3], 1):
                    result_text = result.get('term', 'N/A')
                    score = result.get('similarity_score', 0.0)
                    method = result.get('method', 'unknown')
                    rule_bonus = result.get('rule_bonus', 0.0)
                    print(f"         {j}. {result_text}")
                    print(f"            Score: {score:.3f}, Método: {method}, Bônus: {rule_bonus:.3f}")
            else:
                print(f"      ❌ Nenhum resultado encontrado")
            
            results.append({
                'term': term,
                'search_time': search_time,
                'results_count': len(results_list),
                'translation_confidence': search_result.get('translation_confidence', 0),
                'translated_query': search_result.get('translated_query', '')
            })
            
        except Exception as e:
            print(f"      ❌ Erro: {e}")
            results.append({
                'term': term,
                'error': str(e)
            })
    
    # Análise rápida
    print(f"\n{'='*50}")
    print("📊 ANÁLISE RÁPIDA DAS MELHORIAS")
    print(f"{'='*50}")
    
    successful_tests = [r for r in results if 'error' not in r and r.get('results_count', 0) > 0]
    total_tests = len(results)
    success_rate = len(successful_tests) / total_tests if total_tests > 0 else 0
    
    print(f"📋 Total de testes: {total_tests}")
    print(f"✅ Testes com resultados: {len(successful_tests)}")
    print(f"📊 Taxa de sucesso: {success_rate:.1%}")
    
    # Análise de tradução
    translation_confidences = [r.get('translation_confidence', 0) for r in results if 'translation_confidence' in r]
    if translation_confidences:
        avg_translation_conf = sum(translation_confidences) / len(translation_confidences)
        print(f"🔤 Confiança média de tradução: {avg_translation_conf:.3f}")
    
    # Análise de tempo
    search_times = [r.get('search_time', 0) for r in results if 'search_time' in r]
    if search_times:
        avg_time = sum(search_times) / len(search_times)
        print(f"⏱️ Tempo médio de busca: {avg_time:.3f}s")
    
    print(f"\n🎯 RESULTADO:")
    if success_rate >= 0.8:
        print(f"   ✅ EXCELENTE: {success_rate:.1%} de sucesso")
    elif success_rate >= 0.6:
        print(f"   ✅ BOM: {success_rate:.1%} de sucesso")
    elif success_rate >= 0.4:
        print(f"   ⚠️ REGULAR: {success_rate:.1%} de sucesso")
    else:
        print(f"   ❌ RUIM: {success_rate:.1%} de sucesso")
    
    return results

if __name__ == "__main__":
    quick_test_improvements()
