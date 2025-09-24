"""
Teste Simplificado do Sistema Híbrido
Usa índices existentes para testar a qualidade
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.cached_pubmedbert_search import CachedPubMedBERTSearch
from src.core.enhanced_clinical_translator import EnhancedClinicalTranslator
import time
import json

def test_hybrid_quality_simple():
    """Teste simplificado de qualidade usando sistema existente"""
    print("🧪 Teste Simplificado de Qualidade - Sistema Híbrido")
    print("=" * 60)
    
    try:
        # 1. Inicializa sistema existente (que já funciona)
        print("1️⃣ Inicializando Sistema Existente...")
        cached_search = CachedPubMedBERTSearch(cache_size=1000)
        cached_search.load_model()
        
        # Carrega índice existente
        index_path = "data/indices/snomed_pubmedbert_large_index"
        if not cached_search.load_index(index_path):
            print(f"❌ Índice não encontrado em: {index_path}")
            return False
            
        print("✅ Sistema existente carregado!")
        
        # 2. Inicializa tradutor aprimorado
        print("\n2️⃣ Inicializando Tradutor Aprimorado...")
        translator = EnhancedClinicalTranslator()
        translator.load_models()
        translator.load_clinical_dictionaries("data")
        
        # 3. Testa com casos médicos
        print("\n3️⃣ Testando Qualidade...")
        
        test_cases = [
            {
                "query": "dor no peito",
                "expected_concepts": ["chest pain", "angina", "myocardial infarction", "precordial pain"],
                "specialty": "cardiology",
                "min_expected": 2
            },
            {
                "query": "infarto do miocárdio",
                "expected_concepts": ["myocardial infarction", "acute myocardial infarction", "heart attack"],
                "specialty": "cardiology",
                "min_expected": 2
            },
            {
                "query": "hipertensão arterial",
                "expected_concepts": ["hypertension", "arterial hypertension", "high blood pressure"],
                "specialty": "cardiology",
                "min_expected": 2
            },
            {
                "query": "falta de ar",
                "expected_concepts": ["shortness of breath", "dyspnea", "breathing difficulty"],
                "specialty": "pulmonology",
                "min_expected": 2
            },
            {
                "query": "diabetes mellitus",
                "expected_concepts": ["diabetes mellitus", "type 2 diabetes", "type 1 diabetes"],
                "specialty": "endocrinology",
                "min_expected": 2
            }
        ]
        
        total_score = 0
        detailed_results = []
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n{i}. Teste: '{case['query']}' (especialidade: {case['specialty']})")
            
            # Testa tradução aprimorada
            translation_result = translator.translate_clinical_text(case['query'], expand_synonyms=True)
            print(f"   🌐 Traduzido: '{translation_result['base_translation']}'")
            print(f"   📊 Confiança: {translation_result['confidence']:.2f}")
            
            # Testa busca com sistema existente
            start_time = time.time()
            search_result = cached_search.search_with_cache(case['query'], specialty=case['specialty'], top_k=10)
            search_time = time.time() - start_time
            
            # Extrai resultados da busca
            results = search_result.get('results', [])
            
            # Avalia resultados
            found_concepts = 0
            found_terms = []
            
            for result in results[:5]:  # Top 5
                term = result['term'].lower()
                for expected in case['expected_concepts']:
                    if expected.lower() in term or term in expected.lower():
                        found_concepts += 1
                        found_terms.append(result['term'])
                        break
                        
            # Calcula score do caso
            case_score = found_concepts / len(case['expected_concepts'])
            total_score += case_score
            
            # Armazena resultado detalhado
            detailed_result = {
                "query": case['query'],
                "specialty": case['specialty'],
                "translation": translation_result['base_translation'],
                "confidence": translation_result['confidence'],
                "found_concepts": found_concepts,
                "expected_concepts": len(case['expected_concepts']),
                "case_score": case_score,
                "search_time": search_time,
                "found_terms": found_terms[:3],  # Top 3
                "all_results": [r['term'] for r in results[:5]]
            }
            detailed_results.append(detailed_result)
            
            print(f"   📊 Score: {case_score:.2f} ({found_concepts}/{len(case['expected_concepts'])} conceitos)")
            print(f"   ⏱️ Tempo: {search_time:.3f}s")
            print(f"   🎯 Encontrados: {', '.join(found_terms[:3])}")
            
            # Mostra top 3 resultados
            for j, result in enumerate(results[:3]):
                score = result.get('similarity_score', 0)
                term = result['term']
                print(f"   {j+1}. {term} (score: {score:.3f})")
        
        # Calcula score final
        final_score = total_score / len(test_cases)
        
        print(f"\n📊 Resultados Finais:")
        print(f"   📈 Score Médio: {final_score:.2f}/1.0")
        print(f"   🎯 Casos Testados: {len(test_cases)}")
        print(f"   ⏱️ Tempo Médio: {sum(r['search_time'] for r in detailed_results) / len(detailed_results):.3f}s")
        
        # Avalia qualidade
        if final_score >= 0.8:
            print(f"\n🎉 SUCESSO! Sistema atingiu qualidade ≥8/10!")
            print(f"✅ Score: {final_score:.2f} (≥0.8)")
        elif final_score >= 0.6:
            print(f"\n✅ Sistema com boa qualidade")
            print(f"📊 Score: {final_score:.2f} (0.6-0.8)")
        else:
            print(f"\n⚠️ Sistema precisa de melhorias")
            print(f"📊 Score: {final_score:.2f} (<0.6)")
            
        # Salva resultados
        results_file = "data/reports/simple_hybrid_test_results.json"
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "final_score": final_score,
                "total_cases": len(test_cases),
                "detailed_results": detailed_results
            }, f, indent=2, ensure_ascii=False)
            
        print(f"\n💾 Resultados salvos em: {results_file}")
        
        return final_score >= 0.8
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    print("🏥 Teste Simplificado de Qualidade - Sistema Híbrido")
    print("=" * 60)
    
    success = test_hybrid_quality_simple()
    
    if success:
        print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print("✅ Sistema atingiu qualidade ≥8/10")
        print("🚀 Sistema híbrido funcionando!")
    else:
        print("\n⚠️ TESTE CONCLUÍDO COM LIMITAÇÕES")
        print("📈 Sistema testado, mas não atingiu ≥8/10")
        print("🔧 Considere ajustar parâmetros")

if __name__ == "__main__":
    main()
