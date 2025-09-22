-- V2__create_generation_logs.sql
-- Phase 2.1 Migration: Create question generation tracking and audit logs

CREATE TABLE IF NOT EXISTS question_generation_logs (
    id BIGSERIAL PRIMARY KEY,
    
    -- Request context
    student_id TEXT NOT NULL,
    session_id UUID DEFAULT gen_random_uuid(),
    request_id UUID DEFAULT gen_random_uuid(),
    
    -- Generation parameters
    topic_id TEXT NOT NULL,
    exam_type TEXT NOT NULL CHECK (exam_type IN ('JEE_MAIN', 'JEE_ADVANCED', 'NEET', 'FOUNDATION')),
    subject TEXT NOT NULL CHECK (subject IN ('PHYSICS', 'CHEMISTRY', 'MATHEMATICS', 'BIOLOGY')),
    format TEXT NOT NULL CHECK (format IN ('MCQ', 'NUMERICAL', 'ASSERTION_REASON', 'PASSAGE', 'MATRIX_MATCH')),
    
    -- Difficulty calibration
    requested_difficulty NUMERIC(3,2) NOT NULL CHECK (requested_difficulty BETWEEN 0.1 AND 1.0),
    calibrated_difficulty NUMERIC(3,2) NULL CHECK (calibrated_difficulty BETWEEN 0.1 AND 1.0),
    bkt_mastery_level NUMERIC(4,3) NULL CHECK (bkt_mastery_level BETWEEN 0.0 AND 1.0),
    
    -- Template and generation details
    template_id UUID REFERENCES question_templates(template_id),
    template_variables JSONB DEFAULT '{}'::jsonb,
    generated_question_text TEXT,
    generated_options JSONB NULL, -- For MCQ questions
    correct_answer TEXT,
    solution_steps JSONB NULL,
    
    -- Validation pipeline results
    grammar_score NUMERIC(3,2) NULL CHECK (grammar_score BETWEEN 0.0 AND 1.0),
    clarity_score NUMERIC(3,2) NULL CHECK (clarity_score BETWEEN 0.0 AND 1.0),
    ambiguity_score NUMERIC(3,2) NULL CHECK (ambiguity_score BETWEEN 0.0 AND 1.0),
    validator_feedback TEXT NULL,
    
    -- RAG advisor results
    rag_alignment_score NUMERIC(3,2) NULL CHECK (rag_alignment_score BETWEEN 0.0 AND 1.0),
    rag_exemplar_ids TEXT[] NULL,
    rag_feedback TEXT NULL,
    regeneration_triggered BOOLEAN DEFAULT FALSE,
    regeneration_reason TEXT NULL,
    
    -- Performance metrics
    generation_time_ms INTEGER NOT NULL DEFAULT 0,
    calibration_time_ms INTEGER DEFAULT 0,
    validation_time_ms INTEGER DEFAULT 0,
    rag_time_ms INTEGER DEFAULT 0,
    total_pipeline_time_ms INTEGER NOT NULL DEFAULT 0,
    
    -- Quality flags
    validation_passed BOOLEAN DEFAULT FALSE NOT NULL,
    final_quality_score NUMERIC(3,2) NULL CHECK (final_quality_score BETWEEN 0.0 AND 1.0),
    
    -- Status tracking
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'GENERATED', 'VALIDATED', 'RAG_CHECKED', 'COMPLETED', 'FAILED', 'REGENERATED')),
    error_message TEXT NULL,
    retry_count INTEGER DEFAULT 0,
    
    -- Service metadata
    generator_version TEXT DEFAULT 'v1.0.0' NOT NULL,
    model_version TEXT DEFAULT 'template-v1' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Partitioning by month for performance with high volume
-- CREATE TABLE question_generation_logs_y2025m09 PARTITION OF question_generation_logs
--     FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');

-- Indexes for query performance
CREATE INDEX idx_generation_logs_student_date ON question_generation_logs(student_id, created_at DESC);
CREATE INDEX idx_generation_logs_topic_status ON question_generation_logs(topic_id, status, created_at DESC);
CREATE INDEX idx_generation_logs_template_performance ON question_generation_logs(template_id, validation_passed, final_quality_score DESC);
CREATE INDEX idx_generation_logs_difficulty_calibration ON question_generation_logs(requested_difficulty, calibrated_difficulty);
CREATE INDEX idx_generation_logs_performance_metrics ON question_generation_logs(total_pipeline_time_ms, generation_time_ms);
CREATE INDEX idx_generation_logs_rag_scores ON question_generation_logs(rag_alignment_score DESC, regeneration_triggered);

-- GIN index for JSONB operations
CREATE INDEX idx_generation_logs_template_vars ON question_generation_logs USING GIN (template_variables);

-- Materialized view for analytics dashboard
CREATE MATERIALIZED VIEW generation_performance_summary AS
SELECT 
    topic_id,
    exam_type,
    subject,
    format,
    COUNT(*) as total_generations,
    AVG(total_pipeline_time_ms) as avg_pipeline_time_ms,
    AVG(final_quality_score) as avg_quality_score,
    AVG(rag_alignment_score) as avg_rag_alignment,
    COUNT(*) FILTER (WHERE validation_passed = true) as successful_generations,
    COUNT(*) FILTER (WHERE regeneration_triggered = true) as regenerations,
    COUNT(*) FILTER (WHERE status = 'FAILED') as failed_generations,
    DATE_TRUNC('hour', created_at) as hour_bucket
FROM question_generation_logs 
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY topic_id, exam_type, subject, format, DATE_TRUNC('hour', created_at);

CREATE UNIQUE INDEX idx_gen_perf_summary ON generation_performance_summary(topic_id, exam_type, subject, format, hour_bucket);

-- Function to refresh analytics (call via cron job)
CREATE OR REPLACE FUNCTION refresh_generation_analytics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY generation_performance_summary;
END;
$$ LANGUAGE plpgsql;

-- Create index on frequently queried columns for reporting
CREATE INDEX idx_generation_logs_analytics ON question_generation_logs(
    exam_type, subject, format, validation_passed, created_at
) WHERE created_at >= NOW() - INTERVAL '7 days';

COMMENT ON TABLE question_generation_logs IS 'Comprehensive audit trail for every question generation request with performance metrics and quality scores';
COMMENT ON COLUMN question_generation_logs.rag_alignment_score IS 'RAG advisor computed alignment score with exemplar questions and rubrics';
COMMENT ON COLUMN question_generation_logs.regeneration_triggered IS 'Whether RAG advisor triggered regeneration due to low alignment score';
COMMENT ON MATERIALIZED VIEW generation_performance_summary IS 'Hourly aggregated performance metrics for monitoring dashboard';