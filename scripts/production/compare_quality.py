"""
Comparação de Qualidade: Sistema Anterior vs Sistema Híbrido
Avalia melhoria na acurácia e qualidade
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.cached_pubmedbert_search import CachedPubMedBERTSearch
from src.core.enhanced_clinical_translator import EnhancedClinicalTranslator
import time
import json

def test_original_system():
    """Testa sistema original (sem tradutor aprimorado)"""
    print("🔍 Testando Sistema Original...")
    
    cached_search = CachedPubMedBERTSearch(cache_size=1000)
    cached_search.load_model()
    cached_search.load_index("data/indices/snomed_pubmedbert_large_index")
    
    test_cases = [
        {
            "query": "dor no peito",
            "expected_concepts": ["chest pain", "angina", "myocardial infarction"],
            "specialty": "cardiology"
        },
        {
            "query": "infarto do miocárdio", 
            "expected_concepts": ["myocardial infarction", "acute myocardial infarction", "heart attack"],
            "specialty": "cardiology"
        },
        {
            "query": "hipertensão arterial",
            "expected_concepts": ["hypertension", "arterial hypertension", "high blood pressure"],
            "specialty": "cardiology"
        },
        {
            "query": "falta de ar",
            "expected_concepts": ["shortness of breath", "dyspnea", "breathing difficulty"],
            "specialty": "pulmonology"
        },
        {
            "query": "diabetes mellitus",
            "expected_concepts": ["diabetes mellitus", "type 2 diabetes", "type 1 diabetes"],
            "specialty": "endocrinology"
        }
    ]
    
    results = []
    total_score = 0
    
    for case in test_cases:
        start_time = time.time()
        search_result = cached_search.search_with_cache(case['query'], specialty=case['specialty'], top_k=10)
        search_time = time.time() - start_time
        
        results_list = search_result.get('results', [])
        
        # Avalia resultados
        found_concepts = 0
        for result in results_list[:5]:
            term = result['term'].lower()
            for expected in case['expected_concepts']:
                if expected.lower() in term or term in expected.lower():
                    found_concepts += 1
                    break
                    
        case_score = found_concepts / len(case['expected_concepts'])
        total_score += case_score
        
        results.append({
            "query": case['query'],
            "score": case_score,
            "search_time": search_time,
            "found_concepts": found_concepts,
            "expected_concepts": len(case['expected_concepts'])
        })
    
    avg_score = total_score / len(test_cases)
    avg_time = sum(r['search_time'] for r in results) / len(results)
    
    return {
        "avg_score": avg_score,
        "avg_time": avg_time,
        "results": results
    }

def test_hybrid_system():
    """Testa sistema híbrido (com tradutor aprimorado)"""
    print("🔍 Testando Sistema Híbrido...")
    
    cached_search = CachedPubMedBERTSearch(cache_size=1000)
    cached_search.load_model()
    cached_search.load_index("data/indices/snomed_pubmedbert_large_index")
    
    translator = EnhancedClinicalTranslator()
    translator.load_models()
    translator.load_clinical_dictionaries("data")
    
    test_cases = [
        {
            "query": "dor no peito",
            "expected_concepts": ["chest pain", "angina", "myocardial infarction"],
            "specialty": "cardiology"
        },
        {
            "query": "infarto do miocárdio",
            "expected_concepts": ["myocardial infarction", "acute myocardial infarction", "heart attack"],
            "specialty": "cardiology"
        },
        {
            "query": "hipertensão arterial",
            "expected_concepts": ["hypertension", "arterial hypertension", "high blood pressure"],
            "specialty": "cardiology"
        },
        {
            "query": "falta de ar",
            "expected_concepts": ["shortness of breath", "dyspnea", "breathing difficulty"],
            "specialty": "pulmonology"
        },
        {
            "query": "diabetes mellitus",
            "expected_concepts": ["diabetes mellitus", "type 2 diabetes", "type 1 diabetes"],
            "specialty": "endocrinology"
        }
    ]
    
    results = []
    total_score = 0
    
    for case in test_cases:
        # Tradução aprimorada
        translation_result = translator.translate_clinical_text(case['query'], expand_synonyms=True)
        
        start_time = time.time()
        search_result = cached_search.search_with_cache(case['query'], specialty=case['specialty'], top_k=10)
        search_time = time.time() - start_time
        
        results_list = search_result.get('results', [])
        
        # Avalia resultados
        found_concepts = 0
        for result in results_list[:5]:
            term = result['term'].lower()
            for expected in case['expected_concepts']:
                if expected.lower() in term or term in expected.lower():
                    found_concepts += 1
                    break
                    
        case_score = found_concepts / len(case['expected_concepts'])
        total_score += case_score
        
        results.append({
            "query": case['query'],
            "translation": translation_result['base_translation'],
            "confidence": translation_result['confidence'],
            "score": case_score,
            "search_time": search_time,
            "found_concepts": found_concepts,
            "expected_concepts": len(case['expected_concepts'])
        })
    
    avg_score = total_score / len(test_cases)
    avg_time = sum(r['search_time'] for r in results) / len(results)
    
    return {
        "avg_score": avg_score,
        "avg_time": avg_time,
        "results": results
    }

def compare_systems():
    """Compara os dois sistemas"""
    print("🏥 Comparação de Qualidade: Sistema Anterior vs Sistema Híbrido")
    print("=" * 70)
    
    # Testa sistema original
    print("\n1️⃣ Testando Sistema Original...")
    original_results = test_original_system()
    
    # Testa sistema híbrido
    print("\n2️⃣ Testando Sistema Híbrido...")
    hybrid_results = test_hybrid_system()
    
    # Compara resultados
    print("\n📊 Comparação de Resultados:")
    print("=" * 50)
    
    print(f"📈 Score Médio:")
    print(f"   🖥️ Sistema Original: {original_results['avg_score']:.3f}")
    print(f"   🚀 Sistema Híbrido: {hybrid_results['avg_score']:.3f}")
    
    improvement = hybrid_results['avg_score'] - original_results['avg_score']
    improvement_pct = (improvement / original_results['avg_score']) * 100 if original_results['avg_score'] > 0 else 0
    
    print(f"   📊 Melhoria: {improvement:+.3f} ({improvement_pct:+.1f}%)")
    
    print(f"\n⏱️ Tempo Médio:")
    print(f"   🖥️ Sistema Original: {original_results['avg_time']:.3f}s")
    print(f"   🚀 Sistema Híbrido: {hybrid_results['avg_time']:.3f}s")
    
    time_diff = hybrid_results['avg_time'] - original_results['avg_time']
    print(f"   📊 Diferença: {time_diff:+.3f}s")
    
    # Análise detalhada por query
    print(f"\n📋 Análise Detalhada por Query:")
    print("   Query | Original | Híbrido | Melhoria")
    print("   " + "-" * 50)
    
    for i, orig_result in enumerate(original_results['results']):
        hybrid_result = hybrid_results['results'][i]
        query = orig_result['query']
        orig_score = orig_result['score']
        hybrid_score = hybrid_result['score']
        improvement = hybrid_score - orig_score
        
        print(f"   {query[:15]:15} | {orig_score:.3f} | {hybrid_score:.3f} | {improvement:+.3f}")
    
    # Avalia qualidade
    print(f"\n🎯 Avaliação de Qualidade:")
    if hybrid_results['avg_score'] >= 0.8:
        print(f"   ✅ Sistema Híbrido: QUALIDADE EXCELENTE (≥8/10)")
    elif hybrid_results['avg_score'] >= 0.6:
        print(f"   ✅ Sistema Híbrido: BOA QUALIDADE (6-8/10)")
    else:
        print(f"   ⚠️ Sistema Híbrido: PRECISA MELHORAR (<6/10)")
        
    if improvement > 0.1:
        print(f"   🎉 MELHORIA SIGNIFICATIVA: +{improvement:.3f}")
    elif improvement > 0.05:
        print(f"   ✅ MELHORIA MODERADA: +{improvement:.3f}")
    elif improvement > 0:
        print(f"   📈 MELHORIA PEQUENA: +{improvement:.3f}")
    else:
        print(f"   ⚠️ SEM MELHORIA: {improvement:.3f}")
    
    # Salva relatório
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "original_system": original_results,
        "hybrid_system": hybrid_results,
        "comparison": {
            "score_improvement": improvement,
            "score_improvement_pct": improvement_pct,
            "time_difference": time_diff,
            "hybrid_quality": "EXCELLENT" if hybrid_results['avg_score'] >= 0.8 else "GOOD" if hybrid_results['avg_score'] >= 0.6 else "NEEDS_IMPROVEMENT"
        }
    }
    
    report_file = "data/reports/system_comparison_report.json"
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    print(f"\n💾 Relatório salvo em: {report_file}")
    
    return report

def main():
    """Função principal"""
    print("🔬 Comparação de Qualidade: Sistema Anterior vs Sistema Híbrido")
    print("=" * 70)
    
    report = compare_systems()
    
    print("\n" + "=" * 70)
    print("📋 Resumo Final:")
    print(f"   🖥️ Sistema Original: {report['original_system']['avg_score']:.3f}")
    print(f"   🚀 Sistema Híbrido: {report['hybrid_system']['avg_score']:.3f}")
    print(f"   📊 Melhoria: {report['comparison']['score_improvement']:+.3f}")
    print(f"   🎯 Qualidade: {report['comparison']['hybrid_quality']}")
    
    if report['comparison']['hybrid_quality'] == "EXCELLENT":
        print("\n🎉 SUCESSO! Sistema híbrido atingiu qualidade excelente!")
        print("✅ Melhoria significativa na acurácia!")
    elif report['comparison']['score_improvement'] > 0:
        print("\n✅ Sistema híbrido mostra melhoria!")
        print("📈 Qualidade melhorada com tradutor aprimorado!")
    else:
        print("\n⚠️ Sistema híbrido precisa de ajustes")
        print("🔧 Considere otimizar parâmetros")

if __name__ == "__main__":
    main()
