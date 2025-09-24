# -*- coding: utf-8 -*-
"""
Validação Incremental de Relevância Clínica
Analisa os resultados dos 7 prontuários com critérios rigorosos
"""

import json
import os
import sys
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def analyze_clinical_relevance(term, results, category, expected_terms):
    """Analisa relevância clínica com critérios rigorosos"""
    if not results:
        return {'relevant': False, 'reason': 'No results', 'score': 0.0, 'confidence': 0.0}
    
    relevant_count = 0
    total_score = 0
    best_score = 0
    best_match = ''
    
    for result in results:
        result_text = result['text'].lower()
        score = result.get('score', 0.0)
        
        contains_expected = any(expected in result_text for expected in expected_terms)
        
        if contains_expected:
            relevant_count += 1
            total_score += score
            if score > best_score:
                best_score = score
                best_match = result_text
    
    relevance_ratio = relevant_count / len(results)
    avg_score = total_score / len(results)
    
    #Critérios rigorosos
    is_relevant = (
        relevance_ratio >= 0.5 and
        avg_score >= 0.6 and
        best_score >= 0.7
    )
    
    confidence = (relevance_ratio * 0.4 + (avg_score / 1.0) * 0.3 + (best_score / 1.0) * 0.3)
    
    return {
        'relevant': is_relevant,
        'reason': f'Relevant: {relevant_count}/{len(results)} results, avg: {avg_score:.3f}, best: {best_score:.3f}' if is_relevant else f'Not relevant: {relevant_count}/{len(results)} results, avg: {avg_score:.3f}, best: {best_score:.3f}',
        'score': best_score,
        'avg_score': avg_score,
        'confidence': confidence,
        'relevance_ratio': relevance_ratio,
        'best_match': best_match
    }

def main():
    # Carrega os resultados existentes
    with open('data/final_reports/all_prontuarios_test_results.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print('🔍 VALIDAÇÃO INCREMENTAL DE RELEVÂNCIA CLÍNICA')
    print('=' * 60)

    # Dicionário de termos médicos esperados por categoria
    medical_terms_expected = {
        'cardiology': ['glucose', 'blood glucose', 'infarction', 'myocardial', 'hypertension', 'blood pressure', 'pain', 'chest', 'acute', 'diabetes', 'mellitus'],
        'pulmonology': ['shortness', 'breath', 'dyspnea', 'copd', 'respiratory', 'breathing', 'pulmonary'],
        'gastroenterology': ['ulcer', 'hemorrhage', 'bleeding', 'endoscopy', 'gastrointestinal', 'duodenal'],
        'neurology': ['stroke', 'cerebrovascular', 'paresis', 'weakness', 'paralysis', 'headache', 'cephalgia'],
        'infectology': ['hiv', 'cellulitis', 'infection', 'infectious', 'viral', 'bacterial'],
        'oncology': ['cancer', 'carcinoma', 'neoplasm', 'adenocarcinoma', 'chemotherapy', 'tumor'],
        'general': ['hours', 'left', 'olive', 'cleaning', 'excellent', 'after', 'yesterday', 'confused', 'degree', 'performed']
    }

    # Análise por prontuário
    total_relevant = 0
    total_tests = 0
    prontuario_analysis = []

    for prontuario in data['prontuarios']:
        prontuario_id = prontuario['prontuario_id']
        print(f'\n📋 PRONTUÁRIO {prontuario_id}:')
        
        prontuario_relevant = 0
        prontuario_total = 0
        
        # Determina categoria baseada no ID
        if prontuario_id == 1:
            category = 'cardiology'
        elif prontuario_id == 2:
            category = 'pulmonology'
        elif prontuario_id == 3:
            category = 'gastroenterology'
        elif prontuario_id in [4, 7]:
            category = 'neurology'
        elif prontuario_id == 5:
            category = 'oncology'
        elif prontuario_id == 6:
            category = 'infectology'
        else:
            category = 'general'
        
        expected_terms = medical_terms_expected.get(category, medical_terms_expected['general'])
        
        for result in prontuario['results']:
            term = result['term']
            top_results = result['top_results']
            scores = result['scores']
            
            print(f'   Termo: {term}')
            
            # Converte para formato de análise
            results_for_analysis = []
            for res, score in zip(top_results, scores):
                results_for_analysis.append({
                    'text': res,
                    'score': score
                })
            
            # Análise de relevância
            analysis = analyze_clinical_relevance(term, results_for_analysis, category, expected_terms)
            
            if analysis['relevant']:
                print(f'   ✅ RELEVANTE (confiança: {analysis["confidence"]:.3f})')
                print(f'   📊 {analysis["reason"]}')
                prontuario_relevant += 1
            else:
                print(f'   ❌ IRRELEVANTE (confiança: {analysis["confidence"]:.3f})')
                print(f'   📊 {analysis["reason"]}')
            
            prontuario_total += 1
            total_tests += 1
            if analysis['relevant']:
                total_relevant += 1
        
        prontuario_rate = prontuario_relevant / prontuario_total if prontuario_total > 0 else 0
        print(f'   📈 Taxa de relevância: {prontuario_rate:.1%} ({prontuario_relevant}/{prontuario_total})')
        
        prontuario_analysis.append({
            'prontuario_id': prontuario_id,
            'category': category,
            'relevant': prontuario_relevant,
            'total': prontuario_total,
            'rate': prontuario_rate
        })

    # Análise geral
    overall_rate = total_relevant / total_tests if total_tests > 0 else 0

    print(f'\n{"="*60}')
    print('📊 ANÁLISE FINAL DE RELEVÂNCIA CLÍNICA')
    print(f'{"="*60}')

    print(f'📋 Total de testes: {total_tests}')
    print(f'✅ Testes relevantes: {total_relevant}')
    print(f'📊 Taxa geral de relevância: {overall_rate:.1%}')

    print(f'\n📋 Análise por Prontuário:')
    print('   ID | Categoria      | Relevantes | Total | Taxa')
    print('   ' + '-' * 50)

    for analysis in prontuario_analysis:
        print(f'   {analysis["prontuario_id"]:2d} | {analysis["category"]:14} | {analysis["relevant"]:10d} | {analysis["total"]:5d} | {analysis["rate"]:5.1%}')

    # Análise por categoria
    category_stats = {}
    for analysis in prontuario_analysis:
        cat = analysis['category']
        if cat not in category_stats:
            category_stats[cat] = {'relevant': 0, 'total': 0}
        category_stats[cat]['relevant'] += analysis['relevant']
        category_stats[cat]['total'] += analysis['total']

    print(f'\n📋 Análise por Categoria:')
    print('   Categoria      | Relevantes | Total | Taxa')
    print('   ' + '-' * 40)

    for cat, stats in category_stats.items():
        rate = stats['relevant'] / stats['total'] if stats['total'] > 0 else 0
        print(f'   {cat:14} | {stats["relevant"]:10d} | {stats["total"]:5d} | {rate:5.1%}')

    # Avaliação final
    print(f'\n🎯 AVALIAÇÃO FINAL:')
    if overall_rate >= 0.8:
        print(f'   ✅ EXCELENTE: {overall_rate:.1%} de relevância clínica')
    elif overall_rate >= 0.6:
        print(f'   ✅ BOA: {overall_rate:.1%} de relevância clínica')
    elif overall_rate >= 0.4:
        print(f'   ⚠️ REGULAR: {overall_rate:.1%} de relevância clínica')
    else:
        print(f'   ❌ RUIM: {overall_rate:.1%} de relevância clínica')

    # Salva relatório de validação
    validation_report = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_tests': total_tests,
        'total_relevant': total_relevant,
        'overall_rate': overall_rate,
        'prontuario_analysis': prontuario_analysis,
        'category_stats': category_stats,
        'validation_criteria': {
            'relevance_ratio_threshold': 0.5,
            'avg_score_threshold': 0.6,
            'best_score_threshold': 0.7
        }
    }

    report_file = 'data/final_reports/incremental_validation_report.json'
    os.makedirs(os.path.dirname(report_file), exist_ok=True)

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(validation_report, f, indent=2, ensure_ascii=False)

    print(f'\n💾 Relatório de validação salvo em: {report_file}')

if __name__ == "__main__":
    main()
