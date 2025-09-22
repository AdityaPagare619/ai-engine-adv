-- V3__alter_metadata_cache.sql
-- Phase 2.1 Migration: Extend question_metadata_cache for generation pipeline

-- Add generation-specific columns to existing metadata cache
ALTER TABLE question_metadata_cache 
ADD COLUMN IF NOT EXISTS template_id UUID REFERENCES question_templates(template_id),
ADD COLUMN IF NOT EXISTS generation_log_id BIGINT REFERENCES question_generation_logs(id),
ADD COLUMN IF NOT EXISTS ai_generated BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS generation_method TEXT DEFAULT 'manual' CHECK (generation_method IN ('manual', 'template', 'ai_assisted')),
ADD COLUMN IF NOT EXISTS quality_assured BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS rag_verified BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN IF NOT EXISTS template_version INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS calibration_params JSONB DEFAULT '{}'::jsonb;

-- Update existing indexes and add new ones for generation queries
CREATE INDEX IF NOT EXISTS idx_question_metadata_cache_generation ON question_metadata_cache(
    ai_generated, quality_assured, generation_method, created_at DESC
);

CREATE INDEX IF NOT EXISTS idx_question_metadata_cache_template ON question_metadata_cache(
    template_id, template_version
) WHERE template_id IS NOT NULL;

-- GIN index for calibration parameters
CREATE INDEX IF NOT EXISTS idx_question_metadata_cache_calibration ON question_metadata_cache 
USING GIN (calibration_params) WHERE ai_generated = true;

-- Add constraint for AI-generated questions to have template_id
ALTER TABLE question_metadata_cache 
ADD CONSTRAINT chk_ai_generated_has_template 
CHECK (NOT ai_generated OR template_id IS NOT NULL);

-- Create view for generation quality monitoring
CREATE OR REPLACE VIEW question_quality_monitor AS
SELECT 
    qmc.question_id,
    qmc.topic_id,
    qmc.exam_type,
    qmc.subject,
    qmc.difficulty_level,
    qmc.ai_generated,
    qmc.quality_assured,
    qmc.rag_verified,
    qt.template_id,
    qt.base_difficulty,
    qt.validation_score as template_validation_score,
    qgl.final_quality_score,
    qgl.rag_alignment_score,
    qgl.total_pipeline_time_ms,
    qmc.created_at
FROM question_metadata_cache qmc
LEFT JOIN question_templates qt ON qmc.template_id = qt.template_id
LEFT JOIN question_generation_logs qgl ON qmc.generation_log_id = qgl.id
WHERE qmc.ai_generated = true;

-- Function to update quality assurance flags
CREATE OR REPLACE FUNCTION update_question_quality_flags(
    p_question_id TEXT,
    p_quality_assured BOOLEAN DEFAULT NULL,
    p_rag_verified BOOLEAN DEFAULT NULL
) RETURNS void AS $$
BEGIN
    UPDATE question_metadata_cache 
    SET 
        quality_assured = COALESCE(p_quality_assured, quality_assured),
        rag_verified = COALESCE(p_rag_verified, rag_verified),
        updated_at = NOW()
    WHERE question_id = p_question_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Question % not found in metadata cache', p_question_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically set quality_assured when rag_verified is true
CREATE OR REPLACE FUNCTION auto_quality_assurance()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.rag_verified = true AND OLD.rag_verified = false THEN
        NEW.quality_assured = true;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_quality_assurance
    BEFORE UPDATE ON question_metadata_cache
    FOR EACH ROW EXECUTE FUNCTION auto_quality_assurance();

-- Create aggregate statistics view for dashboard
CREATE OR REPLACE VIEW generation_stats_daily AS
SELECT 
    DATE(created_at) as generation_date,
    exam_type,
    subject,
    COUNT(*) as total_questions,
    COUNT(*) FILTER (WHERE ai_generated = true) as ai_generated_count,
    COUNT(*) FILTER (WHERE quality_assured = true) as quality_assured_count,
    COUNT(*) FILTER (WHERE rag_verified = true) as rag_verified_count,
    AVG(difficulty_level) as avg_difficulty,
    COUNT(DISTINCT template_id) as unique_templates_used
FROM question_metadata_cache 
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at), exam_type, subject
ORDER BY generation_date DESC, exam_type, subject;

COMMENT ON VIEW question_quality_monitor IS 'Real-time quality monitoring for AI-generated questions with template and RAG scores';
COMMENT ON VIEW generation_stats_daily IS 'Daily aggregated statistics for question generation performance and quality metrics';