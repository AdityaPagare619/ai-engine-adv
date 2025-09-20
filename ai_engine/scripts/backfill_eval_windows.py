#!/usr/bin/env python
"""
Backfill evaluation windows over a date range (inclusive of start, exclusive of end).
Env:
  - EVAL_START_DATE=YYYY-MM-DD
  - EVAL_END_DATE=YYYY-MM-DD
  - EVAL_CONCEPT_ID (optional)
"""
from __future__ import annotations
import os
from datetime import datetime, timedelta, timezone

from ai_engine.src.knowledge_tracing.evaluation.run_evaluation_job import run_evaluation

def _iso_day_bounds(day: datetime) -> tuple[str, str]:
    start = datetime(day.year, day.month, day.day, 0, 0, 0, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    return start.isoformat(), end.isoformat()

def main():
    start_s = os.getenv("EVAL_START_DATE")
    end_s = os.getenv("EVAL_END_DATE")
    concept = os.getenv("EVAL_CONCEPT_ID")
    if not start_s or not end_s:
        raise SystemExit("Set EVAL_START_DATE and EVAL_END_DATE (YYYY-MM-DD)")

    start_d = datetime.fromisoformat(start_s).date()
    end_d = datetime.fromisoformat(end_s).date()

    cur = start_d
    while cur < end_d:
        s_iso, e_iso = _iso_day_bounds(datetime(cur.year, cur.month, cur.day))
        rep = run_evaluation(concept_id=concept, start_ts=s_iso, end_ts=e_iso)
        print(f"{cur.isoformat()} → AUC={rep['next_step_auc']:.3f}, ECE={rep['calibration_error']:.3f}")
        cur += timedelta(days=1)

if __name__ == "__main__":
    main()
