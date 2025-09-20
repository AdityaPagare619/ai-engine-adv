# ai_engine/tests/unit/test_hlr_scheduler.py
import pytest
from ai_engine.src.knowledge_tracing.scheduling.hlr_scheduler import HalfLifeRegressionScheduler

def test_half_life_increases_with_mastery_and_correct():
    hlr = HalfLifeRegressionScheduler()
    h_low = hlr.estimate_half_life_minutes(mastery=0.30, last_correct=False)
    h_high = hlr.estimate_half_life_minutes(mastery=0.80, last_correct=True)
    assert h_high > h_low
    # Bounds respected [5 min, 14 days]
    assert 5.0 <= h_low <= (14.0 * 24.0 * 60.0)
    assert 5.0 <= h_high <= (14.0 * 24.0 * 60.0)

def test_optimal_spacing_monotone_in_retention():
    hlr = HalfLifeRegressionScheduler()
    out_lo = hlr.optimal_spacing_minutes(mastery=0.6, last_correct=True, retention_target=0.70)
    out_hi = hlr.optimal_spacing_minutes(mastery=0.6, last_correct=True, retention_target=0.95)
    # For exponential forgetting p=exp(-Δt/h), higher retention target implies a SHORTER gap.
    assert out_hi["next_review_in_minutes"] < out_lo["next_review_in_minutes"]

def test_optimal_spacing_respects_bounds():
    hlr = HalfLifeRegressionScheduler()
    out = hlr.optimal_spacing_minutes(mastery=0.5, last_correct=False, retention_target=0.99)
    assert 1.0 <= out["next_review_in_minutes"] <= (30.0 * 24.0 * 60.0)
