# ai_engine/src/knowledge_tracing/models/ensemble_gate.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np

from ..core.bkt_core import CanonicalBKTCore
from ..bkt.repository import BKTParams
from .sakt_model import SAKTAttentionModel


@dataclass
class EnsembleConfig:
    min_seq_for_sakt: int = 10            # below this, use BKT only
    max_uncertainty_for_sakt: float = 0.5 # if uncertainty too high, prefer BKT
    bkt_weight_floor: float = 0.3         # keep BKT contribution for interpretability
    sakt_weight_cap: float = 0.7          # never let SAKT fully dominate
    calibrate_to_bkt: bool = True         # bias ensemble toward BKT if calibration is poor


class BKTSAKTEnsembleGate:
    """
    Blends BKT and SAKT predictions with simple, interpretable rules:
      - Use BKT alone for short histories to preserve stability.
      - Increase SAKT weight for longer sequences and moderate uncertainty.
      - Clamp weights so BKT remains visible and calibrated.
    """

    def __init__(self, sakt: Optional[SAKTAttentionModel] = None, cfg: Optional[EnsembleConfig] = None):
        self.sakt = sakt or SAKTAttentionModel()
        self.cfg = cfg or EnsembleConfig()

    def predict_next_correctness(
        self,
        *,
        bkt_mastery: float,
        bkt_params: BKTParams,
        sequence: List[Dict[str, Any]],
        uncertainty: float,
        bkt_calibration_error: Optional[float] = None
    ) -> Dict[str, Any]:
        # Base BKT probability
        p_bkt = CanonicalBKTCore.predict_correctness_prob(bkt_mastery, bkt_params)

        # Gate rules
        use_sakt = self.sakt.is_loaded and (len(sequence) >= self.cfg.min_seq_for_sakt) and (uncertainty <= self.cfg.max_uncertainty_for_sakt)

        # SAKT prediction or fallback
        p_sakt = self.sakt.predict_correctness_prob(sequence) if use_sakt else p_bkt

        # Weighting
        w_sakt = 0.5
        if use_sakt:
            # More history → trust SAKT a bit more, within cap
            w_sakt = min(self.cfg.sakt_weight_cap, 0.35 + 0.01 * min(len(sequence), 100))
            # If BKT calibration is good, bias ensemble toward BKT
            if self.cfg.calibrate_to_bkt and bkt_calibration_error is not None and bkt_calibration_error < 0.08:
                w_sakt = max(0.35, w_sakt - 0.10)
        else:
            w_sakt = 0.0

        w_bkt = max(self.cfg.bkt_weight_floor, 1.0 - w_sakt)
        # Normalize weights in case of floor/cap effects
        total = max(w_bkt + w_sakt, 1e-6)
        w_bkt /= total
        w_sakt /= total

        p_ens = float(w_bkt * p_bkt + w_sakt * p_sakt)

        return {
            "p_bkt": float(p_bkt),
            "p_sakt": float(p_sakt),
            "p_ensemble": float(p_ens),
            "weights": {"bkt": float(w_bkt), "sakt": float(w_sakt)},
            "flags": {"use_sakt": bool(use_sakt)},
        }
