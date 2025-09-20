# ai_engine/tests/unit/test_ensemble_gate.py
import pytest
from ai_engine.src.knowledge_tracing.models.ensemble_gate import BKTSAKTEnsembleGate, EnsembleConfig
from ai_engine.src.knowledge_tracing.models.sakt_model import SAKTAttentionModel
from ai_engine.src.knowledge_tracing.bkt.repository import BKTParams

def test_ensemble_respects_weight_bounds_and_uses_bkt_for_short_sequences():
    sakt = SAKTAttentionModel()
    sakt.is_loaded = True
    gate = BKTSAKTEnsembleGate(sakt=sakt, cfg=EnsembleConfig(min_seq_for_sakt=10, bkt_weight_floor=0.3, sakt_weight_cap=0.7))
    params = BKTParams(learn_rate=0.25, slip_rate=0.10, guess_rate=0.20)
    seq = [{"question_id": "q1", "is_correct": 1}] * 3  # shorter than min_seq_for_sakt
    out = gate.predict_next_correctness(bkt_mastery=0.6, bkt_params=params, sequence=seq, uncertainty=0.3, bkt_calibration_error=0.05)
    assert out["flags"]["use_sakt"] is False
    assert out["weights"]["bkt"] >= 0.3 and out["weights"]["sakt"] <= 0.7
    assert 0.0 <= out["p_ensemble"] <= 1.0

def test_ensemble_increases_sakt_weight_with_long_history_and_moderate_uncertainty():
    sakt = SAKTAttentionModel()
    sakt.is_loaded = True
    gate = BKTSAKTEnsembleGate(sakt=sakt, cfg=EnsembleConfig(min_seq_for_sakt=5, bkt_weight_floor=0.3, sakt_weight_cap=0.7))
    params = BKTParams(learn_rate=0.25, slip_rate=0.10, guess_rate=0.20)
    short = [{"question_id": "q", "is_correct": 1}] * 3
    long = [{"question_id": "q", "is_correct": 1}] * 20
    out_short = gate.predict_next_correctness(bkt_mastery=0.6, bkt_params=params, sequence=short, uncertainty=0.3)
    out_long = gate.predict_next_correctness(bkt_mastery=0.6, bkt_params=params, sequence=long, uncertainty=0.3)
    assert out_long["weights"]["sakt"] >= out_short["weights"]["sakt"]
    assert out_long["weights"]["bkt"] <= out_short["weights"]["bkt"]

def test_ensemble_biases_toward_bkt_when_calibration_is_good():
    sakt = SAKTAttentionModel()
    sakt.is_loaded = True
    gate = BKTSAKTEnsembleGate(sakt=sakt)
    params = BKTParams(learn_rate=0.25, slip_rate=0.10, guess_rate=0.20)
    seq = [{"question_id": "q", "is_correct": 1}] * 20
    out_good = gate.predict_next_correctness(bkt_mastery=0.6, bkt_params=params, sequence=seq, uncertainty=0.3, bkt_calibration_error=0.05)
    out_bad = gate.predict_next_correctness(bkt_mastery=0.6, bkt_params=params, sequence=seq, uncertainty=0.3, bkt_calibration_error=0.20)
    assert out_good["weights"]["bkt"] >= out_bad["weights"]["bkt"]
