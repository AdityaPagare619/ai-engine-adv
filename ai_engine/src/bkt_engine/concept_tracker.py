# Concept Tracker - Relationship and Dependency Management
# Tracks concept relationships and prerequisites for JEE subjects

from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import logging

class SubjectArea(Enum):
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    MATHEMATICS = "mathematics"

class DependencyStrength(Enum):
    WEAK = 0.3
    MODERATE = 0.6
    STRONG = 0.8
    CRITICAL = 0.95

@dataclass
class ConceptNode:
    """Represents a concept with its relationships"""
    concept_id: str
    subject: SubjectArea
    difficulty_level: int  # 1-5 scale
    prerequisites: Dict[str, float]  # concept_id -> strength
    enables: Dict[str, float]  # concepts this enables -> strength
    related_concepts: Dict[str, float]  # loosely related concepts
    
class ConceptTracker:
    """
    Advanced concept relationship tracking and management
    Maintains prerequisite chains and concept dependencies
    """
    
    def __init__(self):
        self.concepts: Dict[str, ConceptNode] = {}
        self.subject_trees: Dict[SubjectArea, Dict[str, Set[str]]] = {
            SubjectArea.PHYSICS: {'roots': set(), 'leaves': set()},
            SubjectArea.CHEMISTRY: {'roots': set(), 'leaves': set()},
            SubjectArea.MATHEMATICS: {'roots': set(), 'leaves': set()}
        }
        
        self.logger = logging.getLogger(__name__)
        self._initialize_jee_concept_graph()
    
    def _initialize_jee_concept_graph(self):
        """Initialize comprehensive JEE concept relationship graph"""
        
        # Physics Concepts
        physics_concepts = {
            # Mechanics
            'kinematics': ConceptNode(
                concept_id='kinematics',
                subject=SubjectArea.PHYSICS,
                difficulty_level=2,
                prerequisites={'basic_math': 0.8, 'vectors': 0.7},
                enables={'dynamics': 0.9, 'circular_motion': 0.8, 'projectile_motion': 0.9},
                related_concepts={'coordinate_geometry': 0.6}
            ),
            'dynamics': ConceptNode(
                concept_id='dynamics',
                subject=SubjectArea.PHYSICS,
                difficulty_level=3,
                prerequisites={'kinematics': 0.9, 'vectors': 0.8},
                enables={'work_energy': 0.8, 'momentum': 0.7, 'rotational_motion': 0.8},
                related_concepts={'calculus': 0.5}
            ),
            'work_energy': ConceptNode(
                concept_id='work_energy',
                subject=SubjectArea.PHYSICS,
                difficulty_level=3,
                prerequisites={'dynamics': 0.8, 'kinematics': 0.7},
                enables={'simple_harmonic_motion': 0.6, 'thermodynamics': 0.5},
                related_concepts={'integration': 0.7}
            ),
            'rotational_motion': ConceptNode(
                concept_id='rotational_motion',
                subject=SubjectArea.PHYSICS,
                difficulty_level=4,
                prerequisites={'dynamics': 0.9, 'circular_motion': 0.8},
                enables={'gyroscopes': 0.7, 'rolling_motion': 0.8},
                related_concepts={'moment_of_inertia': 0.9}
            ),
            
            # Thermodynamics
            'thermodynamics': ConceptNode(
                concept_id='thermodynamics',
                subject=SubjectArea.PHYSICS,
                difficulty_level=4,
                prerequisites={'work_energy': 0.7, 'kinetic_theory': 0.8},
                enables={'heat_engines': 0.8, 'refrigeration': 0.7},
                related_concepts={'probability': 0.4, 'statistics': 0.4}
            ),
            'kinetic_theory': ConceptNode(
                concept_id='kinetic_theory',
                subject=SubjectArea.PHYSICS,
                difficulty_level=3,
                prerequisites={'basic_statistics': 0.6},
                enables={'thermodynamics': 0.8, 'gas_laws': 0.9},
                related_concepts={'atomic_structure': 0.5}
            ),
            
            # Electromagnetism
            'electrostatics': ConceptNode(
                concept_id='electrostatics',
                subject=SubjectArea.PHYSICS,
                difficulty_level=3,
                prerequisites={'vectors': 0.8, 'calculus': 0.6},
                enables={'capacitors': 0.9, 'electric_field': 0.9},
                related_concepts={'coulomb_law': 0.9}
            ),
            'current_electricity': ConceptNode(
                concept_id='current_electricity',
                subject=SubjectArea.PHYSICS,
                difficulty_level=3,
                prerequisites={'electrostatics': 0.7},
                enables={'magnetism': 0.7, 'electromagnetic_induction': 0.8},
                related_concepts={'ohms_law': 0.9, 'circuits': 0.9}
            ),
            'electromagnetic_induction': ConceptNode(
                concept_id='electromagnetic_induction',
                subject=SubjectArea.PHYSICS,
                difficulty_level=4,
                prerequisites={'current_electricity': 0.8, 'magnetism': 0.8},
                enables={'ac_circuits': 0.8, 'electromagnetic_waves': 0.7},
                related_concepts={'faraday_law': 0.9, 'lenz_law': 0.8}
            ),
            
            # Optics
            'geometric_optics': ConceptNode(
                concept_id='geometric_optics',
                subject=SubjectArea.PHYSICS,
                difficulty_level=2,
                prerequisites={'basic_geometry': 0.7},
                enables={'wave_optics': 0.6, 'lens_systems': 0.9},
                related_concepts={'trigonometry': 0.8}
            ),
            'wave_optics': ConceptNode(
                concept_id='wave_optics',
                subject=SubjectArea.PHYSICS,
                difficulty_level=4,
                prerequisites={'geometric_optics': 0.6, 'waves': 0.8},
                enables={'interference': 0.9, 'diffraction': 0.9},
                related_concepts={'complex_numbers': 0.5}
            ),
            
            # Modern Physics
            'atomic_physics': ConceptNode(
                concept_id='atomic_physics',
                subject=SubjectArea.PHYSICS,
                difficulty_level=4,
                prerequisites={'electromagnetic_radiation': 0.7, 'quantum_concepts': 0.8},
                enables={'nuclear_physics': 0.8, 'solid_state': 0.6},
                related_concepts={'atomic_structure': 0.9}
            ),
            'nuclear_physics': ConceptNode(
                concept_id='nuclear_physics',
                subject=SubjectArea.PHYSICS,
                difficulty_level=5,
                prerequisites={'atomic_physics': 0.9, 'conservation_laws': 0.8},
                enables={'radioactivity': 0.9, 'nuclear_reactions': 0.9},
                related_concepts={'binding_energy': 0.9}
            )
        }
        
        # Chemistry Concepts
        chemistry_concepts = {
            # Atomic Structure
            'atomic_structure': ConceptNode(
                concept_id='atomic_structure',
                subject=SubjectArea.CHEMISTRY,
                difficulty_level=2,
                prerequisites={'basic_math': 0.6},
                enables={'periodic_table': 0.9, 'chemical_bonding': 0.8, 'quantum_numbers': 0.8},
                related_concepts={'atomic_physics': 0.7}
            ),
            'periodic_table': ConceptNode(
                concept_id='periodic_table',
                subject=SubjectArea.CHEMISTRY,
                difficulty_level=3,
                prerequisites={'atomic_structure': 0.9},
                enables={'chemical_bonding': 0.8, 'periodic_trends': 0.9},
                related_concepts={'electron_configuration': 0.9}
            ),
            'chemical_bonding': ConceptNode(
                concept_id='chemical_bonding',
                subject=SubjectArea.CHEMISTRY,
                difficulty_level=3,
                prerequisites={'atomic_structure': 0.8, 'periodic_table': 0.7},
                enables={'molecular_structure': 0.9, 'solid_state_chemistry': 0.7},
                related_concepts={'lewis_structures': 0.9, 'vsepr_theory': 0.8}
            ),
            
            # Physical Chemistry
            'thermochemistry': ConceptNode(
                concept_id='thermochemistry',
                subject=SubjectArea.CHEMISTRY,
                difficulty_level=4,
                prerequisites={'thermodynamics': 0.6, 'chemical_bonding': 0.5},
                enables={'chemical_equilibrium': 0.7, 'kinetics': 0.6},
                related_concepts={'enthalpy': 0.9, 'entropy': 0.8}
            ),
            'chemical_equilibrium': ConceptNode(
                concept_id='chemical_equilibrium',
                subject=SubjectArea.CHEMISTRY,
                difficulty_level=4,
                prerequisites={'thermochemistry': 0.7, 'kinetics': 0.6},
                enables={'acid_base_equilibrium': 0.8, 'solubility': 0.7},
                related_concepts={'le_chatelier': 0.9}
            ),
            'chemical_kinetics': ConceptNode(
                concept_id='chemical_kinetics',
                subject=SubjectArea.CHEMISTRY,
                difficulty_level=4,
                prerequisites={'calculus': 0.6, 'thermochemistry': 0.5},
                enables={'catalysis': 0.8, 'reaction_mechanisms': 0.9},
                related_concepts={'rate_laws': 0.9, 'activation_energy': 0.8}
            ),
            'electrochemistry': ConceptNode(
                concept_id='electrochemistry',
                subject=SubjectArea.CHEMISTRY,
                difficulty_level=4,
                prerequisites={'chemical_equilibrium': 0.7, 'current_electricity': 0.6},
                enables={'batteries': 0.8, 'electrolysis': 0.9},
                related_concepts={'redox_reactions': 0.9, 'nernst_equation': 0.8}
            ),
            
            # Organic Chemistry
            'organic_structure': ConceptNode(
                concept_id='organic_structure',
                subject=SubjectArea.CHEMISTRY,
                difficulty_level=3,
                prerequisites={'chemical_bonding': 0.8, 'hybridization': 0.7},
                enables={'organic_reactions': 0.9, 'stereochemistry': 0.8},
                related_concepts={'isomerism': 0.9}
            ),
            'organic_reactions': ConceptNode(
                concept_id='organic_reactions',
                subject=SubjectArea.CHEMISTRY,
                difficulty_level=4,
                prerequisites={'organic_structure': 0.9, 'reaction_mechanisms': 0.7},
                enables={'synthesis': 0.8, 'biomolecules': 0.6},
                related_concepts={'functional_groups': 0.9}
            ),
            'stereochemistry': ConceptNode(
                concept_id='stereochemistry',
                subject=SubjectArea.CHEMISTRY,
                difficulty_level=4,
                prerequisites={'organic_structure': 0.8, 'spatial_reasoning': 0.7},
                enables={'chiral_synthesis': 0.8, 'drug_design': 0.6},
                related_concepts={'optical_activity': 0.9}
            ),
            
            # Inorganic Chemistry
            'coordination_chemistry': ConceptNode(
                concept_id='coordination_chemistry',
                subject=SubjectArea.CHEMISTRY,
                difficulty_level=4,
                prerequisites={'chemical_bonding': 0.8, 'periodic_table': 0.7},
                enables={'transition_metal_chemistry': 0.9, 'bioinorganic': 0.6},
                related_concepts={'crystal_field_theory': 0.8}
            ),
            'solid_state_chemistry': ConceptNode(
                concept_id='solid_state_chemistry',
                subject=SubjectArea.CHEMISTRY,
                difficulty_level=4,
                prerequisites={'chemical_bonding': 0.8, 'crystal_structures': 0.7},
                enables={'materials_science': 0.7, 'semiconductors': 0.6},
                related_concepts={'unit_cells': 0.9, 'packing_efficiency': 0.8}
            )
        }
        
        # Mathematics Concepts
        mathematics_concepts = {
            # Algebra
            'basic_algebra': ConceptNode(
                concept_id='basic_algebra',
                subject=SubjectArea.MATHEMATICS,
                difficulty_level=1,
                prerequisites={},
                enables={'quadratic_equations': 0.9, 'polynomials': 0.8},
                related_concepts={'linear_equations': 0.9}
            ),
            'quadratic_equations': ConceptNode(
                concept_id='quadratic_equations',
                subject=SubjectArea.MATHEMATICS,
                difficulty_level=2,
                prerequisites={'basic_algebra': 0.9},
                enables={'complex_numbers': 0.7, 'conic_sections': 0.6},
                related_concepts={'discriminant': 0.9, 'roots': 0.9}
            ),
            'complex_numbers': ConceptNode(
                concept_id='complex_numbers',
                subject=SubjectArea.MATHEMATICS,
                difficulty_level=3,
                prerequisites={'quadratic_equations': 0.7, 'trigonometry': 0.6},
                enables={'polar_form': 0.8, 'de_moivre_theorem': 0.8},
                related_concepts={'argand_diagram': 0.9}
            ),
            
            # Calculus
            'limits': ConceptNode(
                concept_id='limits',
                subject=SubjectArea.MATHEMATICS,
                difficulty_level=3,
                prerequisites={'functions': 0.8, 'coordinate_geometry': 0.6},
                enables={'derivatives': 0.9, 'continuity': 0.9},
                related_concepts={'epsilon_delta': 0.7}
            ),
            'derivatives': ConceptNode(
                concept_id='derivatives',
                subject=SubjectArea.MATHEMATICS,
                difficulty_level=3,
                prerequisites={'limits': 0.9, 'functions': 0.8},
                enables={'applications_of_derivatives': 0.9, 'integrals': 0.7},
                related_concepts={'chain_rule': 0.9, 'product_rule': 0.8}
            ),
            'integrals': ConceptNode(
                concept_id='integrals',
                subject=SubjectArea.MATHEMATICS,
                difficulty_level=4,
                prerequisites={'derivatives': 0.8, 'functions': 0.8},
                enables={'applications_of_integrals': 0.9, 'differential_equations': 0.7},
                related_concepts={'fundamental_theorem': 0.9}
            ),
            'differential_equations': ConceptNode(
                concept_id='differential_equations',
                subject=SubjectArea.MATHEMATICS,
                difficulty_level=5,
                prerequisites={'integrals': 0.8, 'derivatives': 0.8},
                enables={'advanced_applications': 0.8},
                related_concepts={'separation_variables': 0.9}
            ),
            
            # Coordinate Geometry
            'coordinate_geometry': ConceptNode(
                concept_id='coordinate_geometry',
                subject=SubjectArea.MATHEMATICS,
                difficulty_level=2,
                prerequisites={'basic_algebra': 0.7, 'basic_geometry': 0.7},
                enables={'conic_sections': 0.8, 'three_d_geometry': 0.7},
                related_concepts={'distance_formula': 0.9, 'slope': 0.9}
            ),
            'conic_sections': ConceptNode(
                concept_id='conic_sections',
                subject=SubjectArea.MATHEMATICS,
                difficulty_level=3,
                prerequisites={'coordinate_geometry': 0.8, 'quadratic_equations': 0.6},
                enables={'three_d_geometry': 0.6},
                related_concepts={'eccentricity': 0.9, 'focus_directrix': 0.8}
            ),
            'three_d_geometry': ConceptNode(
                concept_id='three_d_geometry',
                subject=SubjectArea.MATHEMATICS,
                difficulty_level=4,
                prerequisites={'coordinate_geometry': 0.8, 'vectors': 0.8},
                enables={'vector_applications': 0.8},
                related_concepts={'direction_cosines': 0.9}
            ),
            
            # Trigonometry
            'trigonometry': ConceptNode(
                concept_id='trigonometry',
                subject=SubjectArea.MATHEMATICS,
                difficulty_level=2,
                prerequisites={'basic_geometry': 0.7},
                enables={'inverse_trigonometry': 0.8, 'trigonometric_equations': 0.9},
                related_concepts={'unit_circle': 0.9, 'identities': 0.9}
            ),
            'inverse_trigonometry': ConceptNode(
                concept_id='inverse_trigonometry',
                subject=SubjectArea.MATHEMATICS,
                difficulty_level=3,
                prerequisites={'trigonometry': 0.9, 'functions': 0.7},
                enables={'trigonometric_equations': 0.7},
                related_concepts={'domain_range': 0.8}
            ),
            
            # Vectors
            'vectors': ConceptNode(
                concept_id='vectors',
                subject=SubjectArea.MATHEMATICS,
                difficulty_level=3,
                prerequisites={'coordinate_geometry': 0.7, 'trigonometry': 0.6},
                enables={'three_d_geometry': 0.8, 'vector_calculus': 0.8},
                related_concepts={'dot_product': 0.9, 'cross_product': 0.9}
            ),
            
            # Probability & Statistics
            'probability': ConceptNode(
                concept_id='probability',
                subject=SubjectArea.MATHEMATICS,
                difficulty_level=3,
                prerequisites={'combinatorics': 0.7, 'basic_algebra': 0.6},
                enables={'statistics': 0.8, 'probability_distributions': 0.8},
                related_concepts={'bayes_theorem': 0.8, 'conditional_probability': 0.9}
            ),
            'statistics': ConceptNode(
                concept_id='statistics',
                subject=SubjectArea.MATHEMATICS,
                difficulty_level=3,
                prerequisites={'probability': 0.7},
                enables={'hypothesis_testing': 0.8, 'regression': 0.7},
                related_concepts={'mean_variance': 0.9, 'distributions': 0.8}
            )
        }
        
        # Merge all concepts
        all_concepts = {**physics_concepts, **chemistry_concepts, **mathematics_concepts}
        
        # Add concepts to tracker
        for concept_id, concept_node in all_concepts.items():
            self.add_concept(concept_node)
        
        self._build_subject_trees()
    
    def add_concept(self, concept: ConceptNode):
        """Add a new concept to the tracker"""
        self.concepts[concept.concept_id] = concept
        self.logger.debug(f"Added concept: {concept.concept_id} ({concept.subject.value})")
    
    def _build_subject_trees(self):
        """Build subject-specific tree structures"""
        for subject in SubjectArea:
            subject_concepts = [c for c in self.concepts.values() if c.subject == subject]
            
            for concept in subject_concepts:
                # Find roots (concepts with no prerequisites in the same subject)
                subject_prereqs = [p for p in concept.prerequisites.keys() 
                                 if p in self.concepts and self.concepts[p].subject == subject]
                
                if not subject_prereqs:
                    self.subject_trees[subject]['roots'].add(concept.concept_id)
                
                # Find leaves (concepts that don't enable others in the same subject)
                subject_enables = [e for e in concept.enables.keys() 
                                 if e in self.concepts and self.concepts[e].subject == subject]
                
                if not subject_enables:
                    self.subject_trees[subject]['leaves'].add(concept.concept_id)
    
    def get_prerequisites_chain(self, concept_id: str, visited: Optional[Set[str]] = None) -> List[str]:
        """Get the complete prerequisite chain for a concept"""
        if visited is None:
            visited = set()
        
        if concept_id not in self.concepts or concept_id in visited:
            return []
        
        visited.add(concept_id)
        concept = self.concepts[concept_id]
        chain = []
        
        # Add direct prerequisites
        for prereq_id, strength in concept.prerequisites.items():
            if strength > 0.5:  # Only consider strong prerequisites
                if prereq_id not in visited:
                    prereq_chain = self.get_prerequisites_chain(prereq_id, visited.copy())
                    chain.extend(prereq_chain)
                    if prereq_id not in chain:
                        chain.append(prereq_id)
        
        return chain
    
    def get_learning_path(self, target_concept: str, current_masteries: Dict[str, float] = None) -> List[str]:
        """Generate optimal learning path to reach target concept"""
        if target_concept not in self.concepts:
            return []
        
        if current_masteries is None:
            current_masteries = {}
        
        # Get all prerequisites
        prereq_chain = self.get_prerequisites_chain(target_concept)
        
        # Filter out already mastered concepts (mastery > 0.8)
        unmastered = [concept for concept in prereq_chain 
                     if current_masteries.get(concept, 0) < 0.8]
        
        # Sort by difficulty level and prerequisite dependencies
        def sort_key(concept_id):
            concept = self.concepts[concept_id]
            # Priority: lower difficulty first, then fewer unresolved dependencies
            unresolved_deps = sum(1 for dep in concept.prerequisites.keys() 
                                if current_masteries.get(dep, 0) < 0.8)
            return (concept.difficulty_level, unresolved_deps)
        
        learning_path = sorted(unmastered, key=sort_key)
        
        # Add the target concept at the end
        if target_concept not in learning_path:
            learning_path.append(target_concept)
        
        return learning_path
    
    def get_concept_recommendations(self, current_masteries: Dict[str, float], 
                                  subject_focus: Optional[SubjectArea] = None) -> Dict[str, List[str]]:
        """Get concept recommendations based on current mastery levels"""
        recommendations = {
            'ready_to_learn': [],  # Prerequisites met, ready to learn
            'continue_practicing': [],  # Partially mastered, need more practice
            'review_needed': [],  # Prerequisites weak, need review
            'advanced_ready': []  # Can tackle advanced concepts
        }
        
        concepts_to_analyze = self.concepts.values()
        if subject_focus:
            concepts_to_analyze = [c for c in concepts_to_analyze if c.subject == subject_focus]
        
        for concept in concepts_to_analyze:
            concept_id = concept.concept_id
            current_mastery = current_masteries.get(concept_id, 0)
            
            # Check prerequisite readiness
            prereq_met = True
            prereq_strength = 1.0
            
            for prereq_id, required_strength in concept.prerequisites.items():
                prereq_mastery = current_masteries.get(prereq_id, 0)
                if prereq_mastery < required_strength:
                    prereq_met = False
                    prereq_strength = min(prereq_strength, prereq_mastery / required_strength)
            
            # Categorize recommendations
            if current_mastery < 0.3:
                if prereq_met and prereq_strength > 0.8:
                    recommendations['ready_to_learn'].append(concept_id)
                elif prereq_strength < 0.6:
                    recommendations['review_needed'].append(concept_id)
            elif current_mastery < 0.8:
                recommendations['continue_practicing'].append(concept_id)
            else:
                # Check if can tackle advanced concepts
                enabled_concepts = list(concept.enables.keys())
                unmastered_advanced = [c for c in enabled_concepts 
                                     if current_masteries.get(c, 0) < 0.5]
                if unmastered_advanced:
                    recommendations['advanced_ready'].extend(unmastered_advanced[:2])  # Top 2
        
        # Remove duplicates and limit recommendations
        for category in recommendations:
            recommendations[category] = list(set(recommendations[category]))[:5]
        
        return recommendations
    
    def calculate_transfer_learning_boost(self, target_concept: str, 
                                        current_masteries: Dict[str, float]) -> float:
        """Calculate potential transfer learning boost for a concept"""
        if target_concept not in self.concepts:
            return 0.0
        
        concept = self.concepts[target_concept]
        total_boost = 0.0
        
        # From prerequisites
        for prereq_id, strength in concept.prerequisites.items():
            prereq_mastery = current_masteries.get(prereq_id, 0)
            if prereq_mastery > 0.7:
                boost = strength * (prereq_mastery - 0.7) * 0.2
                total_boost += boost
        
        # From related concepts
        for related_id, strength in concept.related_concepts.items():
            related_mastery = current_masteries.get(related_id, 0)
            if related_mastery > 0.7:
                boost = strength * (related_mastery - 0.7) * 0.1
                total_boost += boost
        
        return min(0.3, total_boost)  # Cap at 30% boost
    
    def get_concept_difficulty_analysis(self, concept_id: str) -> Dict:
        """Get detailed difficulty analysis for a concept"""
        if concept_id not in self.concepts:
            return {'error': 'Concept not found'}
        
        concept = self.concepts[concept_id]
        
        # Calculate complexity factors
        prerequisite_complexity = len(concept.prerequisites) * 0.2
        enabling_complexity = len(concept.enables) * 0.1
        relationship_complexity = len(concept.related_concepts) * 0.05
        
        total_complexity = (concept.difficulty_level + 
                          prerequisite_complexity + 
                          enabling_complexity + 
                          relationship_complexity)
        
        # Determine difficulty category
        if total_complexity < 2:
            difficulty_category = "beginner"
        elif total_complexity < 4:
            difficulty_category = "intermediate"
        elif total_complexity < 6:
            difficulty_category = "advanced"
        else:
            difficulty_category = "expert"
        
        return {
            'concept_id': concept_id,
            'base_difficulty': concept.difficulty_level,
            'total_complexity': round(total_complexity, 2),
            'difficulty_category': difficulty_category,
            'prerequisite_count': len(concept.prerequisites),
            'enables_count': len(concept.enables),
            'related_count': len(concept.related_concepts),
            'subject': concept.subject.value
        }
    
    def get_subject_mastery_overview(self, current_masteries: Dict[str, float], 
                                   subject: SubjectArea) -> Dict:
        """Get comprehensive subject mastery overview"""
        subject_concepts = [c for c in self.concepts.values() if c.subject == subject]
        
        if not subject_concepts:
            return {'error': 'No concepts found for subject'}
        
        mastery_levels = []
        difficulty_distribution = {1: [], 2: [], 3: [], 4: [], 5: []}
        
        for concept in subject_concepts:
            mastery = current_masteries.get(concept.concept_id, 0)
            mastery_levels.append(mastery)
            difficulty_distribution[concept.difficulty_level].append(mastery)
        
        # Calculate statistics
        avg_mastery = sum(mastery_levels) / len(mastery_levels)
        mastered_count = sum(1 for m in mastery_levels if m > 0.8)
        partially_mastered = sum(1 for m in mastery_levels if 0.4 < m <= 0.8)
        weak_concepts = sum(1 for m in mastery_levels if m <= 0.4)
        
        # Difficulty-wise analysis
        difficulty_analysis = {}
        for level, masteries in difficulty_distribution.items():
            if masteries:
                difficulty_analysis[f"level_{level}"] = {
                    'average_mastery': sum(masteries) / len(masteries),
                    'concept_count': len(masteries),
                    'mastered': sum(1 for m in masteries if m > 0.8)
                }
        
        return {
            'subject': subject.value,
            'total_concepts': len(subject_concepts),
            'overall_mastery': round(avg_mastery, 3),
            'mastered_concepts': mastered_count,
            'partially_mastered': partially_mastered,
            'weak_concepts': weak_concepts,
            'mastery_percentage': round((mastered_count / len(subject_concepts)) * 100, 1),
            'difficulty_analysis': difficulty_analysis,
            'readiness_for_advanced': mastered_count > len(subject_concepts) * 0.6
        }
    
    def export_concept_graph(self) -> Dict:
        """Export complete concept graph for visualization"""
        export_data = {
            'concepts': {},
            'relationships': {
                'prerequisites': {},
                'enables': {},
                'related': {}
            },
            'subjects': {subject.value: {
                'roots': list(self.subject_trees[subject]['roots']),
                'leaves': list(self.subject_trees[subject]['leaves'])
            } for subject in SubjectArea}
        }
        
        for concept_id, concept in self.concepts.items():
            export_data['concepts'][concept_id] = {
                'subject': concept.subject.value,
                'difficulty': concept.difficulty_level
            }
            
            export_data['relationships']['prerequisites'][concept_id] = concept.prerequisites
            export_data['relationships']['enables'][concept_id] = concept.enables
            export_data['relationships']['related'][concept_id] = concept.related_concepts
        
        return export_data