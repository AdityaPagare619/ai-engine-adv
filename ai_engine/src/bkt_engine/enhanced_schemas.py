# Enhanced Database Schemas for BKT Engine
# Based on proven knowledge_tracing schemas with additional enterprise features

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List, Union, Tuple
from datetime import datetime
from enum import Enum

class ExamType(str, Enum):
    """Supported exam types"""
    JEE_MAIN = "JEE_MAIN"
    JEE_ADVANCED = "JEE_ADVANCED"
    NEET = "NEET"
    FOUNDATION = "FOUNDATION"

class DifficultyLevel(str, Enum):
    """Question difficulty levels"""
    VERY_EASY = "VERY_EASY"
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    VERY_HARD = "VERY_HARD"

class InterventionLevel(str, Enum):
    """Intervention intensity levels"""
    NONE = "NONE"
    MILD = "MILD"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    CRITICAL = "CRITICAL"

class EnhancedTraceRequest(BaseModel):
    """Enhanced trace request with all context factors"""
    # Core fields
    student_id: str = Field(..., description="UUID of the student")
    concept_id: str = Field(..., description="Unique concept ID")
    is_correct: bool = Field(..., description="Whether the answer was correct")
    
    # Question context
    question_id: Optional[str] = Field(None, description="Question ID for tracking")
    difficulty: float = Field(0.5, ge=0.0, le=1.0, description="Question difficulty from 0 to 1")
    difficulty_level: Optional[DifficultyLevel] = Field(None, description="Editorial difficulty label")
    bloom_level: Optional[str] = Field(None, description="Bloom taxonomy level")
    
    # Timing and response
    response_time_ms: Optional[int] = Field(None, ge=0, description="Response time in milliseconds")
    time_pressure: float = Field(1.0, ge=0.5, le=2.0, description="Time pressure factor")
    
    # Context factors from proven system
    stress_level: float = Field(0.0, ge=0.0, le=1.0, description="Detected stress level")
    cognitive_load: float = Field(0.0, ge=0.0, le=1.0, description="Cognitive load assessment")
    fatigue_level: float = Field(0.0, ge=0.0, le=1.0, description="Student fatigue level")
    
    # Session context
    session_id: Optional[str] = Field(None, description="Learning session ID")
    time_of_day: Optional[str] = Field(None, description="Time when question was answered")
    device_type: Optional[str] = Field(None, description="Device used (desktop/mobile/tablet)")
    
    # Additional metadata
    hint_used: bool = Field(False, description="Whether student used hints")
    attempt_number: int = Field(1, ge=1, description="Attempt number for this question")
    exam_type: Optional[ExamType] = Field(None, description="Target exam type")
    
    @field_validator("student_id", "concept_id")
    @classmethod
    def non_empty(cls, v: str):
        assert isinstance(v, str) and len(v) > 0, "must be non-empty"
        return v

class CognitiveLoadAssessment(BaseModel):
    """Cognitive load assessment results"""
    total_load: float = Field(..., ge=0.0, le=1.0, description="Overall cognitive load")
    intrinsic_load: float = Field(..., ge=0.0, le=1.0, description="Content complexity load")
    extraneous_load: float = Field(..., ge=0.0, le=1.0, description="Interface/distraction load")
    germane_load: float = Field(..., ge=0.0, le=1.0, description="Learning process load")
    overload_risk: float = Field(..., ge=0.0, le=1.0, description="Risk of cognitive overload")
    recommendations: List[str] = Field(default_factory=list, description="Load management recommendations")

class InterventionData(BaseModel):
    """Intervention recommendation data"""
    strategy: str = Field(..., description="Name of the intervention strategy")
    level: InterventionLevel = Field(..., description="Intervention intensity level")
    recommendations: List[str] = Field(..., description="Specific recommendations")
    success_probability: float = Field(..., ge=0.0, le=1.0, description="Estimated success probability")
    trigger_reason: str = Field(..., description="Why intervention was triggered")
    estimated_duration_minutes: Optional[int] = Field(None, description="Estimated intervention duration")

class TransferLearningData(BaseModel):
    """Transfer learning updates data"""
    source_concept: str = Field(..., description="Source concept for transfer")
    target_concept: str = Field(..., description="Target concept receiving transfer")
    transfer_coefficient: float = Field(..., ge=0.0, le=1.0, description="Strength of transfer")
    mastery_boost: float = Field(..., description="Mastery boost applied")
    confidence_impact: float = Field(..., description="Impact on confidence")

class EnhancedTraceResponse(BaseModel):
    """Enhanced trace response with comprehensive data"""
    # Core BKT results
    student_id: str
    concept_id: str
    previous_mastery: float = Field(..., ge=0.0, le=1.0)
    new_mastery: float = Field(..., ge=0.0, le=1.0)
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    practice_count: int = Field(..., ge=0)
    
    # Prediction and parameters
    p_correct_next: float = Field(..., ge=0.0, le=1.0, description="Probability of next question correct")
    parameters_used: Dict[str, float] = Field(..., description="BKT parameters used in update")
    
    # Context impact analysis
    context_impact: Dict[str, float] = Field(default_factory=dict, description="Impact of context factors")
    cognitive_load: CognitiveLoadAssessment
    
    # Transfer learning
    transfer_updates: Dict[str, float] = Field(default_factory=dict, description="Related concept updates")
    
    # Interventions and recommendations
    intervention: Optional[InterventionData] = Field(None, description="Intervention recommendation if needed")
    
    # Advanced analytics
    learning_trajectory: Dict[str, Any] = Field(default_factory=dict, description="Learning progress indicators")
    performance_prediction: Dict[str, float] = Field(default_factory=dict, description="Future performance predictions")
    
    # System metadata
    processing_time_ms: Optional[float] = Field(None, description="Time taken to process request")
    model_version: str = Field("enhanced_v2", description="BKT model version used")
    success: bool = Field(True, description="Whether update was successful")

class BKTEvaluationRequest(BaseModel):
    """Request for BKT evaluation metrics"""
    concept_id: Optional[str] = Field(None, description="Limit evaluation to this concept")
    student_id: Optional[str] = Field(None, description="Limit evaluation to this student")
    exam_type: Optional[ExamType] = Field(None, description="Filter by exam type")
    start_timestamp: Optional[datetime] = Field(None, description="Start time filter")
    end_timestamp: Optional[datetime] = Field(None, description="End time filter")
    min_interactions: int = Field(10, description="Minimum interactions required for evaluation")
    include_detailed_analysis: bool = Field(False, description="Include detailed breakdown")

class BKTEvaluationResponse(BaseModel):
    """Comprehensive BKT evaluation results matching proven system metrics"""
    # Next-step prediction metrics (core validation)
    next_step_auc: float = Field(..., ge=0.0, le=1.0, description="Area under ROC curve")
    next_step_accuracy: float = Field(..., ge=0.0, le=1.0, description="Prediction accuracy")
    
    # Calibration metrics
    brier_score: float = Field(..., ge=0.0, le=1.0, description="Brier reliability score")
    calibration_error: float = Field(..., ge=0.0, le=1.0, description="Expected calibration error")
    
    # Trajectory analysis
    trajectory_validity: float = Field(..., ge=0.0, le=1.0, description="Learning trajectory validity score")
    mastery_progression_score: float = Field(..., ge=0.0, le=1.0, description="Quality of mastery progression")
    
    # Additional proven metrics
    knowledge_retention_score: float = Field(..., ge=0.0, le=1.0, description="Long-term retention prediction")
    transfer_learning_effectiveness: float = Field(..., ge=0.0, le=1.0, description="Cross-concept transfer success")
    adaptive_parameter_stability: float = Field(..., ge=0.0, le=1.0, description="Parameter adaptation stability")
    
    # System performance
    convergence_rate: float = Field(..., description="How quickly mastery estimates converge")
    prediction_variance: float = Field(..., description="Variance in prediction accuracy")
    
    # Overall assessment
    recommendation: str = Field(..., description="System recommendation (EXCELLENT/GOOD/NEEDS_IMPROVEMENT/CRITICAL)")
    overall_quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall system quality")
    
    # Detailed breakdown (optional)
    concept_breakdown: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Per-concept metrics")
    temporal_analysis: Dict[str, float] = Field(default_factory=dict, description="Time-based performance")
    student_segment_analysis: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Performance by student segment")
    
    # Metadata
    evaluation_period: str = Field(..., description="Time period evaluated")
    total_interactions: int = Field(..., description="Total interactions analyzed")
    total_students: int = Field(..., description="Total students in evaluation")
    total_concepts: int = Field(..., description="Total concepts analyzed")

class StudentProfileRequest(BaseModel):
    """Request for student profile data"""
    student_id: str = Field(..., description="Student identifier")
    include_concept_details: bool = Field(True, description="Include per-concept mastery details")
    include_learning_analytics: bool = Field(True, description="Include learning pattern analysis")
    include_predictions: bool = Field(False, description="Include future performance predictions")
    time_window_days: Optional[int] = Field(None, description="Limit to recent N days")

class ConceptMasteryDetail(BaseModel):
    """Detailed concept mastery information"""
    concept_id: str
    mastery_probability: float = Field(..., ge=0.0, le=1.0)
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    practice_count: int = Field(..., ge=0)
    consecutive_errors: int = Field(..., ge=0)
    last_interaction: datetime
    recent_performance: List[bool] = Field(default_factory=list)
    learning_rate: float = Field(..., ge=0.0, le=1.0)
    difficulty_comfort_zone: Tuple[float, float] = Field(..., description="Comfortable difficulty range")
    predicted_exam_performance: float = Field(..., ge=0.0, le=1.0)

class StudentProfileResponse(BaseModel):
    """Comprehensive student profile response"""
    # Basic info
    student_id: str
    profile_generated_at: datetime
    
    # Overall performance
    overall_performance: float = Field(..., ge=0.0, le=1.0, description="Overall performance score")
    total_interactions: int = Field(..., ge=0)
    active_days: int = Field(..., ge=0)
    
    # Learning characteristics
    learning_velocity: float = Field(..., description="Rate of learning (concepts/day)")
    retention_strength: float = Field(..., ge=0.0, le=1.0, description="Knowledge retention ability")
    stress_resilience: float = Field(..., ge=0.0, le=1.0, description="Performance under stress")
    cognitive_load_tolerance: float = Field(..., ge=0.0, le=1.0, description="Ability to handle complex questions")
    
    # Adaptive characteristics
    preferred_difficulty_level: float = Field(..., ge=0.0, le=1.0, description="Optimal difficulty for learning")
    optimal_session_length: int = Field(..., description="Optimal study session length in minutes")
    best_time_of_day: Optional[str] = Field(None, description="Peak performance time")
    
    # Concept mastery details
    concept_masteries: Dict[str, ConceptMasteryDetail] = Field(default_factory=dict)
    
    # Subject-level analysis
    subject_strengths: Dict[str, float] = Field(default_factory=dict, description="Strength by subject")
    subject_improvement_potential: Dict[str, float] = Field(default_factory=dict, description="Improvement potential by subject")
    
    # Predictions and recommendations
    exam_readiness_score: float = Field(..., ge=0.0, le=1.0, description="Overall exam readiness")
    predicted_exam_performance: Dict[str, float] = Field(default_factory=dict, description="Predicted scores by subject")
    focus_recommendations: List[str] = Field(default_factory=list, description="What student should focus on")
    study_strategy_recommendations: List[str] = Field(default_factory=list, description="Recommended study strategies")
    
    # Risk factors
    dropout_risk: float = Field(..., ge=0.0, le=1.0, description="Risk of student dropping out")
    burnout_indicators: List[str] = Field(default_factory=list, description="Signs of potential burnout")
    intervention_recommendations: List[InterventionData] = Field(default_factory=list, description="Recommended interventions")

class SystemAnalyticsRequest(BaseModel):
    """Request for system-wide analytics"""
    time_window_days: int = Field(7, description="Analysis window in days")
    include_concept_breakdown: bool = Field(True, description="Include per-concept analysis")
    include_performance_distribution: bool = Field(True, description="Include student performance distribution")
    include_accuracy_trends: bool = Field(True, description="Include prediction accuracy trends")
    segment_by_exam_type: bool = Field(False, description="Segment results by exam type")

class SystemAnalyticsResponse(BaseModel):
    """System-wide analytics and insights"""
    # Overview metrics
    system_overview: Dict[str, Union[int, float]] = Field(..., description="High-level system metrics")
    
    # Performance metrics
    overall_prediction_accuracy: float = Field(..., ge=0.0, le=1.0)
    concept_accuracies: Dict[str, float] = Field(default_factory=dict)
    accuracy_trend: List[Dict[str, float]] = Field(default_factory=list, description="Accuracy over time")
    
    # Student analytics
    performance_distribution: Dict[str, int] = Field(default_factory=dict)
    engagement_metrics: Dict[str, float] = Field(default_factory=dict)
    learning_velocity_distribution: Dict[str, int] = Field(default_factory=dict)
    
    # System health
    throughput_metrics: Dict[str, float] = Field(default_factory=dict, description="Requests per second, latency, etc.")
    model_stability_indicators: Dict[str, float] = Field(default_factory=dict)
    error_rates: Dict[str, float] = Field(default_factory=dict)
    
    # Business metrics
    retention_rates: Dict[str, float] = Field(default_factory=dict)
    improvement_rates: Dict[str, float] = Field(default_factory=dict)
    satisfaction_indicators: Dict[str, float] = Field(default_factory=dict)
    
    # Insights and recommendations
    system_health_score: float = Field(..., ge=0.0, le=1.0)
    key_insights: List[str] = Field(default_factory=list)
    optimization_recommendations: List[str] = Field(default_factory=list)
    scaling_recommendations: List[str] = Field(default_factory=list)

# Database schema models for persistence
class BKTInteractionRecord(BaseModel):
    """Database record for BKT interactions"""
    id: Optional[str] = Field(None, description="Unique record ID")
    timestamp: datetime = Field(default_factory=datetime.now)
    student_id: str
    concept_id: str
    question_id: Optional[str] = None
    is_correct: bool
    response_time_ms: Optional[int] = None
    
    # Context data as JSON
    question_metadata: Dict[str, Any] = Field(default_factory=dict)
    context_factors: Dict[str, Any] = Field(default_factory=dict)
    
    # BKT results
    previous_mastery: float
    new_mastery: float
    confidence_level: float
    parameters_used: Dict[str, float] = Field(default_factory=dict)
    
    # Advanced analytics
    cognitive_load_data: Dict[str, Any] = Field(default_factory=dict)
    transfer_updates: Dict[str, float] = Field(default_factory=dict)
    intervention_triggered: Optional[Dict[str, Any]] = None
    
    # System metadata
    model_version: str = "enhanced_v2"
    processing_time_ms: Optional[float] = None

class BKTEvaluationRecord(BaseModel):
    """Database record for BKT evaluation results"""
    id: Optional[str] = Field(None, description="Unique evaluation ID")
    evaluation_timestamp: datetime = Field(default_factory=datetime.now)
    evaluation_period_start: datetime
    evaluation_period_end: datetime
    
    # Filter criteria used
    concept_filter: Optional[str] = None
    student_filter: Optional[str] = None
    exam_type_filter: Optional[str] = None
    
    # Core metrics (matching proven system)
    next_step_auc: float
    next_step_accuracy: float
    brier_score: float
    calibration_error: float
    trajectory_validity: float
    
    # Additional metrics
    knowledge_retention_score: float
    transfer_learning_effectiveness: float
    overall_quality_score: float
    
    # Sample statistics
    total_interactions: int
    total_students: int
    total_concepts: int
    
    # Detailed results as JSON
    concept_breakdown: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    
    # System info
    model_version: str = "enhanced_v2"
    evaluation_duration_ms: float