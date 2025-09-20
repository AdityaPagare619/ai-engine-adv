# ai_engine/tests/unit/test_params_estimation.py
import numpy as np
import pytest
from ai_engine.src.knowledge_tracing.params.estimation import BKTParameterEstimator, Interaction
from ai_engine.src.knowledge_tracing.bkt.repository import BKTParams
from ai_engine.src.knowledge_tracing.core.constraint_validator import ParameterConstraintValidator as PCV

def _gen_synthetic_seq(n=80, mastered_prob=0.6, slip=0.12, guess=0.18, seed=13):
    rng = np.random.default_rng(seed)
    # Binary latent mastery (fixed across seq for simplicity of synthetic generation)
    L = (rng.random() < mastered_prob)
    ys = []
    for _ in range(n):
        p = (1 - slip) if L else guess
        ys.append(int(rng.random() < p))
    return ys

def _make_interactions(student="s1", concept="c1", ys=None):
    ys = ys or [0, 1, 1, 0, 1]
    return [Interaction(student_id=student, concept_id=concept, is_correct=bool(y)) for y in ys]

def test_spectral_initialize_feasible_and_reasonable():
    ys = _gen_synthetic_seq(n=120, mastered_prob=0.55, slip=0.10, guess=0.20, seed=7)
    inter = _make_interactions(ys=ys)
    est = BKTParameterEstimator()
    p: BKTParams = est.spectral_initialize(inter)
    # Feasibility and practical ranges
    assert PCV.MIN_S <= p.slip_rate <= PCV.MAX_S
    assert PCV.MIN_G <= p.guess_rate <= PCV.MAX_G
    assert PCV.MIN_T <= p.learn_rate <= PCV.MAX_T
    # Identifiability & ordering
    assert (p.slip_rate + p.guess_rate) < (1.0 - PCV.MARGIN)
    assert (1.0 - p.slip_rate) > (p.guess_rate + PCV.MARGIN)

def test_constrained_em_fit_converges_and_remains_feasible():
    ys = _gen_synthetic_seq(n=200, mastered_prob=0.50, slip=0.12, guess=0.18, seed=21)
    inter = _make_interactions(ys=ys)
    est = BKTParameterEstimator()
    p0 = est.spectral_initialize(inter)
    p1 = est.constrained_em_fit(interactions=inter, start_params=p0, max_iters=10, tol=1e-5)
    # Feasibility retained
    assert PCV.MIN_S <= p1.slip_rate <= PCV.MAX_S
    assert PCV.MIN_G <= p1.guess_rate <= PCV.MAX_G
    assert PCV.MIN_T <= p1.learn_rate <= PCV.MAX_T
    assert (p1.slip_rate + p1.guess_rate) < (1.0 - PCV.MARGIN)
    assert (1.0 - p1.slip_rate) > (p1.guess_rate + PCV.MARGIN)
