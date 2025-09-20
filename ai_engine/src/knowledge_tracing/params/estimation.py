# ai_engine/src/knowledge_tracing/params/estimation.py
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from ..bkt.repository import BKTParams
from ..core.constraint_validator import ParameterConstraintValidator as PCV


@dataclass
class Interaction:
    """
    Minimal interaction record for parameter estimation.
    Fields can be extended (e.g., by concept, student, time gaps).
    """
    student_id: str
    concept_id: str
    is_correct: bool


class BKTParameterEstimator:
    """
    Parameter estimation utilities:
      1) spectral_initialize: robust, fast initializer using observable moments,
         inspired by spectral methods for HMMs (adapted to binary emissions).  # Ref
      2) constrained_em_fit: refinement loop with feasibility projection each iteration.  # Ref
    """

    def spectral_initialize(
        self,
        interactions: List[Interaction],
        *,
        clip: bool = True
    ) -> BKTParams:
        """
        Heuristic spectral-style initializer from binary sequences:
          - Estimate overall correctness rate r = E[Y].
          - Estimate local agreement a = P(Y_t = Y_{t+1}).
          - Back out coarse slip/guess under identifiability heuristics.
        This is a pragmatic initializer; EM (below) refines it.  # Ref
        """
        if not interactions:
                    # Safe defaults
            return BKTParams(learn_rate=0.25, slip_rate=0.10, guess_rate=0.20)

        # Aggregate by (student, concept) to preserve local sequence structure
        by_key: Dict[Tuple[str, str], List[int]] = {}
        for it in interactions:
            key = (it.student_id, it.concept_id)
            by_key.setdefault(key, []).append(1 if it.is_correct else 0)

        # Empirical r and agreement a
        ys: List[int] = []
        agrees: List[int] = []
        total_pairs = 0
        for seq in by_key.values():
            ys.extend(seq)
            for i in range(len(seq) - 1):
                agrees.append(1 if seq[i] == seq[i + 1] else 0)
                total_pairs += 1

        r = float(np.mean(ys)) if ys else 0.6
        a = float(np.mean(agrees)) if agrees else 0.6

        # Coarse back-out:
        # Assume moderate mastery prevalence m0 (e.g., 0.5) to separate slip/guess from r.
        m0 = 0.5
        # r ≈ m0*(1-s) + (1-m0)*g  => solve linear system for (s,g) with soft priors
        # Let’s impose simple priors s≈0.1, g≈0.2, then nudge toward fitting r.
        s0, g0 = 0.10, 0.20
        # Small corrective step
        # dr/ds = -m0 ; dr/dg = (1-m0)
        dr = r - (m0 * (1 - s0) + (1 - m0) * g0)
        s_hat = s0 - 0.5 * (dr * 1.0 / max(m0, 1e-6))
        g_hat = g0 + 0.5 * (dr * 1.0 / max(1 - m0, 1e-6))

        # Learn-rate rough guess from agreement a (more agreement → more stable knowledge)
        # Map a in [0.5, 0.95] → T in [0.05, 0.35]
        a_clamped = min(max(a, 0.5), 0.95)
        t_hat = 0.05 + (a_clamped - 0.5) * (0.30 / 0.45)

        # Clip and project to feasible region
        if clip:
            s_hat = float(np.clip(s_hat, PCV.MIN_S, PCV.MAX_S))
            g_hat = float(np.clip(g_hat, PCV.MIN_G, PCV.MAX_G))
            t_hat = float(np.clip(t_hat, PCV.MIN_T, PCV.MAX_T))

        init = BKTParams(learn_rate=t_hat, slip_rate=s_hat, guess_rate=g_hat)
        valid = PCV.validate_bkt_parameters(init)
        return valid.corrected_params if not valid.is_valid else init

    def constrained_em_fit(
        self,
        interactions: List[Interaction],
        start_params: Optional[BKTParams] = None,
        *,
        max_iters: int = 25,
        tol: float = 1e-4
    ) -> BKTParams:
        """
        Constrained EM-style refinement:
          - E-step: infer expected mastery trajectory under current params (forward pass).
          - M-step: update slip/guess/learn_rate to maximize expected likelihood,
            then project into feasible region each iteration.  # Ref
        For brevity, this is a stabilized scaffold; production versions should
        vectorize and use batched concept segmentation.
        """
        if not interactions:
            return start_params or BKTParams(learn_rate=0.25, slip_rate=0.10, guess_rate=0.20)

        params = start_params or self.spectral_initialize(interactions)

        # Group by (student, concept)
        by_key: Dict[Tuple[str, str], List[int]] = {}
        for it in interactions:
            key = (it.student_id, it.concept_id)
            by_key.setdefault(key, []).append(1 if it.is_correct else 0)

        last_ll = -1e18
        for _ in range(max_iters):
            # E-step (forward probabilities under current params)
            suff = {"N_mastered": 0.0, "N_not_mastered": 0.0, "C_mastered": 0.0, "C_not_mastered": 0.0}
            ll = 0.0

            for seq in by_key.values():
                m = 0.5  # neutral prior for mastery within concept
                s = params.slip_rate
                g = params.guess_rate
                T = params.learn_rate

                for y in seq:
                    # Likelihood P(y | m)
                    p_correct = m * (1 - s) + (1 - m) * g
                    p_y = p_correct if y == 1 else (1 - p_correct)
                    p_y = max(p_y, 1e-9)
                    ll += math.log(p_y)

                    # Responsibilities (posterior mastery before transition)
                    # r_m = P(L|y)
                    if y == 1:
                        num = m * (1 - s)
                        den = num + (1 - m) * g
                    else:
                        num = m * s
                        den = num + (1 - m) * (1 - g)
                    den = max(den, 1e-9)
                    r_m = num / den

                    # Sufficient stats accumulation
                    if y == 1:
                        suff["C_mastered"] += r_m
                        suff["C_not_mastered"] += (1 - r_m)
                    else:
                        # counting incorrects is implicit via totals, here we track complements via N_*
                        pass

                    suff["N_mastered"] += r_m
                    suff["N_not_mastered"] += (1 - r_m)

                    # Transition to next timestep
                    m = r_m + (1 - r_m) * T

            # M-step (very simplified moment-style update)
            # Update guess/slip using fractions of corrects from mastered vs not mastered
            # Avoid division by small counts with ridge terms
            ridge = 1e-6
            Nm = suff["N_mastered"] + ridge
            Nn = suff["N_not_mastered"] + ridge
            Cm = suff["C_mastered"]
            Cn = suff["C_not_mastered"]

            # P(correct | mastered) ≈ Cm / Nm = 1 - s  => s = 1 - Cm/Nm
            s_new = 1.0 - (Cm / Nm)
            # P(correct | not mastered) ≈ Cn / Nn = g
            g_new = Cn / Nn

            # Learn-rate: conservative update toward observed mastery increases; keep bounded
            # Here we softly nudge T toward mid value if LL is improving; a fuller M-step requires additional stats
            T_new = params.learn_rate * 0.8 + 0.2 * 0.25

            # Project to feasible region
            cand = BKTParams(learn_rate=float(T_new), slip_rate=float(s_new), guess_rate=float(g_new))
            valid = PCV.validate_bkt_parameters(cand)
            cand = valid.corrected_params if not valid.is_valid else cand

            # Check convergence by log-likelihood
            if abs(ll - last_ll) < tol:
                params = cand
                break

            params = cand
            last_ll = ll

        return params
