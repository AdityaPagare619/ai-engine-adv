# ai_engine/src/knowledge_tracing/evaluation/persist_rollups_job.py
"""
Daily rollup job: aggregates bkt_evaluation_windows into bkt_evaluation_concept_daily.
Run after evaluation jobs to keep dashboard metrics current.
"""
from __future__ import annotations
from typing import Optional
from datetime import datetime, timedelta, timezone

from ..bkt.repository_supabase import SupabaseClient

def run_daily_rollup(day_iso: Optional[str] = None) -> dict:
    sb = SupabaseClient()
    if day_iso:
        day = day_iso
    else:
        # default to UTC "yesterday" to ensure window completion
        day = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()

    # Pull all windows whose created_at falls within the day
    rows = sb.table("bkt_evaluation_windows").select(
        "concept_id, next_step_auc, brier_score, calibration_error, trajectory_validity, created_at"
    ).execute().data or []

    # Filter for the target day
    rows = [r for r in rows if r.get("concept_id") and r.get("created_at", "").startswith(day)]

    by_concept = {}
    counts = {}
    for r in rows:
        cid = r["concept_id"]
        agg = by_concept.setdefault(cid, {"auc_sum": 0.0, "brier_sum": 0.0, "ece_sum": 0.0, "traj_sum": 0.0})
        agg["auc_sum"] += float(r["next_step_auc"])
        agg["brier_sum"] += float(r["brier_score"])
        agg["ece_sum"] += float(r["calibration_error"])
        agg["traj_sum"] += float(r["trajectory_validity"])
        counts[cid] = counts.get(cid, 0) + 1

    upserts = []
    for cid, agg in by_concept.items():
        n = max(counts[cid], 1)
        upserts.append({
            "day": day,
            "concept_id": cid,
            "next_step_auc_avg": agg["auc_sum"] / n,
            "brier_score_avg": agg["brier_sum"] / n,
            "calibration_error_avg": agg["ece_sum"] / n,
            "trajectory_validity_avg": agg["traj_sum"] / n,
            "runs_count": n
        })

    if upserts:
        sb.table("bkt_evaluation_concept_daily").upsert(upserts).execute()

    return {"day": day, "concepts": len(upserts)}
