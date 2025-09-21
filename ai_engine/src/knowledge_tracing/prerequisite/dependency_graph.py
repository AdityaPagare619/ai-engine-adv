# ai_engine/src/knowledge_tracing/prerequisite/dependency_graph.py
from __future__ import annotations
from typing import Dict, List, Set, Optional, Tuple
import logging
import networkx as nx
from dataclasses import dataclass
from pydantic import BaseModel

logger = logging.getLogger("prerequisite_graph")

@dataclass
class ConceptNode:
    """Represents a concept node in the prerequisite graph"""
    concept_id: str
    name: str
    mastery: float = 0.0
    difficulty: float = 0.5
    
    def __hash__(self):
        return hash(self.concept_id)
    
    def __eq__(self, other):
        if not isinstance(other, ConceptNode):
            return False
        return self.concept_id == other.concept_id

class PrerequisiteGap(BaseModel):
    """Represents a gap in prerequisite knowledge"""
    concept_id: str
    concept_name: str
    current_mastery: float
    required_mastery: float
    gap: float
    impact_score: float
    
class PrerequisiteAnalysisResult(BaseModel):
    """Results of prerequisite analysis"""
    ready_to_learn: bool
    overall_readiness: float
    prerequisite_gaps: List[PrerequisiteGap]
    recommended_concepts: List[str]
    
class PrerequisiteGraph:
    """
    Manages concept dependencies and prerequisite relationships
    using a directed graph structure.
    """
    def __init__(self):
        self.graph = nx.DiGraph()
        self.concept_cache: Dict[str, ConceptNode] = {}
        self.concepts: Dict[str, ConceptNode] = {}  # Added for test compatibility
        self.mastery_threshold = 0.7  # Default mastery threshold
        
    def add_concept(self, concept_id: str, name: str, difficulty: float = 0.5) -> None:
        """Add a concept to the graph"""
        node = ConceptNode(concept_id=concept_id, name=name, difficulty=difficulty)
        self.graph.add_node(concept_id, data=node)
        self.concept_cache[concept_id] = node
        self.concepts[concept_id] = node  # Update concepts dictionary as well
        
    def add_prerequisite(self, concept_id: str, prerequisite_id: str, weight: float = 1.0) -> None:
        """Add a prerequisite relationship between concepts"""
        if concept_id not in self.graph.nodes:
            logger.warning(f"Concept {concept_id} not found in graph")
            return
            
        if prerequisite_id not in self.graph.nodes:
            logger.warning(f"Prerequisite concept {prerequisite_id} not found in graph")
            return
            
        # Add edge from prerequisite to concept (direction shows dependency)
        self.graph.add_edge(prerequisite_id, concept_id, weight=weight)
        
    def update_mastery(self, concept_id: str, mastery: float) -> None:
        """Update mastery level for a concept"""
        if concept_id in self.graph.nodes:
            node_data = self.graph.nodes[concept_id].get('data')
            if node_data:
                node_data.mastery = mastery
                self.concept_cache[concept_id].mastery = mastery
                if concept_id in self.concepts:
                    self.concepts[concept_id].mastery = mastery
                    
    def get_concept_mastery(self, concept_id: str) -> float:
        """Get the mastery level for a concept"""
        if concept_id in self.concept_cache:
            return self.concept_cache[concept_id].mastery
        return 0.0
        
    def get_prerequisites(self, concept_id: str) -> List[ConceptNode]:
        """Get all direct prerequisites for a concept"""
        if concept_id not in self.graph.nodes:
            return []
            
        prerequisites = []
        for pred in self.graph.predecessors(concept_id):
            node_data = self.graph.nodes[pred].get('data')
            if node_data:
                prerequisites.append(node_data)
        return prerequisites
        
    def get_all_prerequisites(self, concept_id: str) -> List[ConceptNode]:
        """Get all prerequisites (direct and indirect) for a concept"""
        if concept_id not in self.graph.nodes:
            return []
            
        # Use networkx to find all ancestors (prerequisites)
        all_prerequisites = nx.ancestors(self.graph, concept_id)
        
        result = []
        for prereq_id in all_prerequisites:
            node_data = self.graph.nodes[prereq_id].get('data')
            if node_data:
                result.append(node_data)
        return result
        
    def analyze_readiness(self, concept_id: str, mastery_threshold: Optional[float] = None) -> PrerequisiteAnalysisResult:
        """
        Analyze if a student is ready to learn a concept based on prerequisite mastery.
        Returns detailed analysis with gaps and recommendations.
        """
        if mastery_threshold is None:
            mastery_threshold = self.mastery_threshold
            
        if concept_id not in self.graph.nodes:
            return PrerequisiteAnalysisResult(
                ready_to_learn=True,
                overall_readiness=1.0,
                prerequisite_gaps=[],
                recommended_concepts=[]
            )
            
        # Get all prerequisites
        prerequisites = self.get_prerequisites(concept_id)
        
        # Analyze gaps
        gaps = []
        total_weight = 0
        weighted_readiness = 0
        
        for prereq in prerequisites:
            # Get edge weight (importance of this prerequisite)
            weight = self.graph.edges[prereq.concept_id, concept_id].get('weight', 1.0)
            total_weight += weight
            
            # Calculate gap
            current_mastery = prereq.mastery
            gap = max(0, mastery_threshold - current_mastery)
            impact_score = gap * weight
            
            weighted_readiness += (current_mastery / mastery_threshold) * weight
            
            if gap > 0:
                gaps.append(PrerequisiteGap(
                    concept_id=prereq.concept_id,
                    concept_name=prereq.name,
                    current_mastery=current_mastery,
                    required_mastery=mastery_threshold,
                    gap=gap,
                    impact_score=impact_score
                ))
        
        # Calculate overall readiness
        overall_readiness = weighted_readiness / max(total_weight, 1.0)
        
        # Sort gaps by impact score (highest first)
        gaps.sort(key=lambda x: x.impact_score, reverse=True)
        
        # Generate recommendations
        recommended_concepts = [gap.concept_id for gap in gaps]
        
        return PrerequisiteAnalysisResult(
            ready_to_learn=overall_readiness >= 0.8,  # 80% readiness threshold
            overall_readiness=overall_readiness,
            prerequisite_gaps=gaps,
            recommended_concepts=recommended_concepts
        )
        
    def get_learning_path(self, target_concept_id: str) -> List[str]:
        """
        Generate an optimal learning path to reach the target concept,
        considering current mastery levels and dependencies.
        """
        if target_concept_id not in self.graph.nodes:
            return []
            
        # Get all prerequisites
        all_prereqs = self.get_all_prerequisites(target_concept_id)
        
        # Create subgraph with target and all prerequisites
        prereq_ids = [p.concept_id for p in all_prereqs]
        prereq_ids.append(target_concept_id)
        # Convert to DiGraph explicitly to match expected type
        subgraph = nx.DiGraph(self.graph.subgraph(prereq_ids))
        
        # Find a topological sort (respects dependencies)
        try:
            # Topological sort gives us an ordering where prerequisites come before concepts that depend on them
            path = list(nx.topological_sort(subgraph))
            # Convert nodes to strings if they aren't already
            path = [str(node) for node in path]
            return path
        except nx.NetworkXUnfeasible:
            # Graph has cycles, use different approach
            logger.warning(f"Prerequisite graph for {target_concept_id} contains cycles, using alternative path finding")
            
            # Use a simple approach - sort by mastery level (learn what you know most about first)
            sorted_concepts = sorted(all_prereqs, key=lambda x: (-x.mastery, x.difficulty))
            path = [p.concept_id for p in sorted_concepts]
            path.append(target_concept_id)
            # Ensure all elements are strings
            path = [str(node) for node in path]
            return path