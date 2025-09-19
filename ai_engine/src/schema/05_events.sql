-- System performance monitoring
CREATE TABLE public.ai_model_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,6) NOT NULL,

    -- Context
    evaluation_dataset VARCHAR(100),
    evaluation_period_start TIMESTAMPTZ,
    evaluation_period_end TIMESTAMPTZ,

    -- Metadata
    evaluation_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure efficient querying
    UNIQUE(model_name, model_version, metric_name, evaluation_period_start)
);

-- Real-time system events
CREATE TABLE public.system_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    event_source VARCHAR(50) NOT NULL, -- 'knowledge_tracer', 'recommender', 'predictor'
    event_target VARCHAR(50),

    -- Event data
    event_payload JSONB NOT NULL,
    event_timestamp TIMESTAMPTZ DEFAULT NOW(),

    -- Processing status
    processing_status VARCHAR(20) DEFAULT 'pending',
    processed_at TIMESTAMPTZ,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,

    -- Context
    student_context UUID REFERENCES student_profiles(id),
    session_context UUID REFERENCES learning_sessions(id),

    -- TTL for log cleanup
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '30 days')
);

-- Create partitioned table for events (daily partitions)
CREATE TABLE system_events_template (
    LIKE system_events INCLUDING ALL
) PARTITION BY RANGE (event_timestamp);
