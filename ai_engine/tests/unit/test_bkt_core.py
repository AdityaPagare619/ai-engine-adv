# ai_engine/tests/unit/test_bkt_core.py
import math
import pytest
from ai_engine.src.knowledge_tracing.core.bkt_core import CanonicalBKTCore
from ai_engine.src.knowledge_tracing.bkt.repository import BKTParams

TOL = 1e-6

def test_predict_correctness_prob_bounds():
    params = BKTParams(learn_rate=0.3, slip_rate=0.1, guess_rate=0.2)
    for m in [0.0, 0.25, 0.5, 0.75, 1.0]:
        p = CanonicalBKTCore.predict_correctness_prob(m, params)
        assert 0.0 <= p <= 1.0

def test_posterior_correct_matches_formula():
    m = 0.5
    params = BKTParams(learn_rate=0.3, slip_rate=0.1, guess_rate=0.2)
    post, expl = CanonicalBKTCore.posterior(m, True, params)
    # Manual formula: P(L|correct) = m*(1-s) / [m*(1-s) + (1-m)*g]
    s, g = params.slip_rate, params.guess_rate
    num = m * (1.0 - s)
    den = num + (1.0 - m) * g
    expected = num / den
    assert abs(post - expected) < 1e-9

def test_posterior_incorrect_matches_formula():
    m = 0.5
    params = BKTParams(learn_rate=0.3, slip_rate=0.1, guess_rate=0.2)
    post, expl = CanonicalBKTCore.posterior(m, False, params)
    # Manual formula: P(L|incorrect) = m*s / [m*s + (1-m)*(1-g)]
    s, g = params.slip_rate, params.guess_rate
    num = m * s
    den = num + (1.0 - m) * (1.0 - g)
    expected = num / den
    assert abs(post - expected) < 1e-9

def test_transition_step_matches_formula():
    post = 0.6
    params = BKTParams(learn_rate=0.3, slip_rate=0.1, guess_rate=0.2)
    new_m = CanonicalBKTCore.transition(post, params)
    expected = post + (1.0 - post) * params.learn_rate
    assert abs(new_m - expected) < 1e-12

def test_full_update_increases_on_correct_sequence():
    params = BKTParams(learn_rate=0.25, slip_rate=0.1, guess_rate=0.2)
    m = 0.4
    # Two correct answers should increase mastery monotonically
    out1 = CanonicalBKTCore.update(m, True, params)
    out2 = CanonicalBKTCore.update(out1["new_mastery"], True, params)
    assert out1["new_mastery"] > m
    assert out2["new_mastery"] > out1["new_mastery"]

def test_full_update_handles_incorrect_without_nan():
    params = BKTParams(learn_rate=0.25, slip_rate=0.1, guess_rate=0.2)
    m = 0.7
    out = CanonicalBKTCore.update(m, False, params)
    assert 0.0 < out["posterior_mastery"] < 1.0
    assert 0.0 < out["new_mastery"] < 1.0

def test_predicted_correctness_formula_consistency():
    params = BKTParams(learn_rate=0.3, slip_rate=0.1, guess_rate=0.2)
    m = 0.65
    p = CanonicalBKTCore.predict_correctness_prob(m, params)
    # p = m*(1-s) + (1-m)*g
    expected = m * (1.0 - params.slip_rate) + (1.0 - m) * params.guess_rate
    assert abs(p - expected) < 1e-12
