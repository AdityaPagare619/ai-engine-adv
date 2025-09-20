# ai_engine/src/knowledge_tracing/evaluation/data_provider.py
from __future__ import annotations
import datetime as dt
from typing import Dict, Any, List, Tuple, Optional, DefaultDict
from collections import defaultdict

from ..bkt.repository_supabase import SupabaseClient
from ..bkt.repository import BKTParams
from ..core.bkt_core import CanonicalBKTCore
from ..context.metadata_cache import QuestionMetadataCache
from ..context.adjustments import adjust_params_for_context


class EvaluationDataProvider:
    """
    Pulls interaction logs and reconstructs next-step predictions for evaluation:
      - y_true: observed correctness events in order
      - y_prob: model predicted correctness prior to each observation
      - trajectories: mastery trajectories per (student, concept)
    Notes:
      - If per-interaction parameters are not stored, we reconstruct predictions
        using stored prev mastery, base params (by concept), and question context.  # TODO: persist params
    """

    def __init__(self, client: Optional[SupabaseClient] = None):
        self.client = client or SupabaseClient()
        self.qmeta = QuestionMetadataCache()

    def _iso_range_filter(self, start_ts: Optional[str], end_ts: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        return start_ts, end_ts

    def _fetch_logs(
        self,
        concept_id: Optional[str],
        start_ts: Optional[str],
        end_ts: Optional[str],
        limit: int = 5000
    ) -> List[Dict[str, Any]]:
        q = self.client.table("bkt_update_logs").select(
            "student_id, concept_id, previous_mastery, new_mastery, "
            "is_correct, response_time_ms, timestamp, question_id"
        )
        if concept_id:
            q = q.eq("concept_id", concept_id)
        if start_ts:
            q = q.gte("timestamp", start_ts)
        if end_ts:
            q = q.lte("timestamp", end_ts)
        # Order by time to ensure sequence correctness if supported by the adapter
        # Some adapters: q = q.order("timestamp", desc=False)
        data = q.execute().data or []
        # Sort defensively if the adapter didn't respect ordering
        data.sort(key=lambda r: r.get("timestamp", ""))
        return data[:limit]

    def _fetch_params_by_concept(self, concept_ids: List[str]) -> Dict[str, BKTParams]:
        out: Dict[str, BKTParams] = {}
        uniq = list({c for c in concept_ids if c})
        for cid in uniq:
            row = (
                self.client.table("bkt_parameters")
                .select("learn_rate, slip_rate, guess_rate")
                .eq("concept_id", cid)
                .single()
                .execute()
                .data
            )
            if row:
                out[cid] = BKTParams(row["learn_rate"], row["slip_rate"], row["guess_rate"])
        return out

    def load_window(
        self,
        concept_id: Optional[str] = None,
        start_ts: Optional[str] = None,
        end_ts: Optional[str] = None
    ) -> Tuple[List[int], List[float], Dict[str, List[float]]]:
        """
        Returns:
            y_true: list[int]
            y_prob: list[float]
            trajectories: dict[key -> mastery_seq]
        """
        logs = self._fetch_logs(concept_id, start_ts, end_ts)
        if not logs:
            return [], [], {}

        concept_ids = [r["concept_id"] for r in logs]
        base_params = self._fetch_params_by_concept(concept_ids)

        y_true: List[int] = []
        y_prob: List[float] = []
        trajectories: DefaultDict[str, List[float]] = defaultdict(list)

        for r in logs:
            sid = r["student_id"]
            cid = r["concept_id"]
            prev_m = float(r.get("previous_mastery", 0.5))
            is_corr = bool(r.get("is_correct", False))
            qid = r.get("question_id")
            rt_ms = r.get("response_time_ms")

            # Reconstruct params with context
            params = base_params.get(cid)
            if not params:
                # fall back to safe defaults if missing
                params = BKTParams(learn_rate=0.25, slip_rate=0.10, guess_rate=0.20)

            meta = self.qmeta.get(qid) if qid else None
            adj = adjust_params_for_context(params, meta, rt_ms)
            used_params = adj["adjusted"]

            # Predicted correctness based on prev mastery and params
            p_pred = CanonicalBKTCore.predict_correctness_prob(prev_m, used_params)

            # Append
            y_true.append(1 if is_corr else 0)
            y_prob.append(float(p_pred))

            key = f"{sid}_{cid}"
            trajectories[key].append(float(r.get("new_mastery", prev_m)))

        return y_true, y_prob, dict(trajectories)
