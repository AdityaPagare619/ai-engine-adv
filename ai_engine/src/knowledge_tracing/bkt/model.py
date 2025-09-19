import math
import asyncio
import logging
from typing import Any, Dict, Optional
from .repository import (
    BKTRepository,
    BKTParams,
    BKTState,
    QuestionMetadata,
)

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
        self.params = default_params or BKTParams(
            learn_rate=0.3, slip_rate=0.1, guess_rate=0.2
        )
        self.state: Optional[BKTState] = None
        self.question_metadata: Optional[QuestionMetadata] = None

    async def initialize(self, student_id: str):
        """Initialize without question context (baseline)."""
        try:
            self.state = await asyncio.get_running_loop().run_in_executor(
                None, lambda: self.repo.get_state(student_id, self.concept_id)
            )
            self.params = await asyncio.get_running_loop().run_in_executor(
                None, lambda: self.repo.get_parameters(self.concept_id)
            )
            # Validate parameter constraints
            if self.params.slip_rate + self.params.guess_rate >= 0.9:
                raise ValueError(
                    f"Slip + guess rates too high ({self.params.slip_rate + self.params.guess_rate})"
                )
        except Exception as e:
            logger.error(f"BKT init error: {e}")
            self.state = BKTState(mastery_probability=0.5, practice_count=0)
            self.params = self.params

    async def initialize_with_context(
        self, student_id: str, question_id: Optional[str] = None
    ):
        """Initialize with optional question context for better parameter adjustment."""
        try:
            self.state = await asyncio.get_running_loop().run_in_executor(
                None, lambda: self.repo.get_state(student_id, self.concept_id)
            )

            # Get question metadata if available
            question_metadata = None
            if question_id:
                question_metadata = await asyncio.get_running_loop().run_in_executor(
                    None, lambda: self.repo.get_question_metadata(question_id)
                )

            # Get parameters with question context
            self.params = await asyncio.get_running_loop().run_in_executor(
                None,
                lambda: self.repo.get_parameters_with_context(
                    self.concept_id, question_metadata
                ),
            )

            # Store question context for explanation
            self.question_metadata = question_metadata

            # Validate parameter constraints
            if self.params.slip_rate + self.params.guess_rate >= 0.9:
                raise ValueError(
                    f"Slip + guess rates too high ({self.params.slip_rate + self.params.guess_rate})"
                )
        except Exception as e:
            logger.error(f"BKT init error: {e}")
            self.state = BKTState(mastery_probability=0.5, practice_count=0)
            self.params = self.params
            self.question_metadata = None

    def _bayes_update(
        self, m: float, correct: bool, response_time_ms: Optional[int]
    ) -> (float, float, float):
        """Perform Bayesian update and return posterior + modulated slip & guess."""
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

        return posterior, slip_rate, guess_rate

    async def update(
        self,
        student_id: str,
        correct: bool,
        response_time_ms: Optional[int] = None,
        question_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if self.state is None:
            await self.initialize_with_context(student_id, question_id)

        prev_mastery = self.state.mastery_probability
        posterior, slip_rate, guess_rate = self._bayes_update(
            prev_mastery, correct, response_time_ms
        )
        new_mastery = posterior + (1 - posterior) * self.params.learn_rate
        new_mastery = min(max(new_mastery, 0.01), 0.99)
        learning_occurred = not math.isclose(prev_mastery, new_mastery)

        # Confidence interval using beta approximation
        n = max(self.state.practice_count, 1)
        confidence = max(
            0.0,
            min(1.0, 1 - 2 * math.sqrt(new_mastery * (1 - new_mastery) / n)),
        )

        # Retry pattern for persistence
        retry_attempts = 3
        for attempt in range(retry_attempts):
            try:
                await asyncio.get_running_loop().run_in_executor(
                    None,
                    lambda: self.repo.save_state(
                        student_id, self.concept_id, new_mastery
                    ),
                )
                await asyncio.get_running_loop().run_in_executor(
                    None,
                    lambda: self.repo.log_update(
                        student_id,
                        self.concept_id,
                        prev_mastery,
                        new_mastery,
                        correct,
                        response_time_ms,
                    ),
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
            "question_context": self.question_metadata._asdict()
            if self.question_metadata
            else None,
            "difficulty_adjustment": slip_rate - self.params.slip_rate
            if self.question_metadata
            else 0,
            "bloom_adjustment": guess_rate - self.params.guess_rate
            if self.question_metadata
            else 0,
        }

        return {
            "previous_mastery": prev_mastery,
            "new_mastery": new_mastery,
            "confidence": confidence,
            "learning_occurred": learning_occurred,
            "explanation": explanation,
            "question_context": self.question_metadata._asdict()
            if self.question_metadata
            else None,
        }
