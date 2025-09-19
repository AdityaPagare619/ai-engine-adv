-- High-level learning sessions
CREATE TABLE public.learning_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES student_profiles(id) ON DELETE CASCADE,
    session_type VARCHAR(20) CHECK (session_type IN ('drill', 'mock', 'revision', 'diagnostic', 'practice')),

    -- Session lifecycle
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    planned_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,

    -- Session context
    subject_focus VARCHAR(50),
    topics_covered TEXT[],
    difficulty_target DECIMAL(3,2),

    -- Performance metrics
    total_questions INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    skipped_questions INTEGER DEFAULT 0,
    time_per_question_avg DECIMAL(8,2),

    -- Technical context
    device_info JSONB DEFAULT '{}'::jsonb,
    ip_address INET,
    user_agent TEXT,
    browser_fingerprint VARCHAR(256),

    -- AI engine context
    ai_model_version VARCHAR(50),
    recommendation_strategy VARCHAR(50),
    adaptive_parameters JSONB DEFAULT '{}'::jsonb,

    -- Session outcomes
    session_quality_score DECIMAL(3,2), -- 0-1 based on engagement, accuracy, time management
    interruption_count INTEGER DEFAULT 0,
    focus_loss_events INTEGER DEFAULT 0,

    session_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Detailed question interactions within sessions
CREATE TABLE public.question_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES learning_sessions(id) ON DELETE CASCADE,
    student_id UUID REFERENCES student_profiles(id) ON DELETE CASCADE,

    -- Question context (references PostgreSQL question bank)
    question_id VARCHAR(50) NOT NULL, -- Links to Phase 1-3 PostgreSQL
    question_external_id VARCHAR(200), -- Full hierarchical ID from PostgreSQL
    interaction_sequence INTEGER NOT NULL, -- Order within session

    -- Timing data (high precision for behavioral analysis)
    question_shown_at TIMESTAMPTZ NOT NULL,
    first_interaction_at TIMESTAMPTZ,
    first_response_at TIMESTAMPTZ,
    final_response_at TIMESTAMPTZ,
    time_spent_milliseconds INTEGER,
    time_to_first_response_ms INTEGER,

    -- Response data
    selected_option INTEGER,
    response_confidence INTEGER CHECK (response_confidence BETWEEN 1 AND 5),
    is_correct BOOLEAN,
    correct_option INTEGER,

    -- Behavioral patterns
    answer_changes INTEGER DEFAULT 0,
    revisit_count INTEGER DEFAULT 0,
    hint_requests INTEGER DEFAULT 0,
    help_seeking_events INTEGER DEFAULT 0,

    -- Advanced interaction data
    keystroke_patterns JSONB DEFAULT '[]'::jsonb,
    mouse_movement_patterns JSONB DEFAULT '[]'::jsonb,
    scroll_behavior JSONB DEFAULT '[]'::jsonb,
    focus_events JSONB DEFAULT '[]'::jsonb,

    -- Content interaction
    diagram_interactions JSONB DEFAULT '[]'::jsonb, -- Zoom, pan, hover events
    text_selection_events JSONB DEFAULT '[]'::jsonb,
    formula_interaction_events JSONB DEFAULT '[]'::jsonb,

    -- AI model predictions and features
    predicted_correctness DECIMAL(5,4),
    predicted_difficulty DECIMAL(5,4),
    knowledge_state_before JSONB,
    knowledge_state_after JSONB,

    -- Quality assurance
    interaction_quality_flags JSONB DEFAULT '[]'::jsonb, -- Potential cheating, unusual patterns
    data_completeness_score DECIMAL(3,2) DEFAULT 1.0,

    interaction_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Partitioning for performance (monthly partitions)
CREATE TABLE question_interactions_template (
    LIKE question_interactions INCLUDING ALL
) PARTITION BY RANGE (question_shown_at);

-- Performance indexes
CREATE INDEX idx_interactions_student_session
ON question_interactions (student_id, session_id, interaction_sequence);

CREATE INDEX idx_interactions_question_performance
ON question_interactions (question_id, is_correct, time_spent_milliseconds);

CREATE INDEX idx_interactions_temporal
ON question_interactions (question_shown_at DESC);
