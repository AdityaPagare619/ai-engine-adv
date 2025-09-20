# ai_engine/src/knowledge_tracing/core/bkt_core.py
import math
from typing import Dict, Any, Tuple
from ..bkt.repository import BKTParams

EPS = 1e-9

class CanonicalBKTCore:
    """
    Canonical Bayesian Knowledge Tracing (Corbett & Anderson 1995) with numerically safe updates.

    Posterior after a correct response:
        P(L_t | correct) = [P(L_t) * (1 - P(S))] /
                           [P(L_t) * (1 - P(S)) + (1 - P(L_t)) * P(G)]
    Posterior after an incorrect response:
        P(L_t | incorrect) = [P(L_t) * P(S)] /
                             [P(L_t) * P(S) + (1 - P(L_t)) * (1 - P(G))]
    Transition:
        P(L_{t+1}) = P(L_t | obs) + (1 - P(L_t | obs)) * P(T)
    """

    @staticmethod
    def predict_correctness_prob(mastery: float, params: BKTParams) -> float:
        """
        Predicts P(correct) given current mastery and parameters:
            P(correct) = mastery * (1 - slip) + (1 - mastery) * guess
        """
        slip = min(max(params.slip_rate, 0.0), 1.0)
        guess = min(max(params.guess_rate, 0.0), 1.0)
        m = min(max(mastery, 0.0), 1.0)
        return m * (1.0 - slip) + (1.0 - m) * guess

    @staticmethod
    def posterior(mastery: float, correct: bool, params: BKTParams) -> Tuple[float, Dict[str, float]]:
        """
        Computes posterior P(L_t | obs) with numerical safeguards and returns explanation terms.
        """
        m = min(max(mastery, 0.0), 1.0)
        s = min(max(params.slip_rate, 0.0), 1.0)
        g = min(max(params.guess_rate, 0.0), 1.0)

        if correct:
            num = m * (1.0 - s)
            den = num + (1.0 - m) * g
        else:
            num = m * s
            den = num + (1.0 - m) * (1.0 - g)

        den = max(den, EPS)
        post = num / den
        post = min(max(post, EPS), 1.0 - EPS)

        return post, {
            "numerator": float(num),
            "denominator": float(den),
            "slip": float(s),
            "guess": float(g),
            "prev_mastery": float(m),
        }

    @staticmethod
    def transition(posterior: float, params: BKTParams) -> float:
        """
        Applies learning transition:
            P(L_{t+1}) = posterior + (1 - posterior) * learn_rate
        """
        post = min(max(posterior, 0.0), 1.0)
        t = min(max(params.learn_rate, 0.0), 1.0)
        next_m = post + (1.0 - post) * t
        return min(max(next_m, EPS), 1.0 - EPS)

    @staticmethod
    def predict_correctness(mastery: float, slip_rate: float, guess_rate: float) -> float:
        """
        Alias method for backward compatibility.
        Predicts P(correct) given current mastery and slip/guess rates.
        """
        m = min(max(mastery, 0.0), 1.0)
        slip = min(max(slip_rate, 0.0), 1.0)
        guess = min(max(guess_rate, 0.0), 1.0)
        return m * (1.0 - slip) + (1.0 - m) * guess

    @staticmethod
    def posterior_mastery(mastery: float, correct: bool, learn_rate: float, slip_rate: float, guess_rate: float) -> float:
        """
        Alias method for backward compatibility.
        Computes full BKT update: posterior + transition.
        """
        # Create BKTParams for internal use
        params = BKTParams(learn_rate=learn_rate, slip_rate=slip_rate, guess_rate=guess_rate)
        
        # Get posterior
        post, _ = CanonicalBKTCore.posterior(mastery, correct, params)
        
        # Apply transition
        new_mastery = CanonicalBKTCore.transition(post, params)
        
        return new_mastery

    @classmethod
    def update(cls, mastery: float, correct: bool, params: BKTParams) -> Dict[str, Any]:
        """
        Full update step: posterior -> transition with rich explanation.
        Returns:
            {
                'previous_mastery': float,
                'posterior_mastery': float,
                'new_mastery': float,
                'p_correct_pred': float,
                'explanation': { ... }
            }
        """
        # Predict before seeing the outcome (useful for AUC/Brier calculations)
        p_correct_pred = cls.predict_correctness_prob(mastery, params)

        post, expl = cls.posterior(mastery, correct, params)
        new_m = cls.transition(post, params)

        return {
            "previous_mastery": float(mastery),
            "posterior_mastery": float(post),
            "new_mastery": float(new_m),
            "p_correct_pred": float(p_correct_pred),
            "explanation": {
                **expl,
                "learn_rate": float(params.learn_rate),
                "transition_applied": True,
                "observed_correct": bool(correct),
            },
        }
