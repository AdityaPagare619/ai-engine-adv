# ai_engine/src/knowledge_tracing/selection/candidate_provider.py
from typing import List, Dict, Any
import logging

logger = logging.getLogger("candidate_provider")

class CandidateProvider:
    """
    Fetches and formats candidate question items for bandit selection.
    Intended to be overridden or extended for specific datasource implementations.
    """

    def __init__(self, datasource=None):
        """
        Args:
            datasource: Data access object for fetching questions.
                        Must implement fetch_questions(concept_id, subject, topic, limit).
        """
        self.datasource = datasource

    def build_candidates(self,
                         student_id: str,
                         concept_id: str,
                         subject: str = None,
                         topic: str = None,
                         limit: int = 50) -> List[Dict[str, Any]]:
        """
        Returns a list of candidate dicts each with:
          - arm_id: the unique question ID
          - features: base feature vector dict to feed into bandit policy
        """
        try:
            items = self.datasource.fetch_questions(
                student_id=student_id,
                concept_id=concept_id,
                subject=subject,
                topic=topic,
                limit=limit
            )
            candidates: List[Dict[str, Any]] = []
            for itm in items:
                features = {
                    "difficulty": itm["difficulty"],           # e.g., 1.2
                    "estimated_time_ms": itm["avg_time_ms"],   # e.g., 45000
                    # placeholders: injected by middleware
                    "stress_level": None,
                    "cognitive_load": None,
                    "mastery_level": itm.get("mastery", 0.0),
                    "topic_vector": itm.get("topic_vector", [])
                }
                candidates.append({
                    "arm_id": itm["question_id"],
                    "features": features
                })
            return candidates
        except Exception as e:
            logger.exception("CandidateProvider.build_candidates failed")
            return []
