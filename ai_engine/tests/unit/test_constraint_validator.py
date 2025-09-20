# ai_engine/tests/unit/test_constraint_validator.py
import pytest
from ai_engine.src.knowledge_tracing.core.constraint_validator import (
    ParameterConstraintValidator as PCV, ValidationResult
)
from ai_engine.src.knowledge_tracing.bkt.repository import BKTParams

def is_feasible(p: BKTParams) -> bool:
    g, s, t = p.guess_rate, p.slip_rate, p.learn_rate
    # Identifiability and ordering (loose check with validator margins)
    id_ok = (g + s) < (1.0 - PCV.MARGIN)
    ord_ok = (1.0 - s) > (g + PCV.MARGIN)
    denom = max(1.0 - g, 1e-6)
    jedm_bound = (1.0 - s) / denom
    t_ok = t < (jedm_bound - PCV.MARGIN)
    box_ok = (PCV.MIN_G <= g <= PCV.MAX_G) and (PCV.MIN_S <= s <= PCV.MAX_S) and (PCV.MIN_T <= t <= PCV.MAX_T)
    return id_ok and ord_ok and t_ok and box_ok

def test_identifiability_violation_is_corrected():
    # g + s close to 1 -> should be projected down
    bad = BKTParams(learn_rate=0.4, slip_rate=0.6, guess_rate=0.45)  # sum = 1.05
    res: ValidationResult = PCV.validate_bkt_parameters(bad)
    assert res.is_valid is False  # initial invalid
    corrected = res.corrected_params
    # Re-validate corrected
    res2 = PCV.validate_bkt_parameters(corrected)
    assert res2.is_valid is True
    assert is_feasible(corrected)

def test_performance_ordering_violation_is_corrected():
    # (1 - s) <= g
    bad = BKTParams(learn_rate=0.25, slip_rate=0.25, guess_rate=0.80)  # 1-s = 0.75 <= 0.80
    res = PCV.validate_bkt_parameters(bad)
    assert res.is_valid is False
    corrected = res.corrected_params
    res2 = PCV.validate_bkt_parameters(corrected)
    assert res2.is_valid is True
    assert is_feasible(corrected)

def test_jedm_bound_enforced_on_learn_rate():
    # Force T above bound; expect shrink
    # With s=0.2, g=0.1 → bound = (1-0.2)/(1-0.1) = 0.8/0.9 ≈ 0.888...
    bad = BKTParams(learn_rate=0.95, slip_rate=0.2, guess_rate=0.1)
    res = PCV.validate_bkt_parameters(bad)
    assert res.is_valid is False
    corrected = res.corrected_params
    res2 = PCV.validate_bkt_parameters(corrected)
    assert res2.is_valid is True
    assert is_feasible(corrected)

def test_valid_params_pass_untouched():
    good = BKTParams(learn_rate=0.25, slip_rate=0.10, guess_rate=0.20)
    res = PCV.validate_bkt_parameters(good)
    assert res.is_valid is True
    assert res.violations == []
    assert res.corrected_params == good
