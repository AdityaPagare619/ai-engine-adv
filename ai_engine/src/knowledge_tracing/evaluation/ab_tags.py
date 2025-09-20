# ai_engine/src/knowledge_tracing/evaluation/ab_tags.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass(frozen=True)
class ABContext:
    cohort_id: str
    enable_sakt: bool
    enable_bandit: bool
    enable_hlr: bool
    alpha_bandit: float

def cohort_from_flags(
    *,
    enable_sakt: bool,
    enable_bandit: bool,
    enable_hlr: bool,
    alpha_bandit: float = 0.6
) -> ABContext:
    """
    Deterministically derives a cohort_id from feature flags for A/B evaluation and logging.
    """
    cid = f"S{'1' if enable_sakt else '0'}-B{'1' if enable_bandit else '0'}-H{'1' if enable_hlr else '0'}-A{alpha_bandit:.2f}"
    return ABContext(
        cohort_id=cid,
        enable_sakt=enable_sakt,
        enable_bandit=enable_bandit,
        enable_hlr=enable_hlr,
        alpha_bandit=float(alpha_bandit),
    )

def attach_cohort_to_eval_details(details: Dict[str, Any], ab: ABContext) -> Dict[str, Any]:
    """
    Adds cohort_id and flags into evaluation 'details' blob before persistence.
    """
    meta = {
        "cohort_id": ab.cohort_id,
        "flags": {
            "enable_sakt": ab.enable_sakt,
            "enable_bandit": ab.enable_bandit,
            "enable_hlr": ab.enable_hlr,
            "alpha_bandit": ab.alpha_bandit,
        }
    }
    out = dict(details or {})
    out.update(meta)
    return out
