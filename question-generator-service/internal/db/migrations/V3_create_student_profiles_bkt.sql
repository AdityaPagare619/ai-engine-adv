-- V3__create_student_profiles_bkt.sql
-- Phase 2-3 Migration: Student profiles, BKT integration, and adaptive learning tables
-- Aligns with comprehensive PDF roadmap requirements

-- =======================================================================================
-- STUDENT PROFILE AND MODELING TABLES
-- =======================================================================================

-- Main student profiles table with comprehensive behavioral indicators
CREATE TABLE IF NOT EXISTS student_profiles (
    student_id TEXT PRIMARY KEY,
    
    -- Basic Demographics
    full_name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone_number TEXT,
    date_of_birth DATE,
    
    -- Academic Context
    current_class TEXT NOT NULL CHECK (current_class IN ('11th', '12th', 'Dropper')),
    target_exam_year INTEGER NOT NULL,
    target_exams TEXT[] DEFAULT ARRAY['JEE_MAIN'], -- Multiple exam targets
    preferred_subjects TEXT[] NOT NULL CHECK (preferred_subjects <@ ARRAY['PHYSICS', 'CHEMISTRY', 'MATHEMATICS', 'BIOLOGY']),
    
    -- Geographic and Cultural Context
    state TEXT,
    city TEXT,
    preferred_language TEXT DEFAULT 'ENGLISH' CHECK (preferred_language IN ('ENGLISH', 'HINDI', 'BENGALI', 'TAMIL', 'TELUGU', 'GUJARATI')),
    socioeconomic_indicator TEXT DEFAULT 'MEDIUM' CHECK (socioeconomic_indicator IN ('LOW', 'MEDIUM', 'HIGH')),
    
    -- Device and Connectivity Context
    primary_device TEXT DEFAULT 'MOBILE' CHECK (primary_device IN ('MOBILE', 'TABLET', 'DESKTOP')),
    avg_connection_speed_mbps NUMERIC(5,2) DEFAULT 10.0,
    offline_capability_needed BOOLEAN DEFAULT TRUE,
    
    -- Learning Style Indicators (Multi-dimensional)
    visual_learning_score NUMERIC(3,2) DEFAULT 0.5 CHECK (visual_learning_score BETWEEN 0.0 AND 1.0),
    auditory_learning_score NUMERIC(3,2) DEFAULT 0.5 CHECK (auditory_learning_score BETWEEN 0.0 AND 1.0),
    kinesthetic_learning_score NUMERIC(3,2) DEFAULT 0.5 CHECK (kinesthetic_learning_score BETWEEN 0.0 AND 1.0),
    reading_learning_score NUMERIC(3,2) DEFAULT 0.5 CHECK (reading_learning_score BETWEEN 0.0 AND 1.0),
    
    -- Behavioral Pattern Indicators (50+ as per PDF requirements)
    avg_session_duration_minutes INTEGER DEFAULT 45,
    preferred_study_hours TEXT[] DEFAULT ARRAY['18:00-20:00'], -- Evening default
    attention_span_minutes INTEGER DEFAULT 30,
    break_frequency_per_hour INTEGER DEFAULT 2,
    procrastination_tendency NUMERIC(3,2) DEFAULT 0.3 CHECK (procrastination_tendency BETWEEN 0.0 AND 1.0),
    
    -- Stress and Psychological Indicators
    stress_tolerance_level NUMERIC(3,2) DEFAULT 0.6 CHECK (stress_tolerance_level BETWEEN 0.0 AND 1.0),
    confidence_level NUMERIC(3,2) DEFAULT 0.5 CHECK (confidence_level BETWEEN 0.0 AND 1.0),
    motivation_level NUMERIC(3,2) DEFAULT 0.7 CHECK (motivation_level BETWEEN 0.0 AND 1.0),
    test_anxiety_score NUMERIC(3,2) DEFAULT 0.4 CHECK (test_anxiety_score BETWEEN 0.0 AND 1.0),
    
    -- Performance Patterns
    morning_performance_score NUMERIC(3,2) DEFAULT 0.6,
    afternoon_performance_score NUMERIC(3,2) DEFAULT 0.5,
    evening_performance_score NUMERIC(3,2) DEFAULT 0.7,
    peak_performance_hours TEXT[] DEFAULT ARRAY['19:00-21:00'],
    
    -- Adaptive Learning Parameters
    optimal_difficulty_progression NUMERIC(3,2) DEFAULT 0.15 CHECK (optimal_difficulty_progression BETWEEN 0.05 AND 0.3),
    question_spacing_preference_minutes INTEGER DEFAULT 5,
    hint_usage_frequency NUMERIC(3,2) DEFAULT 0.2,
    solution_viewing_frequency NUMERIC(3,2) DEFAULT 0.3,
    
    -- Engagement Indicators
    daily_target_questions INTEGER DEFAULT 50,
    weekly_target_hours INTEGER DEFAULT 25,
    gamification_responsiveness NUMERIC(3,2) DEFAULT 0.6,
    social_learning_preference BOOLEAN DEFAULT FALSE,
    
    -- System Usage Patterns
    mobile_usage_percentage NUMERIC(3,2) DEFAULT 0.8,
    offline_study_percentage NUMERIC(3,2) DEFAULT 0.3,
    video_content_preference NUMERIC(3,2) DEFAULT 0.6,
    text_content_preference NUMERIC(3,2) DEFAULT 0.4,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    profile_completion_percentage NUMERIC(3,2) DEFAULT 0.2,
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

-- =======================================================================================
-- BKT INTEGRATION AND KNOWLEDGE TRACING TABLES
-- =======================================================================================

-- Enhanced concept mastery tracking integrated with our Python BKT engine
CREATE TABLE IF NOT EXISTS student_concept_mastery (
    id BIGSERIAL PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES student_profiles(student_id) ON DELETE CASCADE,
    concept_id TEXT NOT NULL, -- Maps to our BKT engine concept IDs
    
    -- Core BKT Parameters (aligns with enhanced_multi_concept_bkt.py)
    mastery_level NUMERIC(6,4) NOT NULL DEFAULT 0.3 CHECK (mastery_level BETWEEN 0.0 AND 1.0),
    prior_knowledge NUMERIC(4,3) NOT NULL DEFAULT 0.30,
    learn_rate NUMERIC(4,3) NOT NULL DEFAULT 0.38,
    slip_rate NUMERIC(4,3) NOT NULL DEFAULT 0.11,
    guess_rate NUMERIC(4,3) NOT NULL DEFAULT 0.16,
    decay_rate NUMERIC(5,4) NOT NULL DEFAULT 0.018,
    
    -- Advanced BKT Features
    confidence_score NUMERIC(4,3) DEFAULT 0.5,
    learning_velocity NUMERIC(5,3) DEFAULT 1.0, -- Speed of learning
    knowledge_stability NUMERIC(4,3) DEFAULT 0.6, -- How stable the knowledge is
    last_decay_applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Performance Tracking
    total_attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    recent_performance NUMERIC(4,3) DEFAULT 0.5, -- Last 10 attempts
    streak_count INTEGER DEFAULT 0, -- Current streak (pos/neg)
    max_streak INTEGER DEFAULT 0,
    
    -- Time-based Analytics
    first_exposure_at TIMESTAMP WITH TIME ZONE,
    last_practice_at TIMESTAMP WITH TIME ZONE,
    total_practice_time_minutes INTEGER DEFAULT 0,
    avg_response_time_seconds NUMERIC(6,2) DEFAULT 30.0,
    
    -- Adaptive Parameters
    optimal_difficulty NUMERIC(3,2) DEFAULT 0.5,
    recovery_boost_active BOOLEAN DEFAULT FALSE,
    transfer_learning_boost NUMERIC(3,2) DEFAULT 0.0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    UNIQUE(student_id, concept_id)
);

-- Student interaction logs (detailed event tracking)
CREATE TABLE IF NOT EXISTS student_interactions (
    id BIGSERIAL PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES student_profiles(student_id) ON DELETE CASCADE,
    session_id UUID NOT NULL,
    
    -- Interaction Context
    interaction_type TEXT NOT NULL CHECK (interaction_type IN ('QUESTION_ATTEMPT', 'HINT_REQUEST', 'SOLUTION_VIEW', 'PRACTICE_START', 'PRACTICE_END', 'TEST_START', 'TEST_END')),
    concept_id TEXT,
    question_id TEXT,
    template_id UUID,
    
    -- Performance Data
    is_correct BOOLEAN,
    response_time_ms INTEGER,
    difficulty_level NUMERIC(3,2),
    confidence_reported NUMERIC(3,2), -- Self-reported confidence
    hint_used BOOLEAN DEFAULT FALSE,
    solution_viewed BOOLEAN DEFAULT FALSE,
    partial_credit NUMERIC(3,2) DEFAULT 0.0,
    
    -- Context Information
    device_type TEXT,
    connection_type TEXT, -- WIFI, 4G, 3G, 2G
    study_mode TEXT CHECK (study_mode IN ('PRACTICE', 'TEST', 'REVISION', 'CHALLENGE')),
    time_of_day TIME,
    day_of_week INTEGER CHECK (day_of_week BETWEEN 1 AND 7),
    
    -- Behavioral Indicators
    cursor_movements INTEGER DEFAULT 0, -- Mouse/touch tracking
    focus_changes INTEGER DEFAULT 0, -- Tab changes, focus loss
    idle_time_ms INTEGER DEFAULT 0,
    scroll_actions INTEGER DEFAULT 0,
    
    -- Stress Indicators
    response_pattern TEXT, -- RUSHED, NORMAL, CAREFUL, INDECISIVE
    error_correction_attempts INTEGER DEFAULT 0,
    backspace_count INTEGER DEFAULT 0,
    
    -- Metadata
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    ip_address INET,
    user_agent TEXT
);

-- =======================================================================================
-- ADVANCED ANALYTICS AND PERFORMANCE TRACKING
-- =======================================================================================

-- Student performance summary (materialized view for quick analytics)
CREATE MATERIALIZED VIEW student_performance_summary AS
SELECT 
    sp.student_id,
    sp.current_class,
    sp.target_exams,
    sp.preferred_subjects,
    
    -- Mastery Statistics
    COUNT(scm.concept_id) as total_concepts_encountered,
    AVG(scm.mastery_level) as overall_mastery_level,
    COUNT(scm.concept_id) FILTER (WHERE scm.mastery_level >= 0.8) as mastered_concepts,
    COUNT(scm.concept_id) FILTER (WHERE scm.mastery_level < 0.4) as weak_concepts,
    
    -- Performance Statistics
    COUNT(si.id) FILTER (WHERE si.interaction_type = 'QUESTION_ATTEMPT') as total_questions_attempted,
    COUNT(si.id) FILTER (WHERE si.interaction_type = 'QUESTION_ATTEMPT' AND si.is_correct = true) as correct_answers,
    AVG(si.response_time_ms) FILTER (WHERE si.interaction_type = 'QUESTION_ATTEMPT') as avg_response_time,
    AVG(si.difficulty_level) FILTER (WHERE si.interaction_type = 'QUESTION_ATTEMPT' AND si.is_correct = true) as avg_difficulty_correct,
    
    -- Engagement Statistics
    COUNT(DISTINCT si.session_id) as total_sessions,
    SUM(scm.total_practice_time_minutes) as total_study_time_minutes,
    AVG(si.confidence_reported) FILTER (WHERE si.confidence_reported IS NOT NULL) as avg_confidence,
    
    -- Recent Performance (Last 7 days)
    COUNT(si.id) FILTER (WHERE si.interaction_type = 'QUESTION_ATTEMPT' AND si.timestamp >= NOW() - INTERVAL '7 days') as questions_last_7_days,
    AVG(CASE WHEN si.is_correct THEN 1.0 ELSE 0.0 END) FILTER (WHERE si.interaction_type = 'QUESTION_ATTEMPT' AND si.timestamp >= NOW() - INTERVAL '7 days') as accuracy_last_7_days,
    
    -- Time-based Patterns
    sp.peak_performance_hours,
    sp.preferred_study_hours,
    sp.avg_session_duration_minutes,
    
    -- Last Activity
    sp.last_activity_at,
    MAX(si.timestamp) as last_interaction,
    
    -- Profile Completion
    sp.profile_completion_percentage
    
FROM student_profiles sp
LEFT JOIN student_concept_mastery scm ON sp.student_id = scm.student_id
LEFT JOIN student_interactions si ON sp.student_id = si.student_id
GROUP BY sp.student_id, sp.current_class, sp.target_exams, sp.preferred_subjects, 
         sp.peak_performance_hours, sp.preferred_study_hours, sp.avg_session_duration_minutes,
         sp.last_activity_at, sp.profile_completion_percentage;

-- =======================================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- =======================================================================================

-- Student Profiles Indexes
CREATE INDEX idx_student_profiles_class_exam ON student_profiles(current_class, target_exam_year);
CREATE INDEX idx_student_profiles_subjects ON student_profiles USING GIN (preferred_subjects);
CREATE INDEX idx_student_profiles_location ON student_profiles(state, city);
CREATE INDEX idx_student_profiles_activity ON student_profiles(last_activity_at DESC, is_active);
CREATE INDEX idx_student_profiles_learning_style ON student_profiles(visual_learning_score, auditory_learning_score, kinesthetic_learning_score);

-- Concept Mastery Indexes
CREATE INDEX idx_concept_mastery_student_concept ON student_concept_mastery(student_id, concept_id);
CREATE INDEX idx_concept_mastery_level ON student_concept_mastery(mastery_level DESC);
CREATE INDEX idx_concept_mastery_recent ON student_concept_mastery(student_id, last_practice_at DESC);
CREATE INDEX idx_concept_mastery_performance ON student_concept_mastery(student_id, recent_performance DESC);
CREATE INDEX idx_concept_mastery_difficulty ON student_concept_mastery(optimal_difficulty, mastery_level);

-- Student Interactions Indexes (for high-volume queries)
CREATE INDEX idx_student_interactions_student_time ON student_interactions(student_id, timestamp DESC);
CREATE INDEX idx_student_interactions_concept ON student_interactions(concept_id, timestamp DESC);
CREATE INDEX idx_student_interactions_session ON student_interactions(session_id, timestamp);
CREATE INDEX idx_student_interactions_performance ON student_interactions(student_id, is_correct, difficulty_level);
CREATE INDEX idx_student_interactions_type_time ON student_interactions(interaction_type, timestamp DESC);

-- Composite indexes for common query patterns
CREATE INDEX idx_student_interactions_analytics ON student_interactions(student_id, interaction_type, timestamp DESC) 
    WHERE interaction_type = 'QUESTION_ATTEMPT';
CREATE INDEX idx_concept_mastery_weak_concepts ON student_concept_mastery(student_id, mastery_level) 
    WHERE mastery_level < 0.4;

-- Performance summary materialized view index
CREATE UNIQUE INDEX idx_student_perf_summary_student ON student_performance_summary(student_id);

-- =======================================================================================
-- TRIGGERS FOR DATA CONSISTENCY
-- =======================================================================================

-- Update timestamp triggers
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_student_profiles_modtime 
    BEFORE UPDATE ON student_profiles 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_concept_mastery_modtime 
    BEFORE UPDATE ON student_concept_mastery 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- Profile completion percentage calculation trigger
CREATE OR REPLACE FUNCTION calculate_profile_completion()
RETURNS TRIGGER AS $$
DECLARE
    completion_score NUMERIC := 0.0;
BEGIN
    -- Basic info (30%)
    IF NEW.full_name IS NOT NULL AND NEW.email IS NOT NULL THEN
        completion_score := completion_score + 0.30;
    END IF;
    
    -- Academic info (25%)
    IF NEW.current_class IS NOT NULL AND NEW.target_exam_year IS NOT NULL THEN
        completion_score := completion_score + 0.25;
    END IF;
    
    -- Learning preferences (20%)
    IF NEW.visual_learning_score != 0.5 OR NEW.auditory_learning_score != 0.5 THEN
        completion_score := completion_score + 0.20;
    END IF;
    
    -- Behavioral patterns (15%)
    IF NEW.avg_session_duration_minutes != 45 OR array_length(NEW.preferred_study_hours, 1) > 1 THEN
        completion_score := completion_score + 0.15;
    END IF;
    
    -- Location and context (10%)
    IF NEW.state IS NOT NULL AND NEW.city IS NOT NULL THEN
        completion_score := completion_score + 0.10;
    END IF;
    
    NEW.profile_completion_percentage := completion_score;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER calculate_student_profile_completion
    BEFORE INSERT OR UPDATE ON student_profiles
    FOR EACH ROW EXECUTE FUNCTION calculate_profile_completion();

-- Function to refresh performance summary (call via cron job)
CREATE OR REPLACE FUNCTION refresh_student_analytics()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY student_performance_summary;
END;
$$ LANGUAGE plpgsql;

-- =======================================================================================
-- SAMPLE DATA FOR TESTING
-- =======================================================================================

-- Insert sample student profiles for testing
INSERT INTO student_profiles (
    student_id, full_name, email, current_class, target_exam_year, 
    preferred_subjects, state, city, preferred_language
) VALUES 
('student_001', 'Aarav Sharma', 'aarav.sharma@example.com', '12th', 2025, 
 ARRAY['PHYSICS', 'CHEMISTRY', 'MATHEMATICS'], 'DELHI', 'New Delhi', 'HINDI'),
('student_002', 'Priya Patel', 'priya.patel@example.com', '11th', 2026, 
 ARRAY['PHYSICS', 'CHEMISTRY', 'BIOLOGY'], 'GUJARAT', 'Ahmedabad', 'GUJARATI'),
('student_003', 'Ravi Kumar', 'ravi.kumar@example.com', 'Dropper', 2025, 
 ARRAY['PHYSICS', 'CHEMISTRY', 'MATHEMATICS'], 'TAMIL NADU', 'Chennai', 'TAMIL');

-- Insert sample concept mastery data
INSERT INTO student_concept_mastery (
    student_id, concept_id, mastery_level, total_attempts, correct_attempts
) VALUES 
('student_001', 'PHY_MECHANICS_KINEMATICS', 0.75, 50, 38),
('student_001', 'PHY_MECHANICS_DYNAMICS', 0.45, 30, 12),
('student_002', 'BIO_CELL_STRUCTURE', 0.85, 25, 22),
('student_003', 'MATH_CALCULUS_LIMITS', 0.65, 40, 26);

-- Comments for documentation
COMMENT ON TABLE student_profiles IS 'Comprehensive student profiling with 50+ behavioral indicators as per Phase 3 PDF requirements';
COMMENT ON TABLE student_concept_mastery IS 'BKT integration table storing concept-level mastery data aligned with enhanced_multi_concept_bkt.py';
COMMENT ON TABLE student_interactions IS 'Detailed interaction logging for behavioral pattern analysis and adaptive learning';
COMMENT ON MATERIALIZED VIEW student_performance_summary IS 'Real-time analytics view for student performance dashboard and AI decision making';