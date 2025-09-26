from langgraph.graph import StateGraph, END

from pipe.agent.nodes import (
    input_node,
    process_node,
    concept_clinical_node,
    concept_guideline_node,
    aggregation_node,
    corpus_node,
    question_node,
    qna_node,
    evaluation_node
)

from pipe.agent.types import PipelineState

graph = StateGraph(PipelineState)

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

for name, node in nodes:
    graph.add_node(name, node)

graph.set_entry_point("input")

edges = [
    ("input","process"),
    ("process","concept_clinical"),
    ("process","concept_guideline"),
    ("concept_clinical","aggregation"),
    ("concept_guideline","aggregation"),
    ("aggregation","questions"),
    ("questions","qna"),
    
    ("process","corpus"),
    ("corpus","qna"),
    
    ("qna","evaluation"),
    ("evaluation",END)
]

for src, dst in edges:
    graph.add_edge(src,dst)

app = graph.compile()

from pipe.agent.types import PipelineState

async def run_pipeline(file_path: str):
    # cria um dict compatível com PipelineState
    state: PipelineState = {
        "pdf_path": file_path,
        "chunks": [],
        "results": [],
        "questions_map": [],
        "qna_results": [],
        "metrics": {}
    }

    final_state = await app.ainvoke(state)
    return final_state

agent = app
