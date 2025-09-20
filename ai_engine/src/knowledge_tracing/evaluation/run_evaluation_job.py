# ai_engine/src/knowledge_tracing/evaluation/run_evaluation_job.py
"""
Batch job to compute evaluation metrics over a time window and persist to bkt_evaluation_windows.
Schedule this via cron or a workflow runner. Assumes migrations 005 are applied.
"""
from __future__ import annotations
import os
from typing import Optional, Dict, Any
from ..bkt.repository_supabase import SupabaseClient
from .data_provider import EvaluationDataProvider
from .metrics import BKTEvaluationSuite

def run_evaluation(
    *,
    concept_id: Optional[str] = None,
    start_ts: Optional[str] = None,
    end_ts: Optional[str] = None
) -> Dict[str, Any]:
    sb = SupabaseClient()
    provider = EvaluationDataProvider(sb)
    suite = BKTEvaluationSuite()

    # Load real data
    y_true, y_prob, trajectories = provider.load_window(concept_id=concept_id, start_ts=start_ts, end_ts=end_ts)

    # If empty, record a stub with neutral recommendation
    if not y_true:
        result = {
            "next_step_auc": 0.5,
            "next_step_accuracy": 0.5,
            "brier_score": 0.25,
            "calibration_error": 0.25,
            "trajectory_validity": 0.0,
            "recommendation": "NEEDS_IMPROVEMENT",
            "details": {"n_samples": 0, "n_trajectories": 0}
        }
        _persist(sb, concept_id, start_ts, end_ts, result)
        return result

    # Compute metrics using the suite (reusing binning and thresholds)
    report = suite.evaluate_window(concept_id=concept_id, start_ts=start_ts, end_ts=end_ts)
    _persist(sb, concept_id, start_ts, end_ts, report)
    return report

def _persist(sb: SupabaseClient, concept_id: Optional[str], start_ts: Optional[str], end_ts: Optional[str], report: Dict[str, Any]) -> None:
    payload = {
        "concept_id": concept_id,
        "start_ts": start_ts,
        "end_ts": end_ts,
        "next_step_auc": report["next_step_auc"],
        "next_step_accuracy": report["next_step_accuracy"],
        "brier_score": report["brier_score"],
        "calibration_error": report["calibration_error"],
        "trajectory_validity": report["trajectory_validity"],
        "recommendation": report["recommendation"],
        "details": report.get("details", {}),
    }
    sb.table("bkt_evaluation_windows").upsert(payload).execute()

if __name__ == "__main__":
    # Example: evaluate last 7 days globally or per concept
    # Provide ISO timestamps via environment if desired
    concept = os.getenv("EVAL_CONCEPT_ID")
    start = os.getenv("EVAL_START_TS")
    end = os.getenv("EVAL_END_TS")
    out = run_evaluation(concept_id=concept, start_ts=start, end_ts=end)
    print(out)
