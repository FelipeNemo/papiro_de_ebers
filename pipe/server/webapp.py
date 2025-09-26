from __future__ import annotations
import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from pipe.agent.types import PipelineState
from pipe.agent.graph import pipeline_app, run_pipeline

load_dotenv(".env")

fastapi_app = FastAPI(title="LangGraph SNOMED Pipeline")


@fastapi_app.get("/stream_file")
async def stream_file(file_path: str):
    """
    Streaming em tempo real do processamento do arquivo PDF/TXT.
    Envia cada node processado assim que termina.
    """
    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="Arquivo não existe")

    async def gen():
        state = PipelineState(pdf_path=file_path, chunks=[], results=[], questions_map=[], qna_results=[], metrics={})
        nodes = pipeline_app._graph.nodes
        entry = pipeline_app._graph.entry_point

        current_node = entry
        visited = set()

        while current_node != "END":
            node_fn = nodes[current_node].func
            try:
                output = node_fn(state)
            except Exception as e:
                output = {"error": str(e)}

            state.update(output)
            visited.add(current_node)
            yield f"data: {json.dumps({current_node: output}, ensure_ascii=False)}\n\n"

            edges = pipeline_app._graph.edges.get(current_node, [])
            current_node = edges[0] if edges else "END"

        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@fastapi_app.post("/process_file")
async def process_file(file_path: str):
    """
    Processa o arquivo PDF/TXT e retorna JSON completo.
    """
    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="Arquivo não existe")
    try:
        final_state = run_pipeline(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo: {e}")

    return final_state


@fastapi_app.get("/process_batch")
async def process_batch(input_folder: str = "data/test"):
    """
    Processa todos PDFs/TXT de uma pasta e salva resultados em JSON
    """
    import glob

    res_folder = os.path.join(input_folder, "res")
    os.makedirs(res_folder, exist_ok=True)
    files = glob.glob(os.path.join(input_folder, "*.txt")) + glob.glob(os.path.join(input_folder, "*.pdf"))

    all_results = {}
    for file_path in files:
        try:
            final_state = await run_pipeline(file_path)
            all_results[file_path] = final_state
            output_path = os.path.join(res_folder, os.path.splitext(os.path.basename(file_path))[0] + ".json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(final_state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            all_results[file_path] = {"error": str(e)}

    return all_results
