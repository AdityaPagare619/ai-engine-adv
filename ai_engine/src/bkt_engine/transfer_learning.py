# Transfer Learning Engine - Inter-concept Learning Enhancement
# Manages knowledge transfer between related concepts

from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
import logging
from .concept_tracker import ConceptTracker, SubjectArea

@dataclass
class TransferEvent:
    """Records a transfer learning event"""
    source_concept: str
    target_concept: str
    transfer_strength: float
    boost_amount: float
    timestamp: datetime
    trigger_mastery: float

class TransferLearningEngine:
    """
    Advanced transfer learning system for concept mastery enhancement
    Applies knowledge from mastered concepts to accelerate learning in related areas
    """
    
    def __init__(self, concept_tracker: ConceptTracker):
        self.concept_tracker = concept_tracker
        self.transfer_history: List[TransferEvent] = []
        self.transfer_matrices: Dict[SubjectArea, np.ndarray] = {}
        self.concept_embeddings: Dict[str, np.ndarray] = {}
        
        self.logger = logging.getLogger(__name__)
        
        # Transfer learning parameters
        self.transfer_threshold = 0.75  # Minimum mastery to trigger transfer
        self.max_transfer_boost = 0.25  # Maximum boost from transfer learning
        self.decay_rate = 0.95  # Transfer strength decay over time
        
        self._initialize_transfer_matrices()
        self._initialize_concept_embeddings()
    
    def _initialize_transfer_matrices(self):
        """Initialize transfer strength matrices for each subject"""
        for subject in SubjectArea:
            subject_concepts = [c.concept_id for c in self.concept_tracker.concepts.values() 
                              if c.subject == subject]
            
            if not subject_concepts:
                continue
            
            n_concepts = len(subject_concepts)
            transfer_matrix = np.zeros((n_concepts, n_concepts))
            
            # Create concept to index mapping
            concept_to_idx = {concept: i for i, concept in enumerate(subject_concepts)}
            
            # Fill transfer matrix based on concept relationships
            for i, source_concept in enumerate(subject_concepts):
                source_node = self.concept_tracker.concepts[source_concept]
                
                # Direct enables relationships (strong transfer)
                for target_concept, strength in source_node.enables.items():
                    if target_concept in concept_to_idx:
                        j = concept_to_idx[target_concept]
                        transfer_matrix[i][j] = strength * 0.8
                
                # Prerequisite relationships (moderate reverse transfer)
                for prereq_concept, strength in source_node.prerequisites.items():
                    if prereq_concept in concept_to_idx:
                        j = concept_to_idx[prereq_concept]
                        transfer_matrix[j][i] = strength * 0.4  # Reverse direction
                
                # Related concepts (weak bidirectional transfer)
                for related_concept, strength in source_node.related_concepts.items():
                    if related_concept in concept_to_idx:
                        j = concept_to_idx[related_concept]
                        transfer_matrix[i][j] = strength * 0.3
                        transfer_matrix[j][i] = strength * 0.3
            
            self.transfer_matrices[subject] = transfer_matrix
            self.concept_to_idx = {subject: concept_to_idx for subject in SubjectArea}
    
    def _initialize_concept_embeddings(self):
        """Initialize concept embeddings for similarity calculations"""
        # Simple embedding based on concept properties
        for concept_id, concept_node in self.concept_tracker.concepts.items():
            # Create feature vector based on concept characteristics
            embedding = np.array([
                concept_node.difficulty_level / 5.0,  # Normalized difficulty
                len(concept_node.prerequisites) / 10.0,  # Normalized prereq count
                len(concept_node.enables) / 10.0,  # Normalized enables count
                len(concept_node.related_concepts) / 15.0,  # Normalized related count
                hash(concept_node.subject.value) % 100 / 100.0,  # Subject encoding
            ])
            
            self.concept_embeddings[concept_id] = embedding
    
    def calculate_transfer_boost(self, target_concept: str, 
                               current_masteries: Dict[str, float],
                               recent_interactions: Optional[List[Dict]] = None) -> Dict:
        """
        Calculate comprehensive transfer learning boost for target concept
        """
        if target_concept not in self.concept_tracker.concepts:
            return {'boost': 0.0, 'sources': [], 'error': 'Concept not found'}
        
        target_node = self.concept_tracker.concepts[target_concept]
        total_boost = 0.0
        transfer_sources = []
        
        # 1. Direct prerequisite transfer
        prereq_boost, prereq_sources = self._calculate_prerequisite_transfer(
            target_concept, current_masteries
        )
        total_boost += prereq_boost
        transfer_sources.extend(prereq_sources)
        
        # 2. Related concept transfer
        related_boost, related_sources = self._calculate_related_transfer(
            target_concept, current_masteries
        )
        total_boost += related_boost
        transfer_sources.extend(related_sources)
        
        # 3. Cross-subject transfer
        cross_boost, cross_sources = self._calculate_cross_subject_transfer(
            target_concept, current_masteries
        )
        total_boost += cross_boost
        transfer_sources.extend(cross_sources)
        
        # 4. Temporal transfer (recent learning momentum)
        if recent_interactions:
            temporal_boost, temporal_sources = self._calculate_temporal_transfer(
                target_concept, recent_interactions, current_masteries
            )
            total_boost += temporal_boost
            transfer_sources.extend(temporal_sources)
        
        # 5. Similarity-based transfer
        similarity_boost, similarity_sources = self._calculate_similarity_transfer(
            target_concept, current_masteries
        )
        total_boost += similarity_boost
        transfer_sources.extend(similarity_sources)
        
        # Cap total boost
        final_boost = min(self.max_transfer_boost, total_boost)
        
        # Record transfer event if significant
        if final_boost > 0.05:
            self._record_transfer_event(target_concept, transfer_sources, final_boost)
        
        return {
            'boost': round(final_boost, 4),
            'sources': transfer_sources,
            'breakdown': {
                'prerequisite': round(prereq_boost, 4),
                'related': round(related_boost, 4),
                'cross_subject': round(cross_boost, 4),
                'temporal': round(temporal_boost if recent_interactions else 0, 4),
                'similarity': round(similarity_boost, 4)
            }
        }
    
    def _calculate_prerequisite_transfer(self, target_concept: str, 
                                       masteries: Dict[str, float]) -> Tuple[float, List[Dict]]:
        """Calculate transfer boost from prerequisite concepts"""
        target_node = self.concept_tracker.concepts[target_concept]
        boost = 0.0
        sources = []
        
        for prereq_id, required_strength in target_node.prerequisites.items():
            prereq_mastery = masteries.get(prereq_id, 0)
            
            if prereq_mastery > self.transfer_threshold:
                # Strong prerequisites provide more transfer
                transfer_strength = required_strength * (prereq_mastery - self.transfer_threshold)
                concept_boost = transfer_strength * 0.2  # 20% of transfer strength
                
                boost += concept_boost
                sources.append({
                    'concept': prereq_id,
                    'type': 'prerequisite',
                    'strength': round(transfer_strength, 4),
                    'boost': round(concept_boost, 4),
                    'mastery': round(prereq_mastery, 4)
                })
        
        return boost, sources
    
    def _calculate_related_transfer(self, target_concept: str, 
                                  masteries: Dict[str, float]) -> Tuple[float, List[Dict]]:
        """Calculate transfer boost from related concepts"""
        target_node = self.concept_tracker.concepts[target_concept]
        boost = 0.0
        sources = []
        
        for related_id, relationship_strength in target_node.related_concepts.items():
            related_mastery = masteries.get(related_id, 0)
            
            if related_mastery > self.transfer_threshold:
                transfer_strength = relationship_strength * (related_mastery - self.transfer_threshold)
                concept_boost = transfer_strength * 0.1  # 10% of transfer strength
                
                boost += concept_boost
                sources.append({
                    'concept': related_id,
                    'type': 'related',
                    'strength': round(transfer_strength, 4),
                    'boost': round(concept_boost, 4),
                    'mastery': round(related_mastery, 4)
                })
        
        return boost, sources
    
    def _calculate_cross_subject_transfer(self, target_concept: str, 
                                        masteries: Dict[str, float]) -> Tuple[float, List[Dict]]:
        """Calculate transfer boost from concepts in other subjects"""
        target_node = self.concept_tracker.concepts[target_concept]
        boost = 0.0
        sources = []
        
        # Check concepts from other subjects that might transfer
        cross_subject_pairs = {
            # Math to Physics transfers
            ('calculus', 'kinematics'): 0.4,
            ('derivatives', 'dynamics'): 0.5,
            ('integrals', 'work_energy'): 0.6,
            ('vectors', 'electrostatics'): 0.7,
            ('trigonometry', 'wave_optics'): 0.4,
            ('complex_numbers', 'ac_circuits'): 0.5,
            ('probability', 'quantum_mechanics'): 0.3,
            
            # Physics to Chemistry transfers
            ('thermodynamics', 'thermochemistry'): 0.8,
            ('current_electricity', 'electrochemistry'): 0.7,
            ('atomic_physics', 'atomic_structure'): 0.9,
            ('electromagnetic_radiation', 'quantum_chemistry'): 0.6,
            
            # Chemistry to Physics transfers
            ('atomic_structure', 'atomic_physics'): 0.8,
            ('chemical_bonding', 'solid_state_physics'): 0.6,
            
            # Math to Chemistry transfers
            ('logarithms', 'chemical_kinetics'): 0.4,
            ('coordinate_geometry', 'molecular_geometry'): 0.5,
        }
        
        for (source, target), strength in cross_subject_pairs.items():
            if target == target_concept and source in masteries:
                source_mastery = masteries[source]
                if source_mastery > self.transfer_threshold:
                    transfer_strength = strength * (source_mastery - self.transfer_threshold)
                    concept_boost = transfer_strength * 0.15  # 15% for cross-subject
                    
                    boost += concept_boost
                    sources.append({
                        'concept': source,
                        'type': 'cross_subject',
                        'strength': round(transfer_strength, 4),
                        'boost': round(concept_boost, 4),
                        'mastery': round(source_mastery, 4)
                    })
        
        return boost, sources
    
    def _calculate_temporal_transfer(self, target_concept: str, 
                                   recent_interactions: List[Dict],
                                   masteries: Dict[str, float]) -> Tuple[float, List[Dict]]:
        """Calculate transfer boost from recent learning momentum"""
        boost = 0.0
        sources = []
        
        if not recent_interactions:
            return boost, sources
        
        # Get recent successful interactions (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_successes = [
            interaction for interaction in recent_interactions
            if (interaction.get('is_correct', False) and 
                datetime.fromisoformat(interaction.get('timestamp', '')) > cutoff_time)
        ]
        
        if len(recent_successes) >= 3:  # Minimum momentum threshold
            # Calculate momentum factor
            success_rate = len(recent_successes) / len(recent_interactions[-10:])  # Last 10 interactions
            momentum_boost = min(0.1, success_rate * 0.15)  # Up to 10% boost
            
            boost += momentum_boost
            sources.append({
                'concept': 'learning_momentum',
                'type': 'temporal',
                'strength': round(success_rate, 4),
                'boost': round(momentum_boost, 4),
                'recent_successes': len(recent_successes)
            })
        
        return boost, sources
    
    def _calculate_similarity_transfer(self, target_concept: str, 
                                     masteries: Dict[str, float]) -> Tuple[float, List[Dict]]:
        """Calculate transfer boost from similar concepts using embeddings"""
        if target_concept not in self.concept_embeddings:
            return 0.0, []
        
        target_embedding = self.concept_embeddings[target_concept]
        boost = 0.0
        sources = []
        
        # Find most similar concepts with high mastery
        similarities = []
        for concept_id, embedding in self.concept_embeddings.items():
            if concept_id != target_concept and concept_id in masteries:
                mastery = masteries[concept_id]
                if mastery > self.transfer_threshold:
                    # Calculate cosine similarity
                    similarity = np.dot(target_embedding, embedding) / (
                        np.linalg.norm(target_embedding) * np.linalg.norm(embedding)
                    )
                    similarities.append((concept_id, similarity, mastery))
        
        # Sort by similarity and take top 3
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_similar = similarities[:3]
        
        for concept_id, similarity, mastery in top_similar:
            if similarity > 0.7:  # High similarity threshold
                transfer_strength = similarity * (mastery - self.transfer_threshold)
                concept_boost = transfer_strength * 0.08  # 8% of transfer strength
                
                boost += concept_boost
                sources.append({
                    'concept': concept_id,
                    'type': 'similarity',
                    'strength': round(transfer_strength, 4),
                    'boost': round(concept_boost, 4),
                    'similarity': round(similarity, 4),
                    'mastery': round(mastery, 4)
                })
        
        return boost, sources
    
    def _record_transfer_event(self, target_concept: str, sources: List[Dict], boost: float):
        """Record a significant transfer learning event"""
        for source in sources:
            if source['concept'] != 'learning_momentum':
                event = TransferEvent(
                    source_concept=source['concept'],
                    target_concept=target_concept,
                    transfer_strength=source['strength'],
                    boost_amount=source['boost'],
                    timestamp=datetime.now(),
                    trigger_mastery=source.get('mastery', 0)
                )
                self.transfer_history.append(event)
        
        # Keep only last 1000 events
        if len(self.transfer_history) > 1000:
            self.transfer_history = self.transfer_history[-1000:]
    
    def get_transfer_analytics(self, time_window_hours: int = 24) -> Dict:
        """Get analytics on recent transfer learning activity"""
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        recent_events = [e for e in self.transfer_history if e.timestamp > cutoff_time]
        
        if not recent_events:
            return {'message': 'No recent transfer events'}
        
        # Analyze transfer patterns
        source_counts = {}
        target_counts = {}
        total_boost = 0.0
        
        for event in recent_events:
            source_counts[event.source_concept] = source_counts.get(event.source_concept, 0) + 1
            target_counts[event.target_concept] = target_counts.get(event.target_concept, 0) + 1
            total_boost += event.boost_amount
        
        # Find most active concepts
        top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_targets = sorted(target_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'time_window_hours': time_window_hours,
            'total_events': len(recent_events),
            'total_boost_provided': round(total_boost, 4),
            'average_boost_per_event': round(total_boost / len(recent_events), 4),
            'top_source_concepts': [{'concept': c, 'events': count} for c, count in top_sources],
            'top_target_concepts': [{'concept': c, 'events': count} for c, count in top_targets],
            'transfer_efficiency': round(total_boost / len(recent_events) * 100, 2)  # Percentage
        }
    
    def get_concept_transfer_potential(self, concept_id: str, 
                                     current_masteries: Dict[str, float]) -> Dict:
        """Analyze the transfer learning potential of a specific concept"""
        if concept_id not in self.concept_tracker.concepts:
            return {'error': 'Concept not found'}
        
        current_mastery = current_masteries.get(concept_id, 0)
        concept_node = self.concept_tracker.concepts[concept_id]
        
        # Calculate potential as source
        source_potential = 0.0
        potential_targets = []
        
        if current_mastery > self.transfer_threshold:
            # Check what this concept can help with
            for target_id in self.concept_tracker.concepts:
                if target_id != concept_id:
                    transfer_data = self.calculate_transfer_boost(target_id, current_masteries)
                    for source in transfer_data['sources']:
                        if source['concept'] == concept_id:
                            source_potential += source['boost']
                            potential_targets.append({
                                'target': target_id,
                                'potential_boost': source['boost'],
                                'transfer_type': source['type']
                            })
        
        # Calculate potential as target
        target_potential = self.calculate_transfer_boost(concept_id, current_masteries)
        
        return {
            'concept_id': concept_id,
            'current_mastery': round(current_mastery, 4),
            'as_source': {
                'total_potential': round(source_potential, 4),
                'can_help_concepts': len(potential_targets),
                'top_targets': sorted(potential_targets, key=lambda x: x['potential_boost'], reverse=True)[:3]
            },
            'as_target': {
                'current_boost_available': target_potential['boost'],
                'boost_sources': len(target_potential['sources']),
                'breakdown': target_potential['breakdown']
            },
            'transfer_readiness': 'high' if current_mastery > 0.8 else 'medium' if current_mastery > 0.6 else 'low'
        }
    
    def optimize_learning_sequence(self, target_concepts: List[str], 
                                 current_masteries: Dict[str, float]) -> List[Dict]:
        """Optimize learning sequence to maximize transfer learning benefits"""
        if not target_concepts:
            return []
        
        # Calculate transfer potential for each concept
        concept_scores = []
        for concept in target_concepts:
            if concept in self.concept_tracker.concepts:
                # Score based on: current readiness + transfer potential + difficulty
                prerequisites_met = self._check_prerequisites(concept, current_masteries)
                transfer_boost = self.calculate_transfer_boost(concept, current_masteries)
                difficulty = self.concept_tracker.concepts[concept].difficulty_level
                
                # Calculate composite score
                readiness_score = 1.0 if prerequisites_met else 0.3
                transfer_score = min(1.0, transfer_boost['boost'] * 4)  # Scale boost to 0-1
                difficulty_penalty = (6 - difficulty) / 5  # Easier concepts score higher
                
                composite_score = (readiness_score * 0.4 + 
                                 transfer_score * 0.4 + 
                                 difficulty_penalty * 0.2)
                
                concept_scores.append({
                    'concept': concept,
                    'score': composite_score,
                    'readiness': readiness_score,
                    'transfer_potential': transfer_score,
                    'difficulty_factor': difficulty_penalty,
                    'current_boost': transfer_boost['boost'],
                    'prerequisites_met': prerequisites_met
                })
        
        # Sort by composite score (highest first)
        optimal_sequence = sorted(concept_scores, key=lambda x: x['score'], reverse=True)
        
        return optimal_sequence
    
    def _check_prerequisites(self, concept_id: str, masteries: Dict[str, float]) -> bool:
        """Check if prerequisites are sufficiently met for a concept"""
        if concept_id not in self.concept_tracker.concepts:
            return False
        
        concept_node = self.concept_tracker.concepts[concept_id]
        
        for prereq_id, required_strength in concept_node.prerequisites.items():
            current_mastery = masteries.get(prereq_id, 0)
            if current_mastery < required_strength * 0.8:  # 80% of required strength
                return False
        
        return True
    
    def export_transfer_data(self) -> Dict:
        """Export transfer learning data for analysis"""
        return {
            'transfer_history': [
                {
                    'source': event.source_concept,
                    'target': event.target_concept,
                    'strength': event.transfer_strength,
                    'boost': event.boost_amount,
                    'timestamp': event.timestamp.isoformat(),
                    'trigger_mastery': event.trigger_mastery
                }
                for event in self.transfer_history[-100:]  # Last 100 events
            ],
            'transfer_matrices': {
                subject.value: matrix.tolist() 
                for subject, matrix in self.transfer_matrices.items()
            },
            'parameters': {
                'transfer_threshold': self.transfer_threshold,
                'max_transfer_boost': self.max_transfer_boost,
                'decay_rate': self.decay_rate
            }
        }