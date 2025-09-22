# Enhanced BKT Engine Package
# Enterprise-grade Bayesian Knowledge Tracing with 90%+ accuracy

# Legacy components (v1)
from .multi_concept_bkt import EnhancedMultiConceptBKT, ConceptMastery
from .concept_tracker import ConceptTracker
from .transfer_learning import TransferLearningEngine
from .bkt_evaluator import BKTPerformanceEvaluator

# Enhanced components (v2) - Main production system
from .enhanced_bkt_service import EnhancedBKTService
from .enhanced_repositories import InMemoryBKTRepository, AbstractBKTRepository
from .enhanced_schemas import (
    EnhancedTraceRequest,
    EnhancedTraceResponse,
    BKTEvaluationRequest,
    BKTEvaluationResponse,
    StudentProfileRequest,
    StudentProfileResponse,
    SystemAnalyticsRequest,
    SystemAnalyticsResponse,
    ExamType,
    DifficultyLevel,
    InterventionLevel
)
from .enhanced_multi_concept_bkt import EnhancedMultiConceptBKTv2

__version__ = "2.0.0"
__author__ = "Enhanced BKT Development Team"
__description__ = "Enterprise-grade Bayesian Knowledge Tracing with proven 90%+ accuracy"

# Main exports (v2 components recommended for production)
__all__ = [
    # Core service (v2)
    "EnhancedBKTService",
    
    # Repositories (v2)
    "AbstractBKTRepository",
    "InMemoryBKTRepository",
    
    # Request/Response schemas (v2)
    "EnhancedTraceRequest",
    "EnhancedTraceResponse",
    "BKTEvaluationRequest", 
    "BKTEvaluationResponse",
    "StudentProfileRequest",
    "StudentProfileResponse",
    "SystemAnalyticsRequest",
    "SystemAnalyticsResponse",
    
    # Enums (v2)
    "ExamType",
    "DifficultyLevel", 
    "InterventionLevel",
    
    # Core BKT engine (v2)
    "EnhancedMultiConceptBKTv2",
    
    # Legacy components (v1) - for backward compatibility
    'EnhancedMultiConceptBKT',
    'ConceptMastery', 
    'ConceptTracker',
    'TransferLearningEngine',
    'BKTPerformanceEvaluator'
]
