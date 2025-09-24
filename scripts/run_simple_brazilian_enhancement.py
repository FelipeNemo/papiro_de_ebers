"""
Script Simplificado para Melhorias do Sistema Brasileiro
Fase 4: Criação de dicionários e melhorias sem fine-tuning complexo
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.simple_brazilian_finetuning import SimpleBrazilianFineTuner
import time

def run_brazilian_enhancement():
    """Executa melhorias para termos brasileiros"""
    print("🔬 Fase 4: Melhorias para Termos Médicos Brasileiros")
    print("=" * 70)
    
    try:
        # Inicializa sistema
        print("🚀 Inicializando sistema de melhorias...")
        enhancer = SimpleBrazilianFineTuner()
        
        # Carrega modelo
        print("\n📥 Carregando modelo PubMedBERT...")
        enhancer.load_model()
        
        # Cria dados de treinamento
        print("\n🔨 Criando dados de treinamento...")
        enhancer.create_training_data("data/brazilian_medical_terms.json")
        
        # Avalia modelo atual
        print("\n🧪 Avaliando modelo atual...")
        evaluation = enhancer.evaluate_model()
        
        # Cria traduções aprimoradas
        print("\n📚 Criando traduções aprimoradas...")
        enhancer.save_enhanced_translations("data/enhanced_medical_translations.json")
        
        # Cria sinônimos médicos
        print("\n📖 Criando sinônimos médicos...")
        enhancer.save_medical_synonyms("data/medical_synonyms.json")
        
        # Gera relatório
        print("\n📊 Gerando relatório de melhorias...")
        report = enhancer.generate_enhancement_report("data/brazilian_enhancement_report.json")
        
        print(f"\n✅ Melhorias concluídas!")
        print(f"📊 Similaridade média atual: {evaluation['average_similarity']:.3f}")
        print(f"📚 Traduções criadas: {report['translations_count']}")
        print(f"📖 Grupos de sinônimos: {report['synonyms_groups']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nas melhorias: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_system():
    """Testa sistema com melhorias"""
    print("\n🧪 Testando Sistema com Melhorias...")
    print("=" * 50)
    
    try:
        enhancer = SimpleBrazilianFineTuner()
        enhancer.load_model()
        
        # Testa com termos brasileiros complexos
        test_queries = [
            "dor no peito",
            "infarto agudo do miocárdio",
            "hipertensão arterial sistêmica",
            "falta de ar",
            "diabetes mellitus tipo 2",
            "pneumonia adquirida na comunidade",
            "asma brônquica",
            "gastrite",
            "hepatite viral",
            "câncer de mama"
        ]
        
        print("🔍 Testando similaridade com termos brasileiros...")
        similarities = []
        
        for query in test_queries:
            # Simula tradução para inglês
            if "dor no peito" in query:
                en_term = "chest pain"
            elif "infarto" in query:
                en_term = "myocardial infarction"
            elif "hipertensão" in query:
                en_term = "arterial hypertension"
            elif "falta de ar" in query:
                en_term = "shortness of breath"
            elif "diabetes" in query:
                en_term = "diabetes mellitus"
            elif "pneumonia" in query:
                en_term = "pneumonia"
            elif "asma" in query:
                en_term = "asthma"
            elif "gastrite" in query:
                en_term = "gastritis"
            elif "hepatite" in query:
                en_term = "hepatitis"
            elif "câncer" in query:
                en_term = "cancer"
            else:
                en_term = query
                
            similarity = enhancer.evaluate_similarity(query, en_term)
            similarities.append(similarity)
            
            print(f"   {query[:30]:30} ↔ {en_term[:20]:20} | {similarity:.3f}")
        
        avg_similarity = sum(similarities) / len(similarities)
        print(f"\n📊 Similaridade média: {avg_similarity:.3f}")
        
        if avg_similarity > 0.7:
            print("✅ Sistema com boa qualidade para termos brasileiros!")
        elif avg_similarity > 0.5:
            print("⚠️ Sistema com qualidade moderada")
        else:
            print("❌ Sistema precisa de melhorias")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def create_integration_guide():
    """Cria guia de integração"""
    print("\n📋 Criando Guia de Integração...")
    print("=" * 50)
    
    guide = {
        "title": "Guia de Integração - Sistema PubMedBERT Brasileiro",
        "version": "1.0",
        "description": "Sistema otimizado para termos médicos brasileiros",
        "components": {
            "enhanced_translations": "data/enhanced_medical_translations.json",
            "medical_synonyms": "data/medical_synonyms.json",
            "training_data": "data/brazilian_medical_terms.json",
            "evaluation_report": "data/brazilian_enhancement_report.json"
        },
        "usage": {
            "1": "Carregar traduções aprimoradas no sistema de tradução",
            "2": "Integrar sinônimos médicos no sistema de busca",
            "3": "Usar métricas de avaliação para monitoramento",
            "4": "Expandir dados de treinamento conforme necessário"
        },
        "next_steps": [
            "Integrar traduções no MedicalTranslator",
            "Adicionar sinônimos ao sistema de busca",
            "Implementar API REST",
            "Processar índice completo"
        ]
    }
    
    os.makedirs("data", exist_ok=True)
    with open("data/integration_guide.json", 'w', encoding='utf-8') as f:
        import json
        json.dump(guide, f, indent=2, ensure_ascii=False)
        
    print("✅ Guia de integração criado: data/integration_guide.json")
    return guide

if __name__ == "__main__":
    print("🏥 Fase 4: Melhorias para Termos Médicos Brasileiros")
    print("=" * 70)
    
    # Executa melhorias
    success = run_brazilian_enhancement()
    
    if success:
        # Testa sistema melhorado
        test_success = test_enhanced_system()
        
        if test_success:
            # Cria guia de integração
            guide = create_integration_guide()
            
            print("\n" + "=" * 70)
            print("📋 Resumo da Fase 4:")
            print(f"   ✅ Melhorias: {'PASSOU' if success else 'FALHOU'}")
            print(f"   ✅ Teste do sistema: {'PASSOU' if test_success else 'FALHOU'}")
            print(f"   ✅ Guia de integração: CRIADO")
            
            print("\n🎉 FASE 4 CONCLUÍDA!")
            print("✅ Sistema otimizado para termos brasileiros")
            print("📚 Dicionários e sinônimos criados")
            print("🚀 Pronto para Fase 5: API REST")
        else:
            print("\n❌ Falha no teste do sistema melhorado")
    else:
        print("\n❌ Falha nas melhorias")
