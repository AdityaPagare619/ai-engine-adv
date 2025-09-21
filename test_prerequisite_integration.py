#!/usr/bin/env python3
"""
Test file for validating prerequisite knowledge management integration
with the enhanced BKT system
"""

import os
import sys
import unittest
import logging
from typing import Dict, List, Any

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the enhanced BKT system
from enhanced_bkt_system import PedagogicalBKT, ImprovedSimulation

# Import prerequisite knowledge management
from ai_engine.src.knowledge_tracing.prerequisite.manager import PrerequisiteManager
from ai_engine.src.knowledge_tracing.prerequisite.dependency_graph import PrerequisiteGraph

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_prerequisite")

class TestPrerequisiteIntegration(unittest.TestCase):
    """Test cases for prerequisite knowledge management integration"""
    
    def setUp(self):
        """Set up test environment"""
        # Create enhanced BKT system
        self.bkt_system = PedagogicalBKT(mastery_threshold=0.75)
        
        # Load test concept structure
        self.load_test_concepts()
        
    def load_test_concepts(self):
        """Load test concept structure"""
        self.concepts_data = [
            {
                "concept_id": "algebra_basics",
                "name": "Algebra Basics",
                "difficulty": 0.4,
                "prerequisites": []
            },
            {
                "concept_id": "linear_equations",
                "name": "Linear Equations",
                "difficulty": 0.5,
                "prerequisites": [
                    {"concept_id": "algebra_basics", "weight": 0.9}
                ]
            },
            {
                "concept_id": "quadratic_equations",
                "name": "Quadratic Equations",
                "difficulty": 0.7,
                "prerequisites": [
                    {"concept_id": "linear_equations", "weight": 0.8},
                    {"concept_id": "algebra_basics", "weight": 0.6}
                ]
            },
            {
                "concept_id": "polynomials",
                "name": "Polynomials",
                "difficulty": 0.6,
                "prerequisites": [
                    {"concept_id": "algebra_basics", "weight": 0.7}
                ]
            },
            {
                "concept_id": "advanced_functions",
                "name": "Advanced Functions",
                "difficulty": 0.8,
                "prerequisites": [
                    {"concept_id": "quadratic_equations", "weight": 0.8},
                    {"concept_id": "polynomials", "weight": 0.7}
                ]
            }
        ]
        
        # Load concepts into BKT system
        self.bkt_system.load_concept_structure(self.concepts_data)
        
    def test_concept_structure_loading(self):
        """Test that concept structure is loaded correctly"""
        # Verify that concepts are loaded into prerequisite manager
        self.assertIsNotNone(self.bkt_system.prerequisite_manager)
        self.assertIsNotNone(self.bkt_system.prerequisite_manager.graph)
        
        # Check that all concepts are in the graph
        for concept in self.concepts_data:
            concept_id = concept["concept_id"]
            self.assertIn(concept_id, self.bkt_system.prerequisite_manager.graph.concepts)
            
        # Check that prerequisites are set up correctly
        for concept in self.concepts_data:
            concept_id = concept["concept_id"]
            for prereq in concept.get("prerequisites", []):
                prereq_id = prereq["concept_id"]
                # Verify that prerequisite relationship exists in graph
                self.assertIn(
                    prereq_id, 
                    [p.concept_id for p in self.bkt_system.prerequisite_manager.graph.get_prerequisites(concept_id)]
                )
                
    def test_mastery_synchronization(self):
        """Test that mastery is synchronized between BKT and prerequisite system"""
        student_id = "test_student"
        
        # Update mastery for algebra_basics
        result = self.bkt_system.update_mastery(
            student_id=student_id,
            topic="algebra_basics",
            is_correct=True,
            difficulty=0.4
        )
        
        # Check that mastery is updated in BKT
        self.assertGreater(result["new_mastery"], 0.05)  # Should be higher than prior
        
        # Check that mastery is synchronized to prerequisite system
        self.assertIn("algebra_basics", self.bkt_system.concept_masteries)
        self.assertEqual(
            self.bkt_system.concept_masteries["algebra_basics"],
            result["new_mastery"]
        )
        
        # Check that prerequisite manager has the mastery
        concept_mastery = self.bkt_system.prerequisite_manager.graph.get_concept_mastery("algebra_basics")
        self.assertEqual(concept_mastery, result["new_mastery"])
        
    def test_prerequisite_readiness_analysis(self):
        """Test prerequisite readiness analysis"""
        student_id = "test_student"
        
        # Initially, quadratic_equations should not be ready to learn
        # because prerequisites (linear_equations) are not mastered
        readiness = self.bkt_system.prerequisite_manager.analyze_concept_readiness("quadratic_equations")
        self.assertFalse(readiness.ready_to_learn)
        
        # Master algebra_basics
        for _ in range(5):
            self.bkt_system.update_mastery(
                student_id=student_id,
                topic="algebra_basics",
                is_correct=True,
                difficulty=0.4
            )
            
        # Master linear_equations
        for _ in range(5):
            self.bkt_system.update_mastery(
                student_id=student_id,
                topic="linear_equations",
                is_correct=True,
                difficulty=0.5
            )
            
        # Now quadratic_equations should be ready to learn
        readiness = self.bkt_system.prerequisite_manager.analyze_concept_readiness("quadratic_equations")
        self.assertTrue(readiness.ready_to_learn)
        
    def test_learning_path_generation(self):
        """Test learning path generation"""
        # Get learning path for advanced_functions
        learning_path = self.bkt_system.get_learning_path("advanced_functions")
        
        # Check that learning path is valid
        self.assertIsInstance(learning_path, list)
        self.assertGreater(len(learning_path), 0)
        
        # Check that learning path includes prerequisites in correct order
        # algebra_basics should come before linear_equations
        # linear_equations should come before quadratic_equations
        if "algebra_basics" in learning_path and "linear_equations" in learning_path:
            algebra_index = learning_path.index("algebra_basics")
            linear_index = learning_path.index("linear_equations")
            self.assertLess(algebra_index, linear_index)
            
        if "linear_equations" in learning_path and "quadratic_equations" in learning_path:
            linear_index = learning_path.index("linear_equations")
            quadratic_index = learning_path.index("quadratic_equations")
            self.assertLess(linear_index, quadratic_index)
            
        # Advanced functions should be last
        self.assertEqual(learning_path[-1], "advanced_functions")
        
    def test_prerequisite_gaps(self):
        """Test prerequisite gaps detection"""
        student_id = "test_student"
        
        # Initially, there should be prerequisite gaps for quadratic_equations
        gaps = self.bkt_system.prerequisite_manager.get_prerequisite_gaps("quadratic_equations")
        self.assertGreater(len(gaps), 0)
        
        # Master all prerequisites
        for _ in range(5):
            self.bkt_system.update_mastery(
                student_id=student_id,
                topic="algebra_basics",
                is_correct=True,
                difficulty=0.4
            )
            
        for _ in range(5):
            self.bkt_system.update_mastery(
                student_id=student_id,
                topic="linear_equations",
                is_correct=True,
                difficulty=0.5
            )
            
        # Now there should be no prerequisite gaps
        gaps = self.bkt_system.prerequisite_manager.get_prerequisite_gaps("quadratic_equations")
        self.assertEqual(len(gaps), 0)
        
    def test_next_concept_recommendation(self):
        """Test next concept recommendation"""
        # After mastering algebra_basics, linear_equations should be recommended
        recommendations = self.bkt_system.recommend_next_concepts("algebra_basics")
        self.assertIn("linear_equations", recommendations)
        
        # After mastering linear_equations, quadratic_equations should be recommended
        recommendations = self.bkt_system.recommend_next_concepts("linear_equations")
        self.assertIn("quadratic_equations", recommendations)
        
    def test_motivational_feedback_with_prerequisites(self):
        """Test motivational feedback with prerequisite suggestions"""
        student_id = "test_student"
        
        # Try quadratic_equations without prerequisites
        result = self.bkt_system.update_mastery(
            student_id=student_id,
            topic="quadratic_equations",
            is_correct=False,
            difficulty=0.7
        )
        
        # Check that motivational feedback includes prerequisite suggestion
        feedback = result["motivational_feedback"]
        self.assertIsNotNone(feedback.prerequisite_suggestion)
        
        # Master prerequisites
        for _ in range(5):
            self.bkt_system.update_mastery(
                student_id=student_id,
                topic="algebra_basics",
                is_correct=True,
                difficulty=0.4
            )
            
        for _ in range(5):
            self.bkt_system.update_mastery(
                student_id=student_id,
                topic="linear_equations",
                is_correct=True,
                difficulty=0.5
            )
            
        # Now try quadratic_equations again
        result = self.bkt_system.update_mastery(
            student_id=student_id,
            topic="quadratic_equations",
            is_correct=False,
            difficulty=0.7
        )
        
        # Check that motivational feedback doesn't include prerequisite suggestion
        # since prerequisites are mastered
        feedback = result["motivational_feedback"]
        if feedback.prerequisite_suggestion:
            # If there is a suggestion, it should be for a different concept
            self.assertNotIn(feedback.prerequisite_suggestion["concept_id"], ["algebra_basics", "linear_equations"])
            
    def test_difficulty_selection_with_prerequisites(self):
        """Test difficulty selection with prerequisite readiness"""
        student_id = "test_student"
        
        # Without mastering prerequisites, difficulty for quadratic_equations should be lower
        difficulty_level = self.bkt_system.select_optimal_difficulty(
            student_id=student_id,
            topic="quadratic_equations",
            mastery=0.5
        )
        self.assertIn(difficulty_level.value, ["foundation", "building"])
        
        # Master prerequisites
        for _ in range(5):
            self.bkt_system.update_mastery(
                student_id=student_id,
                topic="algebra_basics",
                is_correct=True,
                difficulty=0.4
            )
            
        for _ in range(5):
            self.bkt_system.update_mastery(
                student_id=student_id,
                topic="linear_equations",
                is_correct=True,
                difficulty=0.5
            )
            
        # Now difficulty for quadratic_equations should be higher
        difficulty_level = self.bkt_system.select_optimal_difficulty(
            student_id=student_id,
            topic="quadratic_equations",
            mastery=0.5
        )
        self.assertIn(difficulty_level.value, ["building", "intermediate"])

class TestImprovedSimulation(unittest.TestCase):
    """Test cases for improved simulation with prerequisite integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.simulation = ImprovedSimulation()
        
    def test_simulation_runs_successfully(self):
        """Test that simulation runs without errors"""
        results = self.simulation.simulate_improved_learning(days=3)
        
        # Check that results are valid
        self.assertIsInstance(results, dict)
        self.assertIn("success_rate", results)
        self.assertIn("total_questions", results)
        self.assertIn("total_correct", results)
        self.assertIn("improvement", results)
        
        # Check that success rate is reasonable
        self.assertGreater(results["success_rate"], 20)  # Should be better than baseline
        
    def test_simulation_learning_path(self):
        """Test that simulation generates valid learning path"""
        # Get learning path for advanced_functions
        learning_path = self.simulation.enhanced_bkt.get_learning_path("advanced_functions")
        
        # Check that learning path is valid
        self.assertIsInstance(learning_path, list)
        self.assertGreater(len(learning_path), 0)
        
        # Advanced functions should be last
        self.assertEqual(learning_path[-1], "advanced_functions")

if __name__ == "__main__":
    unittest.main()