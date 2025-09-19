import logging
from typing import NamedTuple, Optional, List, Dict, Any
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


class QuestionMetadata(NamedTuple):
    question_id: str
    difficulty_calibrated: Optional[float]
    bloom_level: Optional[str]
    estimated_time_seconds: Optional[int]
    required_process_skills: Optional[List[str]]


class BKTRepository:
    def __init__(self):
        self.client = SupabaseClient()

    def get_question_metadata(self, question_id: str) -> Optional[QuestionMetadata]:
        """Get question metadata from question_metadata_cache (via Supabase bridge or cache)."""
        try:
            row = (
                self.client.table("question_metadata_cache")
                .select(
                    "question_id, difficulty_calibrated, bloom_level, "
                    "estimated_time_seconds, required_process_skills"
                )
                .eq("question_id", question_id)
                .single()
                .execute()
                .data
            )

            if row:
                return QuestionMetadata(
                    question_id=row.get("question_id"),
                    difficulty_calibrated=row.get("difficulty_calibrated"),
                    bloom_level=row.get("bloom_level"),
                    estimated_time_seconds=row.get("estimated_time_seconds"),
                    required_process_skills=row.get("required_process_skills", []),
                )

            return None
        except Exception as e:
            # Use exception to capture stack trace in logs
            logger.exception(f"Failed to fetch question metadata for {question_id}: {e}")
            return None

    def get_parameters_with_context(
        self, concept_id: str, question_metadata: Optional[QuestionMetadata] = None
    ) -> BKTParams:
        """Get BKT parameters with optional question context for adaptive calibration."""
        try:
            base_params = self.get_parameters(concept_id)

            # If no question metadata provided, return base params
            if not question_metadata:
                return base_params

            # Adjust parameters based on question difficulty and Bloom's level
            difficulty = 0.0
            if question_metadata.difficulty_calibrated is not None:
                try:
                    difficulty = float(question_metadata.difficulty_calibrated)
                except (ValueError, TypeError):
                    difficulty = 0.0

            # Increase slip rate for harder questions (bounded)
            adjusted_slip = min(0.4, base_params.slip_rate + (max(0.0, difficulty) * 0.05))

            # Bloom-level adjustments for guess rate
            bloom_adjustments: Dict[str, float] = {
                "Remember": -0.05,   # less guessing on memory tasks
                "Understand": 0.0,
                "Apply": 0.02,
                "Analyze": 0.05,
                "Evaluate": 0.08,
                "Create": 0.1,
            }
            bloom_adj = bloom_adjustments.get(question_metadata.bloom_level, 0.0)
            adjusted_guess = max(0.05, min(0.4, base_params.guess_rate + bloom_adj))

            # Keep learn_rate unchanged for now (could be extended later)
            return BKTParams(base_params.learn_rate, adjusted_slip, adjusted_guess)

        except Exception as e:
            logger.exception(f"Failed to get contextual parameters for {concept_id}: {e}")
            # Safe fallback
            return BKTParams(learn_rate=0.3, slip_rate=0.1, guess_rate=0.2)

    def get_parameters(self, concept_id: str) -> BKTParams:
        """Fetch stored BKT parameters for a concept; fall back to safe defaults if unavailable."""
        try:
            row = (
                self.client.table("bkt_parameters")
                .select("learn_rate, slip_rate, guess_rate")
                .eq("concept_id", concept_id)
                .single()
                .execute()
                .data
            )

            if row:
                # Use .get with defaults to be robust to schema changes
                return BKTParams(
                    learn_rate=float(row.get("learn_rate", 0.3)),
                    slip_rate=float(row.get("slip_rate", 0.1)),
                    guess_rate=float(row.get("guess_rate", 0.2)),
                )

            return BKTParams(learn_rate=0.3, slip_rate=0.1, guess_rate=0.2)
        except Exception as e:
            logger.exception(f"Failed to fetch BKT parameters for {concept_id}: {e}")
            return BKTParams(learn_rate=0.3, slip_rate=0.1, guess_rate=0.2)

    def get_state(self, student_id: str, concept_id: str) -> BKTState:
        """Fetch a student's BKT state for a specific concept, return sensible defaults if missing."""
        try:
            row = (
                self.client.table("bkt_knowledge_states")
                .select("mastery_probability, practice_count")
                .eq("student_id", student_id)
                .eq("concept_id", concept_id)
                .single()
                .execute()
                .data
            )
            if row:
                mastery = float(row.get("mastery_probability", 0.5))
                practice_count = int(row.get("practice_count", 0))
                return BKTState(mastery_probability=mastery, practice_count=practice_count)
            else:
                return BKTState(mastery_probability=0.5, practice_count=0)
        except Exception as e:
            logger.exception(f"Failed to fetch BKT state for {student_id}, {concept_id}: {e}")
            return BKTState(mastery_probability=0.5, practice_count=0)

    def save_state(self, student_id: str, concept_id: str, mastery: float) -> None:
        """Upsert the student's knowledge state (increments practice_count)."""
        try:
            state = self.get_state(student_id, concept_id)
            now = datetime.utcnow().isoformat()
            self.client.table("bkt_knowledge_states").upsert(
                {
                    "student_id": student_id,
                    "concept_id": concept_id,
                    "mastery_probability": mastery,
                    "practice_count": state.practice_count + 1,
                    "last_updated": now,
                }
            ).execute()
        except Exception as e:
            logger.exception(f"Failed to save BKT state for {student_id}, {concept_id}: {e}")
            # Re-raise to let calling code decide how to react
            raise

    def get_practice_count(self, student_id: str, concept_id: str) -> int:
        return self.get_state(student_id, concept_id).practice_count

    def log_update(
        self,
        student_id: str,
        concept_id: str,
        prev: float,
        new: float,
        correct: bool,
        response_time_ms: int,
    ) -> None:
        """Log each BKT update in bkt_update_logs for audit / analytics."""
        try:
            now = datetime.utcnow().isoformat()
            self.client.table("bkt_update_logs").insert(
                {
                    "student_id": student_id,
                    "concept_id": concept_id,
                    "previous_mastery": prev,
                    "new_mastery": new,
                    "is_correct": correct,
                    "response_time_ms": response_time_ms,
                    "timestamp": now,
                }
            ).execute()
        except Exception as e:
            logger.exception(f"Failed to log BKT update for {student_id}, {concept_id}: {e}")
            # don't raise; logging failure shouldn't break learning flow
