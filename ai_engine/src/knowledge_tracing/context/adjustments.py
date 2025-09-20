# ai_engine/src/knowledge_tracing/context/adjustments.py
from typing import Optional, Dict, Any
from ..bkt.repository import BKTParams, QuestionMetadata
from ..core.constraint_validator import ParameterConstraintValidator


def adjust_params_for_context(
    base: BKTParams,
    meta: Optional[QuestionMetadata],
    response_time_ms: Optional[int] = None
) -> Dict[str, Any]:
    """
    Adjust slip and guess using calibrated difficulty, Bloom taxonomy, and response time,
    then project into a feasible region to satisfy identifiability and performance ordering.
    Returns:
        {
            "adjusted": BKTParams,
            "explanation": { ... }
        }
    """
    s = float(base.slip_rate)
    g = float(base.guess_rate)
    t = float(base.learn_rate)

    # Difficulty-based slip modulation (harder items slightly increase slip)
    diff_adj = 0.0
    diff = meta.difficulty_calibrated if (meta and meta.difficulty_calibrated is not None) else None
    if diff is not None:
        diff = max(0.0, diff)  # ignore negative (easier) for additive slip
        diff_adj = 0.05 * diff
        s = s + diff_adj

    # Bloom-based guess modulation (higher-order cognition tends to reduce guessing benefit)
    bloom_adj_map = {
        "Remember": -0.05,
        "Understand": 0.00,
        "Apply": 0.02,
        "Analyze": 0.05,
        "Evaluate": 0.08,
        "Create": 0.10,
    }
    bloom_adj = 0.0
    bloom = meta.bloom_level if meta and meta.bloom_level else None
    if bloom in bloom_adj_map:
        bloom_adj = bloom_adj_map[bloom]
        g = g + bloom_adj

    # Response-time effects: very fast corrects may indicate guessy behavior; very long times may raise slips
    rt_adj_guess = 0.0
    rt_adj_slip = 0.0
    if response_time_ms is not None:
        if response_time_ms < 1000:
            rt_adj_guess = 0.05  # modest increase vs model-level modulation
            g = g + rt_adj_guess
        elif response_time_ms > 30000:
            rt_adj_slip = 0.03
            s = s + rt_adj_slip

    # Clamp to broad practical bounds before feasibility projection
    s = min(max(s, ParameterConstraintValidator.MIN_S), ParameterConstraintValidator.MAX_S)
    g = min(max(g, ParameterConstraintValidator.MIN_G), ParameterConstraintValidator.MAX_G)
    t = min(max(t, ParameterConstraintValidator.MIN_T), ParameterConstraintValidator.MAX_T)

    adjusted = BKTParams(learn_rate=t, slip_rate=s, guess_rate=g)

    # Enforce first-principles constraints (identifiability, performance ordering, JEDM bound)
    result = ParameterConstraintValidator.validate_bkt_parameters(adjusted)
    final_params = result.corrected_params

    explanation = {
        "base_params": {"learn_rate": float(base.learn_rate), "slip_rate": float(base.slip_rate), "guess_rate": float(base.guess_rate)},
        "difficulty": float(diff) if diff is not None else None,
        "bloom": bloom,
        "response_time_ms": int(response_time_ms) if response_time_ms is not None else None,
        "diff_adj_slip": float(diff_adj),
        "bloom_adj_guess": float(bloom_adj),
        "rt_adj_guess": float(rt_adj_guess),
        "rt_adj_slip": float(rt_adj_slip),
        "post_modulation_params": {"learn_rate": float(t), "slip_rate": float(s), "guess_rate": float(g)},
        "violations": result.violations,
        "final_params": {"learn_rate": float(final_params.learn_rate), "slip_rate": float(final_params.slip_rate), "guess_rate": float(final_params.guess_rate)},
    }

    return {"adjusted": final_params, "explanation": explanation}
