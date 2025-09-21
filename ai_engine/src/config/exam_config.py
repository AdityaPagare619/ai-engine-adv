# ai_engine/src/config/exam_config.py
from typing import Dict, List, Optional
from pydantic import BaseModel

class ScoringScheme(BaseModel):
    correct_score: float
    incorrect_score: float
    partial_credit_rules: Optional[Dict[str, float]] = None

class ExamConfiguration(BaseModel):
    exam_code: str
    question_types: List[str]
    scoring_scheme: ScoringScheme
    time_constraints_sec: int
    subject_weightings: Dict[str, float]
    difficulty_ranges: Dict[str, List[float]]

EXAM_CONFIGS = {
    "JEE_Mains": ExamConfiguration(
        exam_code="JEE_Mains",
        question_types=["mcq", "integer"],
        scoring_scheme=ScoringScheme(correct_score=4, incorrect_score=-1),
        time_constraints_sec=180,
        subject_weightings={"physics": 0.35, "chemistry": 0.35, "math": 0.30},
        difficulty_ranges={"physics": [0, 1], "chemistry": [0, 1], "math": [0, 1]}
    ),
    "NEET": ExamConfiguration(
        exam_code="NEET",
        question_types=["mcq"],
        scoring_scheme=ScoringScheme(correct_score=4, incorrect_score=-1),
        time_constraints_sec=90,
        subject_weightings={"physics": 0.25, "chemistry": 0.25, "biology": 0.50},
        difficulty_ranges={"physics": [0, 1], "chemistry": [0, 1], "biology": [0, 1]}
    ),
    "JEE_Advanced": ExamConfiguration(
        exam_code="JEE_Advanced",
        question_types=["mcq", "integer", "matrix"],
        scoring_scheme=ScoringScheme(correct_score=4, incorrect_score=-2),
        time_constraints_sec=240,
        subject_weightings={"physics": 0.33, "chemistry": 0.33, "math": 0.34},
        difficulty_ranges={"physics": [0, 1], "chemistry": [0, 1], "math": [0, 1]}
    )
}
