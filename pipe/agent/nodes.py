from langsmith import traceable
from .tools import extract_and_split_file, generate_questions, evaluate_results
from .embeddings import search_snomed, snomed_terms
from .prompts import prepare_prompt
from langchain_openai import ChatOpenAI

from pipe.agent.types import PipelineState

import os

MODEL_NAME = os.getenv("MODEL", "gpt-3.5-turbo")  # pega do .env ou usa padrão
llm = ChatOpenAI(model=MODEL_NAME, temperature=0)



@traceable(name="Input Node")
def input_node(state: PipelineState):
    return {"pdf_path": state["pdf_path"]}  # continua funcionando

@traceable(name="Process Node")  # preparação
def process_node(state: PipelineState):
    return {"chunks": extract_and_split_file(state["pdf_path"], snomed_terms, 100, 20)}

@traceable(name="ConceptClinical Node")
def concept_clinical_node(state: PipelineState):
    analyzed = []
    for chunk in state["chunks"]:
        matches = search_snomed(chunk, k=5, distance_threshold=0.8)
        prompt = prepare_prompt(matches, chunk, qa=False)  # usa SYSTEM_PROMPT
        analyzed.append({"chunk": chunk, "concepts": matches, "diagnostic": llm.invoke(prompt).content})
    return {"clinical_results": analyzed}

@traceable(name="ConceptGuideline Node")
def concept_guideline_node(state: PipelineState):
    analyzed = []
    for chunk in state["chunks"]:
        matches = search_snomed(chunk, k=5, distance_threshold=0.8)
        prompt = prepare_prompt(matches, f"[Guideline Extraction] {chunk}", qa=False)  # SYSTEM_PROMPT 
        analyzed.append({"chunk": chunk, "concepts": matches, "guideline_info": llm.invoke(prompt).content})
    return {"guideline_results": analyzed}

@traceable(name="Aggregation Node")  # agregação de conceitos
def aggregation_node(state: PipelineState):
    # Junta resultados clínicos e de diretriz, remove sinônimos
    all_results = state["clinical_results"] + state["guideline_results"]
    # Exemplo simples: só junta
    unique = {r["chunk"]: r for r in all_results}  
    return {"results": list(unique.values())}

@traceable(name="Corpus Node")  # extração de frases por palavras-chave/locais
def corpus_node(state: PipelineState):
    corpus = [{"chunk": r["chunk"], "sentences": [s for s in r["chunk"].split(".") if len(s) > 20]} for r in state["results"]]
    return {"results": state["results"], "corpus": corpus}

@traceable(name="Question Node")
def question_node(state: PipelineState):
    return {
        "results": state["results"],
        "questions_map": [{"chunk": r["chunk"], "questions": generate_questions(r["concepts"])} for r in state["results"]]
    }

@traceable(name="QnA Node")
def qna_node(state: PipelineState):
    qna_results = []
    for qm in state["questions_map"]:
        prompt = prepare_prompt(qm["questions"], qm["chunk"], qa=True)  # usa SYSTEM_PROMPT_QA
        qna_results.append({"chunk": qm["chunk"], "qna": llm.invoke(prompt).content})
    return {"qna_results": qna_results}

@traceable(name="Evaluation Node")
def evaluation_node(state: PipelineState):
    metrics = evaluate_results(state["qna_results"])
    return {"qna_results": state["qna_results"], "metrics": metrics}


nodes = [
    ("input", input_node),
    ("process", process_node),
    ("concept_clinical", concept_clinical_node),
    ("concept_guideline", concept_guideline_node),
    ("aggregation", aggregation_node),
    ("corpus", corpus_node),
    ("questions", question_node),
    ("qna", qna_node),
    ("evaluation", evaluation_node),
]



