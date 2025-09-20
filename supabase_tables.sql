-- =============================================================================
-- JEE Smart AI Platform - Supabase BKT Tables Creation
-- =============================================================================
-- Copy and paste these commands into your Supabase SQL Editor to create tables

-- 1. BKT Parameters Table
-- Stores learning parameters for each concept
CREATE TABLE IF NOT EXISTS bkt_parameters (
    concept_id text PRIMARY KEY,
    learn_rate numeric NOT NULL DEFAULT 0.3 CHECK (learn_rate >= 0 AND learn_rate <= 1),
    slip_rate numeric NOT NULL DEFAULT 0.1 CHECK (slip_rate >= 0 AND slip_rate <= 1),
    guess_rate numeric NOT NULL DEFAULT 0.2 CHECK (guess_rate >= 0 AND guess_rate <= 1),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

-- Add RLS (Row Level Security) policies
ALTER TABLE bkt_parameters ENABLE ROW LEVEL SECURITY;

-- Create policy for service role access
CREATE POLICY "Service role can manage bkt_parameters" ON bkt_parameters
    FOR ALL USING (auth.role() = 'service_role');

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_bkt_parameters_concept_id ON bkt_parameters(concept_id);

-- 2. BKT Knowledge States Table
-- Tracks student mastery for each concept
CREATE TABLE IF NOT EXISTS bkt_knowledge_states (
    id bigserial PRIMARY KEY,
    student_id text NOT NULL,
    concept_id text NOT NULL,
    mastery_probability numeric NOT NULL DEFAULT 0.5 CHECK (mastery_probability >= 0 AND mastery_probability <= 1),
    practice_count integer NOT NULL DEFAULT 0 CHECK (practice_count >= 0),
    last_practiced timestamp with time zone,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    UNIQUE(student_id, concept_id)
);

-- Add RLS
ALTER TABLE bkt_knowledge_states ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Service role can manage bkt_knowledge_states" ON bkt_knowledge_states
    FOR ALL USING (auth.role() = 'service_role');

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_bkt_knowledge_states_student_concept ON bkt_knowledge_states(student_id, concept_id);
CREATE INDEX IF NOT EXISTS idx_bkt_knowledge_states_concept ON bkt_knowledge_states(concept_id);
CREATE INDEX IF NOT EXISTS idx_bkt_knowledge_states_last_practiced ON bkt_knowledge_states(last_practiced);

-- 3. BKT Update Logs Table
-- Logs all BKT parameter updates for analytics
CREATE TABLE IF NOT EXISTS bkt_update_logs (
    id bigserial PRIMARY KEY,
    student_id text NOT NULL,
    concept_id text NOT NULL,
    previous_mastery numeric CHECK (previous_mastery >= 0 AND previous_mastery <= 1),
    new_mastery numeric NOT NULL CHECK (new_mastery >= 0 AND new_mastery <= 1),
    is_correct boolean NOT NULL,
    response_time_ms integer CHECK (response_time_ms >= 0),
    question_id text,
    params_json jsonb,
    engine_version text DEFAULT 'v1.0',
    created_at timestamp with time zone DEFAULT now()
);

-- Add RLS
ALTER TABLE bkt_update_logs ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Service role can manage bkt_update_logs" ON bkt_update_logs
    FOR ALL USING (auth.role() = 'service_role');

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_bkt_update_logs_student_concept ON bkt_update_logs(student_id, concept_id);
CREATE INDEX IF NOT EXISTS idx_bkt_update_logs_created_at ON bkt_update_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_bkt_update_logs_question_id ON bkt_update_logs(question_id);

-- 4. Question Metadata Cache Table
-- Caches question metadata for fast access
CREATE TABLE IF NOT EXISTS question_metadata_cache (
    question_id text PRIMARY KEY,
    subject text,
    topic text,
    difficulty_calibrated numeric CHECK (difficulty_calibrated >= -3 AND difficulty_calibrated <= 3),
    bloom_level text CHECK (bloom_level IN ('Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create')),
    estimated_time_seconds integer CHECK (estimated_time_seconds > 0),
    required_process_skills text[],
    question_type text CHECK (question_type IN ('MCQ', 'Numerical', 'Subjective', 'Fill-in-blank')),
    marks numeric CHECK (marks > 0),
    status text DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'released', 'retired')),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

-- Add RLS
ALTER TABLE question_metadata_cache ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Service role can manage question_metadata_cache" ON question_metadata_cache
    FOR ALL USING (auth.role() = 'service_role');

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_question_metadata_cache_subject_topic ON question_metadata_cache(subject, topic);
CREATE INDEX IF NOT EXISTS idx_question_metadata_cache_difficulty ON question_metadata_cache(difficulty_calibrated);
CREATE INDEX IF NOT EXISTS idx_question_metadata_cache_bloom_level ON question_metadata_cache(bloom_level);
CREATE INDEX IF NOT EXISTS idx_question_metadata_cache_status ON question_metadata_cache(status);
CREATE INDEX IF NOT EXISTS idx_question_metadata_cache_skills ON question_metadata_cache USING GIN(required_process_skills);

-- 5. BKT Evaluation Windows Table
-- Tracks learning progress over time windows
CREATE TABLE IF NOT EXISTS bkt_evaluation_windows (
    id bigserial PRIMARY KEY,
    student_id text NOT NULL,
    concept_id text NOT NULL,
    window_start timestamp with time zone NOT NULL,
    window_end timestamp with time zone NOT NULL,
    mastery_gain numeric CHECK (mastery_gain >= -1 AND mastery_gain <= 1),
    questions_attempted integer DEFAULT 0 CHECK (questions_attempted >= 0),
    accuracy_rate numeric CHECK (accuracy_rate >= 0 AND accuracy_rate <= 1),
    created_at timestamp with time zone DEFAULT now(),
    CHECK (window_end > window_start)
);

-- Add RLS
ALTER TABLE bkt_evaluation_windows ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Service role can manage bkt_evaluation_windows" ON bkt_evaluation_windows
    FOR ALL USING (auth.role() = 'service_role');

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_bkt_evaluation_windows_student_concept ON bkt_evaluation_windows(student_id, concept_id);
CREATE INDEX IF NOT EXISTS idx_bkt_evaluation_windows_time_range ON bkt_evaluation_windows(window_start, window_end);

-- 6. BKT Selection Feedback Table
-- Tracks question selection algorithm performance
CREATE TABLE IF NOT EXISTS bkt_selection_feedback (
    id bigserial PRIMARY KEY,
    student_id text NOT NULL,
    question_id text NOT NULL,
    predicted_mastery numeric CHECK (predicted_mastery >= 0 AND predicted_mastery <= 1),
    actual_outcome boolean,
    confidence_score numeric CHECK (confidence_score >= 0 AND confidence_score <= 1),
    selection_algorithm text NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);

-- Add RLS
ALTER TABLE bkt_selection_feedback ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Service role can manage bkt_selection_feedback" ON bkt_selection_feedback
    FOR ALL USING (auth.role() = 'service_role');

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_bkt_selection_feedback_student ON bkt_selection_feedback(student_id);
CREATE INDEX IF NOT EXISTS idx_bkt_selection_feedback_question ON bkt_selection_feedback(question_id);
CREATE INDEX IF NOT EXISTS idx_bkt_selection_feedback_algorithm ON bkt_selection_feedback(selection_algorithm);

-- =============================================================================
-- Initial Data Seeding
-- =============================================================================

-- Insert initial BKT parameters
INSERT INTO bkt_parameters (concept_id, learn_rate, slip_rate, guess_rate) VALUES
    ('kinematics_basic', 0.25, 0.10, 0.20),
    ('thermodynamics_basic', 0.22, 0.12, 0.18),
    ('organic_chemistry_basic', 0.28, 0.08, 0.22),
    ('calculus_derivatives', 0.30, 0.09, 0.15),
    ('algebra_quadratics', 0.35, 0.07, 0.18)
ON CONFLICT (concept_id) DO UPDATE SET
    learn_rate = EXCLUDED.learn_rate,
    slip_rate = EXCLUDED.slip_rate,
    guess_rate = EXCLUDED.guess_rate,
    updated_at = now();

-- Insert sample question metadata
INSERT INTO question_metadata_cache (
    question_id, subject, topic, difficulty_calibrated, bloom_level,
    estimated_time_seconds, required_process_skills, question_type, marks, status
) VALUES
    ('PHY_MECH_0001', 'Physics', 'Kinematics', 1.2, 'Apply', 120, 
     ARRAY['kinematics', 'problem_solving'], 'MCQ', 4.0, 'released'),
    ('CHEM_ORG_0001', 'Chemistry', 'Organic Chemistry', 0.8, 'Understand', 90,
     ARRAY['organic_reactions', 'nomenclature'], 'MCQ', 4.0, 'released'),
    ('MATH_CALC_0001', 'Mathematics', 'Calculus', 1.5, 'Apply', 150,
     ARRAY['differentiation', 'problem_solving'], 'Numerical', 4.0, 'released')
ON CONFLICT (question_id) DO UPDATE SET
    subject = EXCLUDED.subject,
    topic = EXCLUDED.topic,
    difficulty_calibrated = EXCLUDED.difficulty_calibrated,
    bloom_level = EXCLUDED.bloom_level,
    estimated_time_seconds = EXCLUDED.estimated_time_seconds,
    required_process_skills = EXCLUDED.required_process_skills,
    question_type = EXCLUDED.question_type,
    marks = EXCLUDED.marks,
    status = EXCLUDED.status,
    updated_at = now();

-- =============================================================================
-- Verification Queries
-- =============================================================================

-- Verify all tables were created and seeded
SELECT 'bkt_parameters' AS table_name, COUNT(*) AS row_count FROM bkt_parameters
UNION ALL
SELECT 'question_metadata_cache', COUNT(*) FROM question_metadata_cache
UNION ALL
SELECT 'bkt_knowledge_states', COUNT(*) FROM bkt_knowledge_states
UNION ALL
SELECT 'bkt_update_logs', COUNT(*) FROM bkt_update_logs
UNION ALL
SELECT 'bkt_evaluation_windows', COUNT(*) FROM bkt_evaluation_windows
UNION ALL
SELECT 'bkt_selection_feedback', COUNT(*) FROM bkt_selection_feedback;

-- Test data integrity
SELECT 
    concept_id,
    learn_rate,
    slip_rate,
    guess_rate,
    created_at
FROM bkt_parameters
ORDER BY concept_id;