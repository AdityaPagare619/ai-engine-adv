# ai_engine/src/knowledge_tracing/service/advanced_bkt_service.py
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from ..bkt.repository import BKTRepository, BKTParams, BKTState
from ..core.bkt_core import CanonicalBKTCore
from ..core.constraint_validator import ParameterConstraintValidator
from ..context.metadata_cache import QuestionMetadataCache
from ..context.adjustments import adjust_params_for_context

logger = logging.getLogger("advanced_bkt_service")


@dataclass
class MasteryUpdate:
    previous_mastery: float
    posterior_mastery: float
    new_mastery: float
    p_correct_pred: float
    adjusted_params: BKTParams
    constraint_violations: list
    explanation: Dict[str, Any]


class AdvancedBKTService:
    """
    Orchestrates:
      1) Fetch state & base params
      2) Contextual modulation (difficulty, Bloom, response time)
      3) Constraint validation & feasible projection
      4) Canonical BKT posterior & transition
      5) Persistence + rich explanation
    """

    def __init__(self, repo: Optional[BKTRepository] = None):
        self.repo = repo or BKTRepository()
        self.core = CanonicalBKTCore()
        self.qmeta = QuestionMetadataCache()

    def _get_params_with_context(
        self, concept_id: str, question_id: Optional[str], response_time_ms: Optional[int]
    ) -> Dict[str, Any]:
        base = self.repo.get_parameters(concept_id)
        meta = self.qmeta.get(question_id) if question_id else None
        mod = adjust_params_for_context(base, meta, response_time_ms)
        return {"base": base, "meta": meta, **mod}

    async def update_mastery(
        self,
        student_id: str,
        concept_id: str,
        *,
        is_correct: bool,
        question_id: Optional[str] = None,
        response_time_ms: Optional[int] = None
    ) -> MasteryUpdate:
        # 1) Load state
        state: BKTState = await self._get_state_async(student_id, concept_id)

        # 2) Params with context
        ctx = self._get_params_with_context(concept_id, question_id, response_time_ms)
        adjusted: BKTParams = ctx["adjusted"]
        violations = ctx["explanation"]["violations"]

        # 3) Final safety validation (redundant guardrail)
        val = ParameterConstraintValidator.validate_bkt_parameters(adjusted)
        if not val.is_valid:
            adjusted = val.corrected_params
            violations = list(set(violations + val.violations))

        # 4) Canonical update
        out = self.core.update(state.mastery_probability, is_correct, adjusted)

        # 5) Persist with retry handled in repository
        await self._save_async(student_id, concept_id, out["new_mastery"])

        # NEW: include params_used JSON for audit and offline reconstruction
        params_used = {
            "learn_rate": float(adjusted.learn_rate),
            "slip_rate": float(adjusted.slip_rate),
            "guess_rate": float(adjusted.guess_rate),
        }

        await self._log_async(
            student_id,
            concept_id,
            out["previous_mastery"],
            out["new_mastery"],
            is_correct,
            response_time_ms,
            question_id=question_id,
            params_used=params_used,
        )

        # 6) Package response
        explanation = {
            "context": {
                "question_id": question_id,
                "response_time_ms": response_time_ms,
                "question_metadata": (ctx["meta"].__dict__ if ctx["meta"] else None),
            },
            "param_adjustments": ctx["explanation"],
            "bkt": out["explanation"],
        }

        return MasteryUpdate(
            previous_mastery=out["previous_mastery"],
            posterior_mastery=out["posterior_mastery"],
            new_mastery=out["new_mastery"],
            p_correct_pred=out["p_correct_pred"],
            adjusted_params=adjusted,
            constraint_violations=violations,
            explanation=explanation,
        )

    async def _get_state_async(self, student_id: str, concept_id: str) -> BKTState:
        # Offload synchronous repository work if needed later; currently direct
        return self.repo.get_state(student_id, concept_id)

    async def _save_async(self, student_id: str, concept_id: str, mastery: float) -> None:
        return self.repo.save_state(student_id, concept_id, mastery)

    async def _log_async(
        self,
        student_id: str,
        concept_id: str,
        previous: float,
        new: float,
        is_correct: bool,
        response_time_ms: Optional[int],
        *,
        question_id: Optional[str],
        params_used: Dict[str, float],
    ) -> None:
        return self.repo.log_update(
            student_id,
            concept_id,
            previous,
            new,
            is_correct,
            response_time_ms,
            question_id=question_id,
            params_used=params_used,
        )
