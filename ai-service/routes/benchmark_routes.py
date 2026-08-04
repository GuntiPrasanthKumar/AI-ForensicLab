from fastapi import APIRouter, Body
from typing import Optional, List
from pydantic import BaseModel
from benchmark.evaluator import BenchmarkEvaluator

router = APIRouter(prefix="/api/benchmark", tags=["Benchmark"])

class BenchmarkPayload(BaseModel):
    models: Optional[List[str]] = None
    categories: Optional[List[str]] = None

@router.get("/summary")
def get_latest_benchmark_summary():
    """Returns the latest benchmark evaluation summary."""
    evaluator = BenchmarkEvaluator()
    summary = evaluator.run_benchmark(model_keys=["pytorch_spectral"])
    return summary

@router.post("/run")
def trigger_benchmark_run(payload: BenchmarkPayload = Body(...)):
    """Triggers an automated benchmark evaluation run."""
    evaluator = BenchmarkEvaluator()
    summary = evaluator.run_benchmark(model_keys=payload.models, categories=payload.categories)
    return summary
