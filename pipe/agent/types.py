# pipe/agent/types.py
from typing import TypedDict, List, Dict

class PipelineState(TypedDict):
    pdf_path: str
    chunks: List[str]
    results: List[Dict]
    questions_map: List[Dict]
    qna_results: List[Dict]
    metrics: Dict
