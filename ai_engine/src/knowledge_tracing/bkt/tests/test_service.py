import pytest
from knowledge_tracing.bkt.service import update_knowledge_state
from knowledge_tracing.bkt.schemas import TraceRequest

class DummyEngine:
    def __init__(self, concept_id, repo):
        pass
    def update(self, student_id, correct, response_time_ms):
        return {
            "previous_mastery": 0.5,
            "new_mastery": 0.6,
            "confidence": 0.8,
            "learning_occurred": True
        }

@pytest.mark.asyncio
async def test_service_happy_path(monkeypatch):
    monkeypatch.setattr(
        "knowledge_tracing.bkt.service.BayesianKnowledgeTracing",
        lambda concept_id, repo: DummyEngine(concept_id, repo)
    )
    req = TraceRequest(
        student_id="s1",
        concept_id="c1",
        is_correct=True,
        response_time_ms=2000
    )
    res = await update_knowledge_state(req)
    assert res.previous_mastery == 0.5
    assert res.new_mastery == 0.6
    assert res.confidence == 0.8
    assert res.learning_occurred
