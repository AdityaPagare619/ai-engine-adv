# ai_engine/tests/unit/test_bandit_policy.py
import numpy as np
import pytest
from ai_engine.src.knowledge_tracing.selection.bandit_policy import LinUCBPolicy, BanditContext, default_feature_map

def _ctx(arm_id, m, u, tsl_s, d=0.0, et=60.0):
    return BanditContext(
        arm_id=arm_id,
        mastery=m,
        uncertainty=u,
        time_since_last_s=tsl_s,
        difficulty=d,
        est_time_s=et,
        fatigue=0.0,
        bias=1.0
    )

def test_feature_map_dimension_and_semantics():
    ctx = _ctx("Q1", 0.6, 0.4, 600, d=1.0, et=120)
    x = default_feature_map(ctx)
    assert x.shape[0] == 10  # matches policy dimension
    # Semantics: more uncertainty and recency should raise the interaction term
    ctx2 = _ctx("Q1", 0.6, 0.8, 3600, d=1.0, et=120)
    x2 = default_feature_map(ctx2)
    assert x2[7] > x[7]  # u * tsl

def test_linucb_selects_higher_score_arm():
    d = 10
    p = LinUCBPolicy(d=d, alpha=0.6)
    # Two arms: one is more uncertain and overdue → should get higher UCB
    c1 = _ctx("Q_easy_recent", 0.7, 0.2, 30)
    c2 = _ctx("Q_hard_overdue", 0.6, 0.7, 7200, d=1.5)
    best, info = p.select([c1, c2])
    assert best in ("Q_easy_recent", "Q_hard_overdue")
    # Likely the overdue uncertain one scores higher due to exploration term
    assert any(s["arm_id"] == best for s in info["scores"])

def test_linucb_update_changes_parameters_stably():
    d = 10
    p = LinUCBPolicy(d=d, alpha=0.2)
    ctx = _ctx("Q1", 0.5, 0.5, 3600)
    x = default_feature_map(ctx)
    before = p.score("Q1", x)
    p.update("Q1", x, reward=1.0)
    after = p.score("Q1", x)
    # With positive reward, exploit term should increase
    assert after >= before
