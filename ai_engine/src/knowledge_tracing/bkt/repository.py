from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from .repository_supabase import SupabaseClient

logger = logging.getLogger("bkt_repository")


# ---------- Data Models ----------
@dataclass
class BKTParams:
    learn_rate: float
    slip_rate: float
    guess_rate: float


@dataclass
class BKTState:
    student_id: str
    concept_id: str
    mastery_probability: float
    practice_count: int = 0


@dataclass
class QuestionMetadata:
    question_id: str
    difficulty_calibrated: Optional[float] = None
    bloom_level: Optional[str] = None
    estimated_time_seconds: Optional[int] = None
    required_process_skills: Optional[List[str]] = None


# ---------- Repository ----------
class BKTRepository:
    """
    Persists and retrieves BKT parameters, knowledge states, and update logs.
    Includes contextual adjustments using question metadata.
    """

    def __init__(self, client: Optional[Any] = None):
        # Allow any Supabase-like client for testing (mock or real)
        self.client: Any = client or SupabaseClient()

    # ---------- Question Metadata ----------
    def get_question_metadata(self, question_id: str) -> Optional[QuestionMetadata]:
        """Get question metadata from question_metadata_cache (via Supabase)."""
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
            logger.exception(f"Failed to fetch question metadata for {question_id}: {e}")
            return None

    # ---------- Parameters ----------
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
                return BKTParams(
                    learn_rate=float(row.get("learn_rate", 0.3)),
                    slip_rate=float(row.get("slip_rate", 0.1)),
                    guess_rate=float(row.get("guess_rate", 0.2)),
                )
            return BKTParams(learn_rate=0.3, slip_rate=0.1, guess_rate=0.2)
        except Exception as e:
            logger.exception(f"Failed to fetch BKT parameters for {concept_id}: {e}")
            return BKTParams(learn_rate=0.3, slip_rate=0.1, guess_rate=0.2)

    def get_parameters_with_context(
        self, concept_id: str, question_metadata: Optional[QuestionMetadata] = None
    ) -> BKTParams:
        """Get BKT parameters with optional question context for adaptive calibration."""
        try:
            base_params = self.get_parameters(concept_id)

            if not question_metadata:
                return base_params

            # Difficulty adjustment
            difficulty = 0.0
            if question_metadata.difficulty_calibrated is not None:
                try:
                    difficulty = float(question_metadata.difficulty_calibrated)
                except (ValueError, TypeError):
                    difficulty = 0.0

            adjusted_slip = min(0.4, base_params.slip_rate + (max(0.0, difficulty) * 0.05))

            bloom_adjustments: Dict[str, float] = {
                "Remember": -0.05,
                "Understand": 0.0,
                "Apply": 0.02,
                "Analyze": 0.05,
                "Evaluate": 0.08,
                "Create": 0.1,
            }
            bloom_adj = bloom_adjustments.get(question_metadata.bloom_level, 0.0)
            adjusted_guess = max(0.05, min(0.4, base_params.guess_rate + bloom_adj))

            return BKTParams(base_params.learn_rate, adjusted_slip, adjusted_guess)

        except Exception as e:
            logger.exception(f"Failed to get contextual parameters for {concept_id}: {e}")
            return BKTParams(learn_rate=0.3, slip_rate=0.1, guess_rate=0.2)

    # ---------- State ----------
    def get_state(self, student_id: str, concept_id: str) -> BKTState:
        """Fetch a student's BKT state for a concept, return sensible defaults if missing."""
        try:
            resp = (
                self.client.table("bkt_knowledge_states")
                .select("mastery_probability, practice_count")
                .eq("student_id", student_id)
                .eq("concept_id", concept_id)
                .limit(1)
                .execute()
            )
            data = resp.data if isinstance(resp.data, list) else ([resp.data] if resp.data else [])
            if data:
                row = data[0]
                return BKTState(
                    student_id=student_id,
                    concept_id=concept_id,
                    mastery_probability=float(row.get("mastery_probability", 0.5)),
                    practice_count=int(row.get("practice_count", 0)),
                )
            return BKTState(
                student_id=student_id,
                concept_id=concept_id,
                mastery_probability=0.5,
                practice_count=0,
            )
        except Exception as e:
            logger.exception(f"Failed to fetch BKT state for {student_id}, {concept_id}: {e}")
            return BKTState(student_id=student_id, concept_id=concept_id, mastery_probability=0.5, practice_count=0)

    def save_state(self, student_id: str, concept_id: str, mastery: float) -> None:
        """Update or insert the student's knowledge state (increments practice_count)."""
        try:
            # Check if state exists
            try:
                existing = self.client.table("bkt_knowledge_states")\
                    .select("practice_count")\
                    .eq("student_id", student_id)\
                    .eq("concept_id", concept_id)\
                    .limit(1)\
                    .execute()
                
                # Update existing record
                if existing.data:
                    if isinstance(existing.data, list):
                        row0 = existing.data[0] if existing.data else None
                    else:
                        row0 = existing.data
                    current_count = int((row0 or {}).get("practice_count", 0))
                    self.client.table("bkt_knowledge_states")\
                        .update({
                            "mastery_probability": float(mastery),
                            "practice_count": current_count + 1,
                            "last_practiced": datetime.now(timezone.utc).isoformat(),
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                        })\
                        .eq("student_id", student_id)\
                        .eq("concept_id", concept_id)\
                        .execute()
                else:
                    raise ValueError("No existing record found")
                    
            except Exception:
                # Insert new record if it doesn't exist
                payload = {
                    "student_id": student_id,
                    "concept_id": concept_id,
                    "mastery_probability": float(mastery),
                    "practice_count": 1,
                    "last_practiced": datetime.now(timezone.utc).isoformat(),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
                self.client.table("bkt_knowledge_states").insert(payload).execute()
                
        except Exception as e:
            logger.exception(f"Failed to save BKT state for {student_id}, {concept_id}: {e}")
            raise

    def get_practice_count(self, student_id: str, concept_id: str) -> int:
        """Return practice count only (convenience method)."""
        return self.get_state(student_id, concept_id).practice_count

    # ---------- Logging ----------
    def log_update(
        self,
        student_id: str,
        concept_id: str,
        previous_mastery: float,
        new_mastery: float,
        is_correct: bool,
        response_time_ms: Optional[int] = None,
        *,
        question_id: Optional[str] = None,
        params_used: Optional[Dict[str, float]] = None,
        engine_version: str = "v1.0"
    ) -> None:
        """
        Log each BKT update in bkt_update_logs for audit/analytics.
        Fail-safe: logging failure must not interrupt the learning flow.
        """
        try:
            payload = {
                "student_id": student_id,
                "concept_id": concept_id,
                "previous_mastery": float(previous_mastery),
                "new_mastery": float(new_mastery),
                "is_correct": bool(is_correct),
                "response_time_ms": int(response_time_ms) if response_time_ms is not None else None,
                "question_id": question_id,
                "params_json": params_used or {},
                "engine_version": engine_version,
            }
            self.client.table("bkt_update_logs").insert(payload).execute()
        except Exception as e:
            logger.exception(f"Failed to log BKT update for {student_id}, {concept_id}: {e}")
            # Do not raise; preserve learning flow
