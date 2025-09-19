import math
import asyncio
import logging
from typing import Any, Dict, Optional
from .repository import BKTRepository, BKTParams, BKTState

logger = logging.getLogger("bkt_model")

class BayesianKnowledgeTracing:
    def __init__(
        self,
        concept_id: str,
        repo: BKTRepository,
        default_params: Optional[BKTParams] = None,
    ):
        self.concept_id = concept_id
        self.repo = repo

        # Load parameters and state asynchronously, fallback to defaults
        self.params = default_params or BKTParams(learn_rate=0.3, slip_rate=0.1, guess_rate=0.2)
        self.state = None

    async def initialize(self, student_id: str):
        try:
            self.state = await asyncio.get_running_loop().run_in_executor(
                None, lambda: self.repo.get_state(student_id, self.concept_id)
            )
            self.params = await asyncio.get_running_loop().run_in_executor(
                None, lambda: self.repo.get_parameters(self.concept_id)
            )
            # Validate parameters constraints
            if self.params.slip_rate + self.params.guess_rate >= 0.9:
                raise ValueError(
                    f"Slip + guess rates too high ({self.params.slip_rate + self.params.guess_rate})"
                )
        except Exception as e:
            logger.error(f"BKT init error: {e}")
            self.state = BKTState(mastery_probability=0.5, practice_count=0)
            self.params = self.params

    def _bayes_update(self, m: float, correct: bool, response_time_ms: Optional[int]) -> float:
        slip_rate = self.params.slip_rate
        guess_rate = self.params.guess_rate

        # Modulate slip and guess based on response time
        if response_time_ms is not None:
            if response_time_ms < 1000:
                guess_rate = min(0.5, guess_rate + 0.15)
            elif response_time_ms > 30000:
                slip_rate = min(0.5, slip_rate + 0.1)

        try:
            if correct:
                numerator = m * (1 - slip_rate)
                denominator = numerator + (1 - m) * guess_rate
            else:
                numerator = m * slip_rate
                denominator = numerator + (1 - m) * (1 - guess_rate)
            denominator = max(denominator, 1e-6)
            posterior = numerator / denominator
        except Exception as e:
            logger.error(f"Numerical issue in bayes update: {e}")
            posterior = m

        return posterior

    async def update(
        self, student_id: str, correct: bool, response_time_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        if self.state is None:
            await self.initialize(student_id)

        prev_mastery = self.state.mastery_probability
        posterior = self._bayes_update(prev_mastery, correct, response_time_ms)
        new_mastery = posterior + (1 - posterior) * self.params.learn_rate
        new_mastery = min(max(new_mastery, 0.01), 0.99)
        learning_occurred = not math.isclose(prev_mastery, new_mastery)

        # Confidence interval using beta approximation
        n = max(self.state.practice_count, 1)
        confidence = max(0.0, min(1.0, 1 - 2 * math.sqrt(new_mastery * (1 - new_mastery) / n)))

        # Retry pattern for persistence
        retry_attempts = 3
        for attempt in range(retry_attempts):
            try:
                await asyncio.get_running_loop().run_in_executor(
                    None, lambda: self.repo.save_state(student_id, self.concept_id, new_mastery)
                )
                await asyncio.get_running_loop().run_in_executor(
                    None, lambda: self.repo.log_update(
                        student_id, self.concept_id, prev_mastery, new_mastery, correct, response_time_ms
                    )
                )
                break
            except Exception as ex:
                logger.error(f"Save attempt {attempt + 1} failed: {ex}")
                if attempt == retry_attempts - 1:
                    raise

        self.state = BKTState(mastery_probability=new_mastery, practice_count=n + 1)

        explanation = {
            "modulated_slip_rate": slip_rate,
            "modulated_guess_rate": guess_rate,
            "learning_rate": self.params.learn_rate,
            "response_time_ms": response_time_ms,
        }

        return {
            "previous_mastery": prev_mastery,
            "new_mastery": new_mastery,
            "confidence": confidence,
            "learning_occurred": learning_occurred,
            "explanation": explanation,
        }
