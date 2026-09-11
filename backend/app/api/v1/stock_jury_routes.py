from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from app.core.config import settings
from app.stock_jury.evaluation import evaluate_cases, load_cases, release_gate

router = APIRouter(prefix="/evaluation", tags=["stock-jury-evaluation"])


@router.get("/summary")
def evaluation_summary() -> dict:
    dataset = Path(settings.STOCK_JURY_EVALUATION_DATASET)
    if not dataset.is_absolute():
        dataset = Path(__file__).resolve().parents[3] / dataset
    if not dataset.exists():
        return {"status": "not_loaded", "required_cases": 100, "dataset": str(dataset)}
    cases = load_cases(dataset)
    metrics = evaluate_cases(cases)
    approved = Path(settings.STOCK_JURY_APPROVED_METRICS)
    if not approved.is_absolute():
        approved = Path(__file__).resolve().parents[3] / approved
    result = {"status": "ready", "required_cases": 100, "dataset": str(dataset), "metrics": metrics}
    if approved.exists():
        import json

        result["release_gate"] = release_gate(metrics, json.loads(approved.read_text(encoding="utf-8")))
    return result
