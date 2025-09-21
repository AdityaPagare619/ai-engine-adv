# ai_engine/src/knowledge_tracing/selection/candidate_provider.py
import logging
from typing import List, Dict, Any
from ai_engine.src.config.exam_config import EXAM_CONFIGS

logger = logging.getLogger("candidate_provider")

class CandidateProvider:
    def __init__(self, datasource=None, exam_code: str = "JEE_Mains"):
        self.datasource = datasource
        self.exam_code = exam_code
        self.config = EXAM_CONFIGS.get(exam_code, EXAM_CONFIGS["JEE_Mains"])
        # Prerequisite gating configuration
        self.min_mastery_gate = 0.6

    def build_candidates(self,
                         student_id: str,
                         concept_id: str,
                         subject: str = None,
                         topic: str = None,
                         limit: int = 50,
                         stress_level: float = 0.0,
                         cognitive_load: float = 0.0) -> List[Dict[str, Any]]:
        items = []
        if self.datasource:
            items = self.datasource.fetch_questions(student_id=student_id, concept_id=concept_id,
                                                    subject=subject, topic=topic, limit=limit)
        else:
            items = [
                {"question_id": "qA", "difficulty": 0.8, "avg_time_ms": 45000, "mastery": 0.6},
                {"question_id": "qB", "difficulty": 0.5, "avg_time_ms": 30000, "mastery": 0.6},
                {"question_id": "qC", "difficulty": 0.3, "avg_time_ms": 25000, "mastery": 0.6},
            ]

        candidates: List[Dict[str, Any]] = []
        scoring = self.config.scoring_scheme
        for itm in items:
            features = {
                "difficulty": itm["difficulty"],
                "estimated_time_ms": itm["avg_time_ms"],
                "mastery_level": itm.get("mastery", 0.0),
                "stress_level": stress_level,
                "cognitive_load": cognitive_load,
                "correct_score": scoring.correct_score,
                "incorrect_score": scoring.incorrect_score,
            }
            # Prerequisite gating heuristic: if student's mastery for this candidate is below threshold,
            # avoid pushing high-difficulty items. Keep easier ones as scaffolding.
            mastery_level = float(features["mastery_level"])
            difficulty = float(features["difficulty"])
            if mastery_level < self.min_mastery_gate and difficulty > 0.6:
                # Skip gating-failed candidate
                continue
            candidates.append({"arm_id": itm["question_id"], "features": features})
        # If gating removed everything (edge case), fall back to original items (safeguard)
        if not candidates and items:
            for itm in items:
                features = {
                    "difficulty": itm["difficulty"],
                    "estimated_time_ms": itm["avg_time_ms"],
                    "mastery_level": itm.get("mastery", 0.0),
                    "stress_level": stress_level,
                    "cognitive_load": cognitive_load,
                    "correct_score": scoring.correct_score,
                    "incorrect_score": scoring.incorrect_score,
                }
                candidates.append({"arm_id": itm["question_id"], "features": features})
        return candidates
