-- V1__create_question_templates.sql
-- Phase 2.1 Migration: Create question templates table for JEE/NEET

CREATE TABLE IF NOT EXISTS question_templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id TEXT NOT NULL REFERENCES subject_registry(subject_id),
    exam_type TEXT NOT NULL CHECK (exam_type IN ('JEE_MAIN', 'JEE_ADVANCED', 'NEET', 'FOUNDATION')),
    subject TEXT NOT NULL CHECK (subject IN ('PHYSICS', 'CHEMISTRY', 'MATHEMATICS', 'BIOLOGY')),
    format TEXT NOT NULL CHECK (format IN ('MCQ', 'NUMERICAL', 'ASSERTION_REASON', 'PASSAGE', 'MATRIX_MATCH')),
    
    -- Template content and structure
    template_text TEXT NOT NULL,
    variable_slots JSONB NOT NULL DEFAULT '[]'::jsonb,
    options_template JSONB NULL, -- For MCQ templates
    
    -- Difficulty and complexity metadata
    base_difficulty NUMERIC(3,2) NOT NULL CHECK (base_difficulty BETWEEN 0.1 AND 1.0),
    bloom_level INTEGER NOT NULL CHECK (bloom_level BETWEEN 1 AND 6), -- Bloom's taxonomy
    concept_depth INTEGER NOT NULL CHECK (concept_depth BETWEEN 1 AND 5),
    
    -- Quality assurance fields
    validation_score NUMERIC(3,2) DEFAULT NULL CHECK (validation_score BETWEEN 0.0 AND 1.0),
    ambiguity_flag BOOLEAN DEFAULT FALSE,
    clarity_score NUMERIC(3,2) DEFAULT NULL CHECK (clarity_score BETWEEN 0.0 AND 1.0),
    
    -- Syllabus alignment
    chapter TEXT NOT NULL,
    sub_chapter TEXT,
    ncert_reference TEXT,
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    success_rate NUMERIC(4,3) DEFAULT NULL,
    avg_solve_time INTEGER DEFAULT NULL, -- seconds
    
    -- Metadata
    created_by_service TEXT DEFAULT 'question-gen' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    version INTEGER DEFAULT 1 NOT NULL
);

-- Indexes for performance optimization
CREATE INDEX idx_question_templates_topic_format ON question_templates(topic_id, format, exam_type);
CREATE INDEX idx_question_templates_subject_difficulty ON question_templates(subject, base_difficulty);
CREATE INDEX idx_question_templates_bloom_active ON question_templates(bloom_level, is_active);
CREATE INDEX idx_question_templates_usage ON question_templates(usage_count DESC, success_rate DESC);
CREATE INDEX idx_question_templates_validation ON question_templates(validation_score DESC, clarity_score DESC);

-- GIN index for variable_slots JSONB operations
CREATE INDEX idx_question_templates_variable_slots ON question_templates USING GIN (variable_slots);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_question_templates_modtime 
    BEFORE UPDATE ON question_templates 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- Sample template data for JEE Physics (Mechanics)
INSERT INTO question_templates (topic_id, exam_type, subject, format, template_text, variable_slots, base_difficulty, bloom_level, concept_depth, chapter, sub_chapter, ncert_reference) VALUES
('PHY_MECHANICS_KINEMATICS', 'JEE_MAIN', 'PHYSICS', 'MCQ', 
'A particle moves along a straight line with initial velocity {{v0}} m/s and acceleration {{a}} m/s². Find the velocity after {{t}} seconds.',
'[{"name": "v0", "type": "integer", "range": {"min": 0, "max": 20}}, {"name": "a", "type": "integer", "range": {"min": -5, "max": 10}}, {"name": "t", "type": "integer", "range": {"min": 1, "max": 10}}]'::jsonb,
0.3, 2, 2, 'Motion in Straight Line', 'Equations of Motion', 'Class 11 Chapter 3');

-- Sample for NEET Biology
INSERT INTO question_templates (topic_id, exam_type, subject, format, template_text, variable_slots, base_difficulty, bloom_level, concept_depth, chapter, sub_chapter, ncert_reference) VALUES
('BIO_RESPIRATION_AEROBIC', 'NEET', 'BIOLOGY', 'MCQ',
'During aerobic respiration, {{substrate}} is completely oxidized in the presence of oxygen. The net ATP yield per molecule of {{substrate}} in eukaryotic cells is approximately {{atp_count}}.',
'[{"name": "substrate", "type": "string", "options": ["glucose", "pyruvate", "acetyl-CoA"]}, {"name": "atp_count", "type": "integer", "range": {"min": 30, "max": 38}}]'::jsonb,
0.4, 3, 3, 'Respiration in Plants', 'Aerobic Respiration', 'Class 11 Chapter 14');

COMMENT ON TABLE question_templates IS 'Master template repository for AI question generation across JEE/NEET exams';
COMMENT ON COLUMN question_templates.variable_slots IS 'JSON specification of template variables with types, ranges, and constraints';
COMMENT ON COLUMN question_templates.validation_score IS 'RAG-computed alignment score with exemplar questions (0.0-1.0)';