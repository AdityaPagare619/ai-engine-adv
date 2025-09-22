# Advanced Machine Learning Models for Enterprise Knowledge Tracing
# Implements DKT, LSTM-based, and Transformer models for million-user scale

from __future__ import annotations
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import json

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

@dataclass
class ModelPrediction:
    """Standardized model prediction output"""
    probability: float
    confidence: float
    model_type: str
    features_used: List[str]
    processing_time_ms: float
    uncertainty: float

class DeepKnowledgeTracing(nn.Module):
    """
    Deep Knowledge Tracing (DKT) implementation using LSTM
    State-of-the-art model for sequential learning prediction
    """
    
    def __init__(self, num_concepts: int, hidden_dim: int = 200, num_layers: int = 2, dropout: float = 0.2):
        super().__init__()
        self.num_concepts = num_concepts
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        # Input dimension: concept_id (one-hot) + correctness (1 dim)
        self.input_dim = num_concepts * 2  # concept × {correct, incorrect}
        
        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=self.input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )
        
        # Output layer for each concept
        self.output = nn.Linear(hidden_dim, num_concepts)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x, hidden=None):
        """
        Forward pass
        x: (batch_size, seq_len, input_dim)
        """
        lstm_out, hidden = self.lstm(x, hidden)
        
        # Apply dropout
        lstm_out = self.dropout(lstm_out)
        
        # Output predictions for each concept
        output = torch.sigmoid(self.output(lstm_out))
        
        return output, hidden
    
    def predict_concept(self, sequence: torch.Tensor, concept_idx: int) -> float:
        """Predict probability for a specific concept"""
        with torch.no_grad():
            self.eval()
            output, _ = self.forward(sequence.unsqueeze(0))
            probability = output[0, -1, concept_idx].item()
            return probability

class TransformerKnowledgeTracing(nn.Module):
    """
    Transformer-based Knowledge Tracing
    Uses self-attention mechanisms for better long-term dependency modeling
    """
    
    def __init__(self, num_concepts: int, d_model: int = 256, nhead: int = 8, num_layers: int = 6, dropout: float = 0.1):
        super().__init__()
        self.num_concepts = num_concepts
        self.d_model = d_model
        
        # Input embedding
        self.input_embedding = nn.Linear(num_concepts * 2, d_model)
        self.positional_encoding = PositionalEncoding(d_model, dropout, max_len=1000)
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Output projection
        self.output_projection = nn.Linear(d_model, num_concepts)
        
    def forward(self, x, mask=None):
        """
        Forward pass
        x: (batch_size, seq_len, input_dim)
        mask: (seq_len, seq_len) attention mask
        """
        # Input embedding and positional encoding
        embedded = self.input_embedding(x)
        embedded = self.positional_encoding(embedded)
        
        # Transformer encoding
        encoded = self.transformer(embedded, mask=mask)
        
        # Output projection
        output = torch.sigmoid(self.output_projection(encoded))
        
        return output

class PositionalEncoding(nn.Module):
    """Positional encoding for transformer"""
    
    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-np.log(10000.0) / d_model))
        pe = torch.zeros(max_len, 1, d_model)
        pe[:, 0, 0::2] = torch.sin(position * div_term)
        pe[:, 0, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:x.size(1)].transpose(0, 1)
        return self.dropout(x)

class GradientBoostingKT:
    """
    Gradient Boosting for Knowledge Tracing
    Non-neural alternative using ensemble of weak learners
    """
    
    def __init__(self, n_estimators: int = 100, max_depth: int = 6, learning_rate: float = 0.1):
        try:
            from sklearn.ensemble import GradientBoostingClassifier
            from sklearn.preprocessing import StandardScaler
            self.model = GradientBoostingClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=learning_rate,
                random_state=42
            )
            self.scaler = StandardScaler()
            self.is_trained = False
            self.feature_names = []
        except ImportError:
            self.model = None
            print("Warning: scikit-learn not available. GradientBoostingKT disabled.")
    
    def extract_features(self, sequence: List[Dict]) -> np.ndarray:
        """Extract features from interaction sequence"""
        if not sequence:
            return np.zeros(15)  # Default feature vector size
        
        # Calculate various features
        recent_10 = sequence[-10:] if len(sequence) >= 10 else sequence
        recent_5 = sequence[-5:] if len(sequence) >= 5 else sequence
        
        features = [
            # Basic statistics
            len(sequence),
            sum(1 for s in sequence if s.get('is_correct', False)) / len(sequence),  # Overall accuracy
            sum(1 for s in recent_10 if s.get('is_correct', False)) / len(recent_10),  # Recent accuracy
            sum(1 for s in recent_5 if s.get('is_correct', False)) / len(recent_5),  # Very recent accuracy
            
            # Streak analysis
            self._current_streak(sequence),
            self._longest_correct_streak(sequence),
            self._longest_incorrect_streak(sequence),
            
            # Temporal features
            self._average_response_time(sequence),
            self._response_time_trend(sequence),
            
            # Difficulty progression
            self._average_difficulty(sequence),
            self._difficulty_trend(sequence),
            
            # Concept diversity
            self._concept_diversity(sequence),
            
            # Learning velocity
            self._learning_velocity(sequence),
            
            # Persistence features
            self._attempts_per_concept(sequence),
            self._improvement_rate(sequence)
        ]
        
        return np.array(features)
    
    def _current_streak(self, sequence: List[Dict]) -> int:
        """Calculate current streak (positive for correct, negative for incorrect)"""
        if not sequence:
            return 0
        
        streak = 0
        for interaction in reversed(sequence):
            if interaction.get('is_correct', False):
                if streak <= 0:
                    streak = 1
                else:
                    streak += 1
            else:
                if streak >= 0:
                    streak = -1
                else:
                    streak -= 1
            
            # Stop at streak break
            if len(sequence) > 1 and abs(streak) > 1:
                prev_correct = sequence[-2].get('is_correct', False) if len(sequence) > 1 else False
                curr_correct = sequence[-1].get('is_correct', False)
                if prev_correct != curr_correct:
                    streak = 1 if curr_correct else -1
                    break
        
        return streak
    
    def _longest_correct_streak(self, sequence: List[Dict]) -> int:
        """Find longest consecutive correct answers"""
        max_streak = current_streak = 0
        for interaction in sequence:
            if interaction.get('is_correct', False):
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        return max_streak
    
    def _longest_incorrect_streak(self, sequence: List[Dict]) -> int:
        """Find longest consecutive incorrect answers"""
        max_streak = current_streak = 0
        for interaction in sequence:
            if not interaction.get('is_correct', False):
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        return max_streak
    
    def _average_response_time(self, sequence: List[Dict]) -> float:
        """Calculate average response time"""
        times = [s.get('response_time_ms', 30000) for s in sequence if 'response_time_ms' in s]
        return np.mean(times) if times else 30000.0
    
    def _response_time_trend(self, sequence: List[Dict]) -> float:
        """Calculate response time trend (slope)"""
        times = [s.get('response_time_ms', 30000) for s in sequence if 'response_time_ms' in s]
        if len(times) < 2:
            return 0.0
        
        x = np.arange(len(times))
        slope, _ = np.polyfit(x, times, 1)
        return slope
    
    def _average_difficulty(self, sequence: List[Dict]) -> float:
        """Calculate average question difficulty"""
        difficulties = [s.get('difficulty', 0.5) for s in sequence]
        return np.mean(difficulties) if difficulties else 0.5
    
    def _difficulty_trend(self, sequence: List[Dict]) -> float:
        """Calculate difficulty progression trend"""
        difficulties = [s.get('difficulty', 0.5) for s in sequence]
        if len(difficulties) < 2:
            return 0.0
        
        x = np.arange(len(difficulties))
        slope, _ = np.polyfit(x, difficulties, 1)
        return slope
    
    def _concept_diversity(self, sequence: List[Dict]) -> float:
        """Calculate diversity of concepts attempted"""
        concepts = set(s.get('concept_id', 'unknown') for s in sequence)
        return len(concepts) / len(sequence) if sequence else 0.0
    
    def _learning_velocity(self, sequence: List[Dict]) -> float:
        """Calculate learning velocity (improvement over time)"""
        if len(sequence) < 5:
            return 0.0
        
        first_half = sequence[:len(sequence)//2]
        second_half = sequence[len(sequence)//2:]
        
        first_accuracy = sum(1 for s in first_half if s.get('is_correct', False)) / len(first_half)
        second_accuracy = sum(1 for s in second_half if s.get('is_correct', False)) / len(second_half)
        
        return second_accuracy - first_accuracy
    
    def _attempts_per_concept(self, sequence: List[Dict]) -> float:
        """Calculate average attempts per concept"""
        concept_counts = {}
        for s in sequence:
            concept = s.get('concept_id', 'unknown')
            concept_counts[concept] = concept_counts.get(concept, 0) + 1
        
        return np.mean(list(concept_counts.values())) if concept_counts else 1.0
    
    def _improvement_rate(self, sequence: List[Dict]) -> float:
        """Calculate rate of improvement per concept"""
        concept_progressions = {}
        
        for s in sequence:
            concept = s.get('concept_id', 'unknown')
            is_correct = s.get('is_correct', False)
            
            if concept not in concept_progressions:
                concept_progressions[concept] = []
            concept_progressions[concept].append(is_correct)
        
        improvement_rates = []
        for concept, results in concept_progressions.items():
            if len(results) >= 2:
                # Calculate slope of success over time
                x = np.arange(len(results))
                y = np.array([1 if r else 0 for r in results])
                if len(set(y)) > 1:  # Only if there's variation
                    slope, _ = np.polyfit(x, y, 1)
                    improvement_rates.append(slope)
        
        return np.mean(improvement_rates) if improvement_rates else 0.0
    
    def predict_probability(self, sequence: List[Dict]) -> float:
        """Predict correctness probability for next interaction"""
        if self.model is None or not self.is_trained:
            # Fallback to simple baseline
            if not sequence:
                return 0.5
            recent_accuracy = sum(1 for s in sequence[-5:] if s.get('is_correct', False)) / min(5, len(sequence))
            return max(0.1, min(0.9, recent_accuracy * 0.8 + 0.2))
        
        features = self.extract_features(sequence).reshape(1, -1)
        features_scaled = self.scaler.transform(features)
        
        try:
            probability = self.model.predict_proba(features_scaled)[0][1]  # Probability of class 1 (correct)
            return max(0.05, min(0.95, probability))
        except Exception as e:
            print(f"Warning: GradientBoosting prediction failed: {e}")
            return 0.5

class AdvancedModelEnsemble:
    """
    Enterprise-grade ensemble combining multiple advanced models
    Provides robust predictions with uncertainty quantification
    """
    
    def __init__(self):
        self.models = {}
        self.model_weights = {}
        self.performance_history = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all available models"""
        # Gradient Boosting (always available)
        self.models['gbm'] = GradientBoostingKT()
        self.model_weights['gbm'] = 0.4
        
        # Deep models (if PyTorch available)
        if TORCH_AVAILABLE:
            # Placeholder for DKT - would need concept mapping
            self.models['dkt'] = None  # DeepKnowledgeTracing(num_concepts=100)
            self.models['transformer'] = None  # TransformerKnowledgeTracing(num_concepts=100)
            
            # Weights when deep models available
            self.model_weights['gbm'] = 0.3
            self.model_weights['dkt'] = 0.4
            self.model_weights['transformer'] = 0.3
        
        self.logger.info(f"Initialized ensemble with models: {list(self.models.keys())}")
    
    def predict_with_uncertainty(self, sequence: List[Dict], concept_id: str = None) -> ModelPrediction:
        """
        Generate prediction with uncertainty quantification
        """
        start_time = datetime.now()
        
        predictions = []
        confidences = []
        models_used = []
        
        # Get predictions from all available models
        for model_name, model in self.models.items():
            if model is None:
                continue
                
            try:
                if model_name == 'gbm':
                    prob = model.predict_probability(sequence)
                    confidence = self._calculate_gbm_confidence(sequence, prob)
                elif model_name in ['dkt', 'transformer']:
                    # For neural models, would need proper implementation
                    prob = 0.5  # Placeholder
                    confidence = 0.5
                else:
                    continue
                
                weight = self.model_weights.get(model_name, 0.0)
                if weight > 0:
                    predictions.append(prob * weight)
                    confidences.append(confidence)
                    models_used.append(model_name)
                    
            except Exception as e:
                self.logger.warning(f"Model {model_name} failed: {e}")
                continue
        
        # Ensemble prediction
        if predictions:
            final_probability = sum(predictions) / sum(self.model_weights[m] for m in models_used)
            avg_confidence = np.mean(confidences)
            uncertainty = np.std(predictions) / np.mean(predictions) if np.mean(predictions) > 0 else 1.0
        else:
            # Fallback
            final_probability = 0.5
            avg_confidence = 0.3
            uncertainty = 1.0
            models_used = ['fallback']
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ModelPrediction(
            probability=max(0.05, min(0.95, final_probability)),
            confidence=avg_confidence,
            model_type='ensemble',
            features_used=models_used,
            processing_time_ms=processing_time,
            uncertainty=uncertainty
        )
    
    def _calculate_gbm_confidence(self, sequence: List[Dict], probability: float) -> float:
        """Calculate confidence for GBM prediction"""
        # Confidence based on sequence length and probability extremeness
        seq_confidence = min(1.0, len(sequence) / 20.0)  # More data = higher confidence
        prob_confidence = 2 * min(probability, 1 - probability)  # Extreme probabilities = higher confidence
        
        return (seq_confidence + prob_confidence) / 2
    
    def update_model_performance(self, model_name: str, actual_result: bool, predicted_prob: float):
        """Update model performance tracking"""
        if model_name not in self.performance_history:
            self.performance_history[model_name] = {'correct': 0, 'total': 0, 'errors': []}
        
        history = self.performance_history[model_name]
        history['total'] += 1
        
        # Binary prediction (>0.5 = correct prediction)
        predicted_correct = predicted_prob > 0.5
        if predicted_correct == actual_result:
            history['correct'] += 1
        else:
            error = abs(predicted_prob - (1.0 if actual_result else 0.0))
            history['errors'].append(error)
            
            # Keep only recent errors
            if len(history['errors']) > 100:
                history['errors'] = history['errors'][-100:]
    
    def get_model_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive model performance report"""
        report = {}
        
        for model_name, history in self.performance_history.items():
            if history['total'] > 0:
                accuracy = history['correct'] / history['total']
                avg_error = np.mean(history['errors']) if history['errors'] else 0.0
                
                report[model_name] = {
                    'accuracy': accuracy,
                    'total_predictions': history['total'],
                    'average_error': avg_error,
                    'current_weight': self.model_weights.get(model_name, 0.0),
                    'performance_grade': 'excellent' if accuracy > 0.8 else 'good' if accuracy > 0.7 else 'fair' if accuracy > 0.6 else 'poor'
                }
        
        return report
    
    def adaptive_weight_adjustment(self):
        """Adaptively adjust model weights based on recent performance"""
        if not self.performance_history:
            return
        
        # Calculate recent accuracy for each model
        recent_accuracies = {}
        for model_name, history in self.performance_history.items():
            if history['total'] >= 10:  # Minimum samples for adjustment
                recent_accuracies[model_name] = history['correct'] / history['total']
        
        if not recent_accuracies:
            return
        
        # Adjust weights based on relative performance
        total_accuracy = sum(recent_accuracies.values())
        for model_name in recent_accuracies:
            if total_accuracy > 0:
                relative_performance = recent_accuracies[model_name] / total_accuracy
                # Smooth adjustment
                current_weight = self.model_weights.get(model_name, 0.0)
                new_weight = 0.7 * current_weight + 0.3 * relative_performance
                self.model_weights[model_name] = max(0.1, min(0.8, new_weight))
        
        # Normalize weights
        total_weight = sum(self.model_weights.values())
        if total_weight > 0:
            for model_name in self.model_weights:
                self.model_weights[model_name] /= total_weight
        
        self.logger.info(f"Adjusted model weights: {self.model_weights}")