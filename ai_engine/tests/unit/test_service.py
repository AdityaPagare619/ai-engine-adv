# ai_engine/tests/unit/test_service.py
import pytest
from dataclasses import dataclass
from typing import Optional, Dict, Any
from ai_engine.src.knowledge_tracing.services.advanced_bkt_service import AdvancedBKTService, MasteryUpdate
from ai_engine.src.knowledge_tracing.bkt.repository import BKTParams, BKTState, QuestionMetadata

@dataclass
class _FakeRepo:
    params: BKTParams = BKTParams(learn_rate=0.25, slip_rate=0.10, guess_rate=0.20)
    state: BKTState = BKTState(student_id="s1", concept_id="kinematics_basic", mastery_probability=0.50, practice_count=0)

    def get_parameters(self, concept_id: str) -> BKTParams:
        return self.params

    def get_state(self, student_id: str, concept_id: str) -> BKTState:
        return self.state

    def save_state(self, student_id: str, concept_id: str, mastery: float) -> None:
        self.state.mastery_probability = mastery
        self.state.practice_count += 1

    def log_update(self, *args, **kwargs) -> None:
        return None

class _FakeMeta:
    def __init__(self, bloom="Apply", diff=1.0, t=120):
        self._qm = QuestionMetadata(
            question_id="PHY_MECH_0002",
            difficulty_calibrated=diff,
            bloom_level=bloom,
            estimated_time_seconds=t,
            required_process_skills=["kinematics"]
        )
    def get(self, qid: str):
        return self._qm

@pytest.mark.asyncio
async def test_update_mastery_with_context_and_constraints():
    svc = AdvancedBKTService()
    # inject fakes
    svc.repo = _FakeRepo()
    svc.qmeta = _FakeMeta()

    out: MasteryUpdate = await svc.update_mastery(
        student_id="s1",
        concept_id="kinematics_basic",
        is_correct=True,
        question_id="PHY_MECH_0002",
        response_time_ms=1800
    )

    # canonical behavior: correct answer should increase mastery
    assert out.new_mastery > out.previous_mastery

    # feasibility: identifiability, ordering, and bounds are respected
    p = out.adjusted_params
    assert 0.001 <= p.slip_rate <= 0.3
    assert 0.001 <= p.guess_rate <= 0.5
    assert 0.001 <= p.learn_rate <= 0.5
    assert (p.slip_rate + p.guess_rate) < 0.999
    assert (1.0 - p.slip_rate) > p.guess_rate

    # explanation contains both context and BKT internals
    assert "context" in out.explanation
    assert "param_adjustments" in out.explanation
    assert "bkt" in out.explanation
