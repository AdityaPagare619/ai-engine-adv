# ai_engine/src/knowledge_tracing/prerequisite/manager.py
from typing import Dict, List, Optional, Tuple
import logging
from .dependency_graph import PrerequisiteGraph, PrerequisiteAnalysisResult

logger = logging.getLogger("prerequisite_manager")

class PrerequisiteManager:
    """
    Manages prerequisite knowledge relationships and integrates with the BKT system
    to provide adaptive learning recommendations based on prerequisite dependencies.
    """
    def __init__(self, mastery_threshold: float = 0.7):
        self.graph = PrerequisiteGraph()
        self.graph.mastery_threshold = mastery_threshold
        
    def load_concept_structure(self, concepts_data: List[Dict]) -> None:
        """
        Load concept structure from database or configuration
        
        Args:
            concepts_data: List of concept dictionaries with structure:
                [
                    {
                        "concept_id": "c1",
                        "name": "Concept 1",
                        "difficulty": 0.5,
                        "prerequisites": [
                            {"concept_id": "c2", "weight": 0.8},
                            {"concept_id": "c3", "weight": 0.6}
                        ]
                    },
                    ...
                ]
        """
        # First pass: add all concepts
        for concept in concepts_data:
            self.graph.add_concept(
                concept_id=concept["concept_id"],
                name=concept["name"],
                difficulty=concept.get("difficulty", 0.5)
            )
            
        # Second pass: add prerequisites
        for concept in concepts_data:
            for prereq in concept.get("prerequisites", []):
                self.graph.add_prerequisite(
                    concept_id=concept["concept_id"],
                    prerequisite_id=prereq["concept_id"],
                    weight=prereq.get("weight", 1.0)
                )
                
    def sync_mastery_from_bkt(self, mastery_data: Dict[str, float]) -> None:
        """
        Sync mastery levels from BKT engine
        
        Args:
            mastery_data: Dictionary mapping concept_id to mastery level
        """
        for concept_id, mastery in mastery_data.items():
            self.graph.update_mastery(concept_id, mastery)
            
    def analyze_concept_readiness(self, concept_id: str) -> PrerequisiteAnalysisResult:
        """
        Analyze if a student is ready to learn a concept based on prerequisite mastery
        
        Args:
            concept_id: ID of the concept to analyze
            
        Returns:
            PrerequisiteAnalysisResult with readiness analysis
        """
        return self.graph.analyze_readiness(concept_id)
        
    def get_optimal_learning_path(self, target_concept_id: str) -> List[str]:
        """
        Generate optimal learning path to reach target concept
        
        Args:
            target_concept_id: Target concept to learn
            
        Returns:
            List of concept IDs in recommended learning order
        """
        return self.graph.get_learning_path(target_concept_id)
        
    def recommend_next_concepts(self, current_concept_id: str, count: int = 3) -> List[str]:
        """
        Recommend next concepts to learn after current concept
        
        Args:
            current_concept_id: Current concept being learned
            count: Number of recommendations to return
            
        Returns:
            List of recommended concept IDs
        """
        # Get successors (concepts that depend on current concept)
        successors = []
        if current_concept_id in self.graph.graph:
            for succ in self.graph.graph.successors(current_concept_id):
                # Check if all prerequisites are sufficiently mastered
                analysis = self.graph.analyze_readiness(succ)
                successors.append((succ, analysis.overall_readiness))
                
        # Sort by readiness (highest first)
        successors.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N concept IDs
        return [s[0] for s in successors[:count]]
        
    def get_prerequisite_gaps(self, concept_id: str) -> List[Dict]:
        """
        Get prerequisite knowledge gaps for a concept
        
        Args:
            concept_id: Concept to analyze
            
        Returns:
            List of prerequisite gaps with impact scores
        """
        analysis = self.graph.analyze_readiness(concept_id)
        return [gap.dict() for gap in analysis.prerequisite_gaps]