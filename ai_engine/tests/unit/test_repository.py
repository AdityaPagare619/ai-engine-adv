# ai_engine/tests/unit/test_repository.py
import pytest
from typing import Any, Dict
from ai_engine.src.knowledge_tracing.bkt.repository import (
    BKTRepository, BKTParams, BKTState
)

class _FakeExec:
    def __init__(self, data): self.data = data
    def execute(self): return self

class _FakeQuery:
    def __init__(self, table_name: str, store: Dict[str, Any]):
        self.table_name = table_name
        self.store = store
        self._where = {}
        self._select = None
        self._single = False
        self._payload = None

    def select(self, cols: str):
        self._select = cols
        return self

    def eq(self, key: str, value: Any):
        self._where[key] = value
        return self

    def single(self):
        self._single = True
        return self

    def upsert(self, payload):
        self._payload = payload
        # emulate write
        if isinstance(payload, dict):
            key = (payload.get("student_id"), payload.get("concept_id"))
            self.store.setdefault(self.table_name, {})
            self.store[self.table_name][key] = payload
        elif isinstance(payload, list):
            self.store.setdefault(self.table_name, {})
            for row in payload:
                k = row.get("question_id")
                self.store[self.table_name][k] = row
        return self

    def insert(self, payload):
        self._payload = payload
        self.store.setdefault(self.table_name, [])
        self.store[self.table_name].append(payload)
        return self

    @property
    def data(self):
        # emulate read with filters
        tbl = self.store.get(self.table_name, {})
        # parameters table keyed by concept_id
        if self.table_name == "bkt_parameters":
            cid = self._where.get("concept_id")
            row = tbl.get(cid) if isinstance(tbl, dict) else None
            return row
        # knowledge states keyed by (student_id, concept_id)
        if self.table_name == "bkt_knowledge_states":
            sid = self._where.get("student_id")
            cid = self._where.get("concept_id")
            row = tbl.get((sid, cid)) if isinstance(tbl, dict) else None
            return row
        # logs append-only
        if self.table_name == "bkt_update_logs":
            return self.store.get(self.table_name, [])
        return None

    def execute(self):
        return self

class _FakeSupabase:
    def __init__(self):
        self._store: Dict[str, Any] = {
            "bkt_parameters": {},
            "bkt_knowledge_states": {},
            "bkt_update_logs": []
        }

    def table(self, name: str):
        return _FakeQuery(name, self._store)

@pytest.fixture
def repo(monkeypatch):
    fake = _FakeSupabase()
    # seed parameters
    fake._store["bkt_parameters"]["kinematics_basic"] = {
        "concept_id": "kinematics_basic", "learn_rate": 0.25, "slip_rate": 0.10, "guess_rate": 0.20
    }
    r = BKTRepository()
    # monkeypatch internal client
    r._client = fake
    return r

def test_get_parameters_reads_expected_values(repo):
    params = repo.get_parameters("kinematics_basic")
    assert isinstance(params, BKTParams)
    assert params.learn_rate == 0.25
    assert params.slip_rate == 0.10
    assert params.guess_rate == 0.20

def test_get_state_defaults_when_missing(repo):
    st = repo.get_state("s1", "kinematics_basic")
    assert isinstance(st, BKTState)
    assert 0.0 <= st.mastery_probability <= 1.0
    assert int(st.practice_count) == 0

def test_save_state_and_log_update(repo):
    prev = 0.50
    new = 0.62
    repo.save_state("s1", "kinematics_basic", new)
    repo.log_update("s1", "kinematics_basic", prev, new, True, 2300)

    # verify persisted knowledge state
    ks = repo._client.table("bkt_knowledge_states") \
        .eq("student_id", "s1").eq("concept_id", "kinematics_basic").single().execute().data
    assert ks is not None
    assert abs(ks["mastery_probability"] - new) < 1e-9
    assert int(ks["practice_count"]) >= 1

    # verify log append
    logs = repo._client.table("bkt_update_logs").select("*").execute().data
    assert isinstance(logs, list)
    assert len(logs) >= 1
