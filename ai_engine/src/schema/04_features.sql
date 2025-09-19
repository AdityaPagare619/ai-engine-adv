-- Feature store for ML models
CREATE TABLE public.student_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES student_profiles(id) ON DELETE CASCADE,

    -- Feature categories
    cognitive_features JSONB NOT NULL, -- Working memory, processing speed, etc.
    behavioral_features JSONB NOT NULL, -- Time patterns, consistency, engagement
    performance_features JSONB NOT NULL, -- Accuracy trends, improvement rates
    social_features JSONB DEFAULT '{}'::jsonb, -- Peer comparisons, collaborative patterns

    -- Feature metadata
    feature_version VARCHAR(20) NOT NULL,
    extraction_timestamp TIMESTAMPTZ DEFAULT NOW(),
    feature_quality_score DECIMAL(3,2) DEFAULT 1.0,

    -- Temporal features (for time-series analysis)
    temporal_window_start TIMESTAMPTZ,
    temporal_window_end TIMESTAMPTZ,

    -- Feature engineering metadata
    preprocessing_params JSONB DEFAULT '{}'::jsonb,
    feature_importance_scores JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ, -- For feature freshness management

    -- Ensure latest features per student
    UNIQUE(student_id, feature_version)
);

-- AI recommendations tracking
CREATE TABLE public.ai_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES student_profiles(id) ON DELETE CASCADE,
    session_id UUID REFERENCES learning_sessions(id),

    -- Recommendation context
    recommendation_type VARCHAR(50) NOT NULL, -- 'next_questions', 'study_plan', 'remediation'
    context_state JSONB NOT NULL, -- Student state at time of recommendation

    -- Recommendation content
    recommended_questions TEXT[] DEFAULT '{}', -- Question IDs from PostgreSQL
    recommended_topics TEXT[] DEFAULT '{}',
    recommended_difficulty_range NUMRANGE,

    -- Algorithm details
    algorithm_name VARCHAR(100) NOT NULL, -- 'contextual_bandit_v1', 'dkt_transformer_v2'
    algorithm_version VARCHAR(20) NOT NULL,
    model_parameters JSONB DEFAULT '{}'::jsonb,

    -- Recommendation scoring
    confidence_score DECIMAL(5,4),
    expected_learning_gain DECIMAL(5,4),
    diversity_score DECIMAL(5,4),
    novelty_score DECIMAL(5,4),

    -- Outcome tracking
    recommendation_shown BOOLEAN DEFAULT FALSE,
    recommendation_followed BOOLEAN DEFAULT FALSE,
    actual_performance DECIMAL(5,4), -- Filled after student completes recommended content
    recommendation_effectiveness DECIMAL(5,4), -- Calculated post-hoc

    -- A/B testing support
    experiment_group VARCHAR(50),
    control_group_flag BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '24 hours')
);

-- Performance predictions and forecasting
CREATE TABLE public.ai_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES student_profiles(id) ON DELETE CASCADE,

    -- Prediction metadata
    prediction_type VARCHAR(50) NOT NULL, -- 'exam_score', 'mastery_timeline', 'dropout_risk'
    prediction_horizon_days INTEGER NOT NULL,
    prediction_confidence DECIMAL(5,4),

    -- Prediction content
    predicted_score DECIMAL(6,2),
    score_confidence_interval JSONB, -- {"lower": 75.2, "upper": 85.8}
    predicted_percentile DECIMAL(5,2),

    -- Detailed predictions
    subject_wise_predictions JSONB DEFAULT '{}'::jsonb,
    concept_mastery_timeline JSONB DEFAULT '{}'::jsonb,
    improvement_trajectory JSONB DEFAULT '{}'::jsonb,

    -- Risk assessments
    dropout_risk_score DECIMAL(5,4),
    attention_deficit_risk DECIMAL(5,4),
    burnout_risk_score DECIMAL(5,4),

    -- Model information
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    ensemble_components JSONB DEFAULT '[]'::jsonb,
    feature_importance JSONB DEFAULT '{}'::jsonb,

    -- Validation and accuracy
    prediction_accuracy DECIMAL(5,4), -- Filled when ground truth becomes available
    calibration_error DECIMAL(5,4),

    -- Context
    prediction_context JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    validated_at TIMESTAMPTZ,

    -- Performance tracking
    CONSTRAINT valid_confidence CHECK (prediction_confidence BETWEEN 0 AND 1),
    CONSTRAINT valid_score CHECK (predicted_score BETWEEN 0 AND 300) -- JEE Main max score
);
