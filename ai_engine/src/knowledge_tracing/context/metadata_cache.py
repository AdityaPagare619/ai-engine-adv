# ai_engine/src/knowledge_tracing/context/metadata_cache.py
import time
import threading
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from ..bkt.repository_supabase import SupabaseClient
from ..bkt.repository import QuestionMetadata  # reuse the shared type


@dataclass(frozen=True)
class CacheConfig:
    ttl_seconds: int = 300          # 5 minutes default
    max_entries: int = 10_000       # scale as needed


class QuestionMetadataCache:
    """
    Read-optimized accessor over Supabase question_metadata_cache with an in-memory TTL cache.
    """

    def __init__(self, client: Optional[SupabaseClient] = None, config: CacheConfig = CacheConfig()):
        self._client = client or SupabaseClient()
        self._config = config
        self._cache: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def _now(self) -> float:
        return time.time()

    def _evict_if_needed(self):
        # Simple size-based eviction: drop oldest entries when exceeding max_entries
        if len(self._cache) <= self._config.max_entries:
            return
        # Sort by timestamp and evict 10% oldest
        items = sorted(self._cache.items(), key=lambda kv: kv[1]["ts"])
        evict_count = max(1, len(items) // 10)
        for k, _ in items[:evict_count]:
            self._cache.pop(k, None)

    def _is_fresh(self, ts: float) -> bool:
        return (self._now() - ts) < self._config.ttl_seconds

    def get(self, question_id: str) -> Optional[QuestionMetadata]:
        with self._lock:
            entry = self._cache.get(question_id)
            if entry and self._is_fresh(entry["ts"]):
                return entry["value"]

        # Miss or stale: fetch from Supabase
        try:
            row = (
                self._client.table("question_metadata_cache")
                .select(
                    "question_id, difficulty_calibrated, bloom_level, "
                    "estimated_time_seconds, required_process_skills"
                )
                .eq("question_id", question_id)
                .single()
                .execute()
                .data
            )
            if not row:
                return None

            qm = QuestionMetadata(
                question_id=row["question_id"],
                difficulty_calibrated=row.get("difficulty_calibrated"),
                bloom_level=row.get("bloom_level"),
                estimated_time_seconds=row.get("estimated_time_seconds"),
                required_process_skills=row.get("required_process_skills", []),
            )
            with self._lock:
                self._cache[question_id] = {"value": qm, "ts": self._now()}
                self._evict_if_needed()
            return qm
        except Exception:
            # Fail closed on metadata (caller should handle None)
            return None

    def bulk_get(self, question_ids: List[str]) -> Dict[str, Optional[QuestionMetadata]]:
        # Simple loop (optimize to IN query if needed)
        out: Dict[str, Optional[QuestionMetadata]] = {}
        for qid in question_ids:
            out[qid] = self.get(qid)
        return out
