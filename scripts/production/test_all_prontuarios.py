"""
Teste Completo do Sistema com Todos os Prontuários
Inclui prontuários originais (1-3) e novos prontuários (4-7)
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.cached_pubmedbert_search import CachedPubMedBERTSearch
from src.core.enhanced_clinical_translator import EnhancedClinicalTranslator
import time
import json
import re
from datetime import datetime

def extract_medical_terms(text):
    """Extrai termos médicos relevantes do prontuário"""
    # Padrões para identificar termos médicos
    patterns = [
        r'\b[A-Z]{2,}\b',  # Siglas médicas
        r'\b\w+ite\b',     # Terminações -ite
        r'\b\w+ose\b',     # Terminações -ose
        r'\b\w+emia\b',    # Terminações -emia
        r'\b\w+patia\b',   # Terminações -patia
        r'\b\w+algia\b',   # Terminações -algia
        r'\b\w+uria\b',    # Terminações -uria
        r'\bdiabetes\b',   # Diabetes
        r'\bhipertens[ãa]o\b',  # Hipertensão
        r'\binfarto\b',    # Infarto
        r'\binsufici[êe]ncia\b',  # Insuficiência
        r'\bneoplasia\b',  # Neoplasia
        r'\bcarcinoma\b',  # Carcinoma
        r'\badenocarcinoma\b',  # Adenocarcinoma
        r'\bcelulite\b',   # Celulite
        r'\bAVC\b',        # AVC
        r'\bAVCi\b',       # AVCi
        r'\bHAS\b',        # HAS
        r'\bDM\b',         # DM
        r'\bDPOC\b',       # DPOC
        r'\bHIV\b',        # HIV
        r'\bAIDS\b',       # AIDS
        r'\bTARV\b',       # TARV
        r'\bHDB\b',        # HDB
        r'\bEVAR\b',       # EVAR
        r'\bTC\b',         # TC
        r'\bRM\b',         # RM
        r'\bEEG\b',        # EEG
        r'\bUS\b',         # US
        r'\bHGT\b',        # HGT
        r'\bPCR\b',        # PCR
        r'\bCD4\b',        # CD4
        r'\bCV\b',         # CV
        r'\bNIHSS\b',      # NIHSS
        r'\bTOAST\b',      # TOAST
    ]
    
    terms = set()
    text_lower = text.lower()
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower, re.IGNORECASE)
        terms.update(matches)
    
    # Remove termos muito comuns
    common_terms = {'de', 'da', 'do', 'em', 'na', 'no', 'com', 'para', 'por', 'que', 'se', 'ao', 'nao', 'sem'}
    terms = {term for term in terms if term not in common_terms and len(term) > 2}
    
    return list(terms)

def analyze_prontuario(file_path, prontuario_id):
    """Analisa um prontuário específico"""
    print(f"\n{'='*60}")
    print(f"📋 PRONTUÁRIO {prontuario_id}: {os.path.basename(file_path)}")
    print(f"{'='*60}")
    
    # Lê o prontuário
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"📄 Conteúdo ({len(content)} caracteres):")
    print(f"   {content[:200]}...")
    
    # Extrai termos médicos
    medical_terms = extract_medical_terms(content)
    print(f"\n🔍 Termos médicos identificados ({len(medical_terms)}):")
    for i, term in enumerate(medical_terms[:10], 1):  # Mostra apenas os primeiros 10
        print(f"   {i}. {term}")
    if len(medical_terms) > 10:
        print(f"   ... e mais {len(medical_terms) - 10} termos")
    
    # Testa busca para cada termo
    results = []
    total_time = 0
    
    print(f"\n🔍 Testando busca para {len(medical_terms)} termos...")
    
    for i, term in enumerate(medical_terms[:5], 1):  # Testa apenas os primeiros 5 termos
        print(f"\n   {i}. Testando: '{term}'")
        
        try:
            start_time = time.time()
            search_result = cached_search.search_with_cache(term, top_k=5)
            search_time = time.time() - start_time
            total_time += search_time
            
            results_list = search_result.get('results', [])
            
            print(f"      ⏱️ Tempo: {search_time:.3f}s")
            print(f"      🎯 Resultados: {len(results_list)}")
            
            if results_list:
                print(f"      📋 Top 3:")
                for j, result in enumerate(results_list[:3], 1):
                    score = result.get('similarity_score', result.get('score', 0.0))
                    term_text = result.get('term', result.get('preferredTerm', 'N/A'))
                    print(f"         {j}. {term_text} (score: {score:.3f})")
            else:
                print(f"      ❌ Nenhum resultado encontrado")
            
            results.append({
                'term': term,
                'search_time': search_time,
                'results_count': len(results_list),
                'top_results': [r.get('term', r.get('preferredTerm', 'N/A')) for r in results_list[:3]],
                'scores': [r.get('similarity_score', r.get('score', 0.0)) for r in results_list[:3]]
            })
            
        except Exception as e:
            print(f"      ❌ Erro na busca: {e}")
            results.append({
                'term': term,
                'error': str(e),
                'search_time': 0,
                'results_count': 0
            })
    
    # Calcula métricas
    successful_searches = [r for r in results if 'error' not in r]
    avg_time = total_time / len(successful_searches) if successful_searches else 0
    avg_results = sum(r['results_count'] for r in successful_searches) / len(successful_searches) if successful_searches else 0
    
    print(f"\n📊 Resumo do Prontuário {prontuario_id}:")
    print(f"   🔍 Termos testados: {len(successful_searches)}")
    print(f"   ⏱️ Tempo médio: {avg_time:.3f}s")
    print(f"   🎯 Resultados médios: {avg_results:.1f}")
    print(f"   ✅ Sucessos: {len(successful_searches)}/{len(results)}")
    
    return {
        'prontuario_id': prontuario_id,
        'file_path': file_path,
        'content_length': len(content),
        'medical_terms_count': len(medical_terms),
        'terms_tested': len(successful_searches),
        'avg_search_time': avg_time,
        'avg_results': avg_results,
        'success_rate': len(successful_searches) / len(results) if results else 0,
        'results': results
    }

def main():
    """Função principal"""
    print("🏥 TESTE COMPLETO DO SISTEMA COM TODOS OS PRONTUÁRIOS")
    print("=" * 70)
    
    # Inicializa sistema
    print("1️⃣ Inicializando Sistema...")
    global cached_search
    cached_search = CachedPubMedBERTSearch(cache_size=1000)
    cached_search.load_model()
    cached_search.load_index("data/final_indices/snomed_pubmedbert_index")
    
    # Inicializa tradutor
    print("2️⃣ Inicializando Tradutor...")
    translator = EnhancedClinicalTranslator()
    translator.load_models()
    translator.load_clinical_dictionaries("data")
    
    print("✅ Sistema carregado com sucesso!")
    
    # Lista de prontuários para testar
    prontuarios = [
        ("data/test/exemplo_prontuario_1.txt", 1, "Cardiológico - Infarto agudo"),
        ("data/test/exemplo_prontuario_2.txt", 2, "Pneumológico - DPOC"),
        ("data/test/exemplo_prontuario_3.txt", 3, "Gastroenterológico - Hemorragia"),
        ("data/test/exemplo_prontuario_4.txt", 4, "Neurológico - Síndrome sensitivo-motora"),
        ("data/test/exemplo_prontuario_5.txt", 5, "Oncológico - Adenocarcinoma esôfago"),
        ("data/test/exemplo_prontuario_6.txt", 6, "Infectológico - HIV + Celulite"),
        ("data/test/exemplo_prontuario_7.txt", 7, "Neurológico - AVCi")
    ]
    
    # Testa cada prontuário
    all_results = []
    total_start_time = time.time()
    
    for file_path, prontuario_id, description in prontuarios:
        if os.path.exists(file_path):
            print(f"\n🔍 Testando Prontuário {prontuario_id}: {description}")
            result = analyze_prontuario(file_path, prontuario_id)
            all_results.append(result)
        else:
            print(f"\n❌ Prontuário {prontuario_id} não encontrado: {file_path}")
    
    total_time = time.time() - total_start_time
    
    # Relatório final
    print(f"\n{'='*70}")
    print("📊 RELATÓRIO FINAL - TODOS OS PRONTUÁRIOS")
    print(f"{'='*70}")
    
    print(f"📋 Prontuários testados: {len(all_results)}")
    print(f"⏱️ Tempo total: {total_time:.2f}s")
    
    if all_results:
        # Métricas gerais
        total_terms = sum(r['medical_terms_count'] for r in all_results)
        total_tested = sum(r['terms_tested'] for r in all_results)
        avg_time_all = sum(r['avg_search_time'] for r in all_results) / len(all_results)
        avg_results_all = sum(r['avg_results'] for r in all_results) / len(all_results)
        avg_success_rate = sum(r['success_rate'] for r in all_results) / len(all_results)
        
        print(f"🔍 Total de termos médicos: {total_terms}")
        print(f"🧪 Termos testados: {total_tested}")
        print(f"⏱️ Tempo médio por busca: {avg_time_all:.3f}s")
        print(f"🎯 Resultados médios: {avg_results_all:.1f}")
        print(f"✅ Taxa de sucesso: {avg_success_rate:.1%}")
        
        # Resumo por prontuário
        print(f"\n📋 Resumo por Prontuário:")
        print("   ID | Especialidade | Termos | Testados | Tempo | Sucesso")
        print("   " + "-" * 60)
        
        for result in all_results:
            print(f"   {result['prontuario_id']:2d} | {prontuarios[result['prontuario_id']-1][2][:15]:15} | {result['medical_terms_count']:6d} | {result['terms_tested']:8d} | {result['avg_search_time']:5.3f}s | {result['success_rate']:6.1%}")
        
        # Avaliação de qualidade
        print(f"\n🎯 Avaliação de Qualidade:")
        if avg_success_rate >= 0.8:
            print(f"   ✅ EXCELENTE: Taxa de sucesso {avg_success_rate:.1%}")
        elif avg_success_rate >= 0.6:
            print(f"   ✅ BOA: Taxa de sucesso {avg_success_rate:.1%}")
        else:
            print(f"   ⚠️ PRECISA MELHORAR: Taxa de sucesso {avg_success_rate:.1%}")
        
        if avg_time_all <= 0.1:
            print(f"   ✅ PERFORMANCE EXCELENTE: {avg_time_all:.3f}s por busca")
        elif avg_time_all <= 0.5:
            print(f"   ✅ PERFORMANCE BOA: {avg_time_all:.3f}s por busca")
        else:
            print(f"   ⚠️ PERFORMANCE LENTA: {avg_time_all:.3f}s por busca")
    
    # Salva relatório
    report = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'total_prontuarios': len(all_results),
        'total_time': total_time,
        'metrics': {
            'total_terms': total_terms if all_results else 0,
            'total_tested': total_tested if all_results else 0,
            'avg_search_time': avg_time_all if all_results else 0,
            'avg_results': avg_results_all if all_results else 0,
            'success_rate': avg_success_rate if all_results else 0
        },
        'prontuarios': all_results
    }
    
    report_file = "data/final_reports/all_prontuarios_test_results.json"
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Relatório salvo em: {report_file}")
    
    print(f"\n🎉 TESTE CONCLUÍDO!")
    print(f"✅ Sistema testado com {len(all_results)} prontuários")
    print(f"🚀 Performance: {avg_time_all:.3f}s por busca")
    print(f"🎯 Qualidade: {avg_success_rate:.1%} de sucesso")

if __name__ == "__main__":
    main()
