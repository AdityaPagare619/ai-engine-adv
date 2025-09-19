import pytest
from knowledge_tracing.bkt.model import BayesianKnowledgeTracing
from knowledge_tracing.bkt.repository import BKTState, BKTParams

class DummyRepo:
    def __init__(self):
        self.params = BKTParams(0.3, 0.1, 0.2)
        self.state = BKTState(0.5, 0)

    def get_parameters(self, concept_id):
        return self.params

    def get_state(self, student_id, concept_id):
        return self.state

    def get_practice_count(self, student_id, concept_id):
        return self.state.practice_count

    def save_state(self, student_id, concept_id, mastery):
        self.state = BKTState(mastery, self.state.practice_count + 1)

    def log_update(self, *args, **kwargs):
        pass

@pytest.fixture
def engine():
    return BayesianKnowledgeTracing("concept1", repo=DummyRepo())

def test_correct_response_increases_mastery(engine):
    prev = engine.mastery
    result = engine.update("s1", True, 5000)
    assert result["new_mastery"] > prev
    assert result["learning_occurred"]

def test_incorrect_response_decreases_mastery(engine):
    engine.mastery = 0.8
    result = engine.update("s1", False, 10000)
    assert result["new_mastery"] < 0.8

def test_confidence_bounds(engine):
    res = engine.update("s1", True, 1000)
    assert 0.0 <= res["confidence"] <= 1.0

def test_practice_count_increment(engine):
    initial = engine.repo.get_practice_count("s1", "concept1")
    engine.update("s1", True, None)
    assert engine.repo.get_practice_count("s1", "concept1") == initial + 1
