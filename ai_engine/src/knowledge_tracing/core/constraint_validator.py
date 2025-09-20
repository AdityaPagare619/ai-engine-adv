# ai_engine/src/knowledge_tracing/core/constraint_validator.py
from typing import List, NamedTuple
from ..bkt.repository import BKTParams

class ValidationResult(NamedTuple):
    is_valid: bool
    violations: List[str]
    corrected_params: BKTParams

class ParameterConstraintValidator:
    """
    First-principles parameter constraints (identifiability and performance ordering)
    with simple projection into a feasible region.
    """

    # Practical bounds for stability (can be tuned per domain)
    MIN_T, MAX_T = 0.001, 0.50     # Learn rate
    MIN_S, MAX_S = 0.001, 0.30     # Slip
    MIN_G, MAX_G = 0.001, 0.50     # Guess
    MARGIN = 0.01                  # Safety margin for strict inequalities

    @classmethod
    def validate_bkt_parameters(cls, params: BKTParams) -> ValidationResult:
        v: List[str] = []
        t = float(params.learn_rate)
        s = float(params.slip_rate)
        g = float(params.guess_rate)

        # Box constraints
        if not (cls.MIN_T <= t <= 1.0 - cls.MIN_T):
            v.append(f"Learn rate out of bounds: {t}")
        if not (cls.MIN_S <= s <= cls.MAX_S):
            v.append(f"Slip out of bounds: {s}")
        if not (cls.MIN_G <= g <= cls.MAX_G):
            v.append(f"Guess out of bounds: {g}")

        # Identifiability: P(G) + P(S) < 1
        if (g + s) >= (1.0 - cls.MARGIN):
            v.append(f"Identifiability violated: guess+slip={g+s:.4f} >= 1")

        # Performance ordering: (1 - S) > G
        if (1.0 - s) <= (g + cls.MARGIN):
            v.append(f"Performance ordering violated: (1-S) <= G → {(1.0 - s):.4f} <= {g:.4f}")

        # JEDM bound on transition: P(T) < (1 - P(S)) / (1 - P(G))
        denom = max(1.0 - g, 1e-6)
        jedm_bound = (1.0 - s) / denom
        if t >= (jedm_bound - cls.MARGIN):
            v.append(f"JEDM bound violated: T={t:.4f} >= {(jedm_bound - cls.MARGIN):.4f}")

        corrected = cls.project_to_feasible(params) if v else params
        return ValidationResult(is_valid=(len(v) == 0), violations=v, corrected_params=corrected)

    @classmethod
    def project_to_feasible(cls, params: BKTParams) -> BKTParams:
        """
        Lightweight projection into a feasible set without external solvers.
        Strategy:
          1) Clamp to box bounds.
          2) Reduce (g + s) if near/over 1 by proportional scaling.
          3) Enforce (1 - s) > g + margin by reducing g (prefer) or s if needed.
          4) Enforce JEDM upper bound on t by shrinking t if needed.
        """
        t = min(max(params.learn_rate, cls.MIN_T), min(1.0 - cls.MIN_T, cls.MAX_T))
        s = min(max(params.slip_rate, cls.MIN_S), cls.MAX_S)
        g = min(max(params.guess_rate, cls.MIN_G), cls.MAX_G)

        # Step 2: ensure g+s <= 1 - margin
        total = g + s
        max_total = 1.0 - cls.MARGIN
        if total > max_total:
            scale = max_total / total
            g *= scale
            s *= scale

        # Step 3: enforce (1 - s) > g + margin  =>  g < 1 - s - margin
        max_g = max(cls.MIN_G, (1.0 - s) - cls.MARGIN)
        if g >= max_g:
            g = max_g - 1e-6
            g = min(max(g, cls.MIN_G), cls.MAX_G)

        # Step 4: enforce JEDM bound on t
        denom = max(1.0 - g, 1e-6)
        jedm_bound = (1.0 - s) / denom
        max_t = max(cls.MIN_T, min(cls.MAX_T, jedm_bound - cls.MARGIN))
        if t > max_t:
            t = max_t

        return BKTParams(learn_rate=float(t), slip_rate=float(s), guess_rate=float(g))
