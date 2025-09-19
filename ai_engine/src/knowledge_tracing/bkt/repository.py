import logging
from typing import NamedTuple
from datetime import datetime
from .repository_supabase import SupabaseClient

logger = logging.getLogger("bkt_repository")

class BKTState(NamedTuple):
    mastery_probability: float
    practice_count: int

class BKTParams(NamedTuple):
    learn_rate: float
    slip_rate: float
    guess_rate: float

class BKTRepository:
    def __init__(self):
        self.client = SupabaseClient()

    def get_parameters(self, concept_id: str) -> BKTParams:
        try:
            row = self.client.table("bkt_parameters") \
                .select("learn_rate, slip_rate, guess_rate") \
                .eq("concept_id", concept_id).single().execute().data
            return BKTParams(row["learn_rate"], row["slip_rate"], row["guess_rate"])
        except Exception as e:
            logger.error(f"Failed to fetch BKT parameters for {concept_id}: {e}")
            # Return default safe parameters
            return BKTParams(learn_rate=0.3, slip_rate=0.1, guess_rate=0.2)

    def get_state(self, student_id: str, concept_id: str) -> BKTState:
        try:
            row = self.client.table("bkt_knowledge_states") \
                .select("mastery_probability, practice_count") \
                .eq("student_id", student_id) \
                .eq("concept_id", concept_id) \
                .single().execute().data
            if row:
                return BKTState(row["mastery_probability"], row["practice_count"])
            else:
                return BKTState(0.5, 0)
        except Exception as e:
            logger.error(f"Failed to fetch BKT state for {student_id}, {concept_id}: {e}")
            return BKTState(0.5, 0)

    def save_state(self, student_id: str, concept_id: str, mastery: float) -> None:
        try:
            state = self.get_state(student_id, concept_id)
            now = datetime.utcnow().isoformat()
            self.client.table("bkt_knowledge_states").upsert({
                "student_id": student_id,
                "concept_id": concept_id,
                "mastery_probability": mastery,
                "practice_count": state.practice_count + 1,
                "last_updated": now
            }).execute()
        except Exception as e:
            logger.error(f"Failed to save BKT state for {student_id}, {concept_id}: {e}")
            raise

    def get_practice_count(self, student_id: str, concept_id: str) -> int:
        return self.get_state(student_id, concept_id).practice_count

    def log_update(
        self, student_id: str, concept_id: str,
        prev: float, new: float, correct: bool, response_time_ms: int
    ) -> None:
        try:
            now = datetime.utcnow().isoformat()
            self.client.table("bkt_update_logs").insert({
                "student_id": student_id,
                "concept_id": concept_id,
                "previous_mastery": prev,
                "new_mastery": new,
                "is_correct": correct,
                "response_time_ms": response_time_ms,
                "timestamp": now
            }).execute()
        except Exception as e:
            logger.error(f"Failed to log BKT update for {student_id}, {concept_id}: {e}")
