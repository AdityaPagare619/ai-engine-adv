-- =============================================================================
-- JEE Smart AI Platform - Enhanced Foundation Database Schema
-- Integrates with existing structure + new BKT & time context features
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================================================
-- ENHANCED EXAM REGISTRY TABLES (Compatible with existing)
-- =============================================================================

-- Enhanced Exam Registry
CREATE TABLE IF NOT EXISTS exam_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exam_id VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    exam_type VARCHAR(50) NOT NULL CHECK (exam_type IN ('JEE_MAIN', 'JEE_ADVANCED', 'NEET', 'BOARDS')),
    academic_year INTEGER NOT NULL,
    
    -- NEW: Exam scheduling fields
    exam_date DATE,
    registration_start DATE,
    registration_end DATE,
    
    created_by_admin VARCHAR(100) NOT NULL,
    admin_key_hash VARCHAR(500) NOT NULL DEFAULT 'default_hash',
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'ARCHIVED')),
    
    total_subjects INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 0,
    
    -- NEW: Enhanced metadata
    metadata JSONB DEFAULT '{}',
    time_context_config JSONB DEFAULT '{"phases_enabled": true, "countdown_enabled": true}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_exam_type_year UNIQUE(exam_type, academic_year),
    CONSTRAINT valid_academic_year CHECK (academic_year >= 2020 AND academic_year <= 2030),
    CONSTRAINT valid_exam_dates CHECK (exam_date >= registration_start)
);

-- Enhanced Subject Registry
CREATE TABLE IF NOT EXISTS subject_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id VARCHAR(150) UNIQUE NOT NULL,
    exam_id VARCHAR(100) NOT NULL,
    subject_code VARCHAR(10) NOT NULL,
    subject_name VARCHAR(100) NOT NULL,
    
    -- NEW: Subject-specific configuration
    total_concepts INTEGER DEFAULT 0,
    concept_hierarchy JSONB DEFAULT '{}',
    
    total_questions INTEGER DEFAULT 0,
    total_sheets INTEGER DEFAULT 0,
    folder_path VARCHAR(500),
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraint
    CONSTRAINT fk_subject_exam FOREIGN KEY (exam_id) REFERENCES exam_registry(exam_id) ON DELETE CASCADE,
    CONSTRAINT valid_subject_codes CHECK (subject_code IN ('PHY', 'CHE', 'MAT', 'BIO', 'ENG'))
);

-- =============================================================================
-- NEW: BKT ENGINE TABLES
-- =============================================================================

-- BKT Parameters per concept
CREATE TABLE IF NOT EXISTS bkt_parameters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    concept_id VARCHAR(200) NOT NULL,
    subject_id VARCHAR(150) NOT NULL,
    
    -- BKT parameters
    prior_knowledge DECIMAL(5,4) DEFAULT 0.3 CHECK (prior_knowledge BETWEEN 0 AND 1),
    learn_rate DECIMAL(5,4) DEFAULT 0.25 CHECK (learn_rate BETWEEN 0 AND 1),
    slip_rate DECIMAL(5,4) DEFAULT 0.1 CHECK (slip_rate BETWEEN 0 AND 1),
    guess_rate DECIMAL(5,4) DEFAULT 0.2 CHECK (guess_rate BETWEEN 0 AND 1),
    decay_rate DECIMAL(5,4) DEFAULT 0.05 CHECK (decay_rate BETWEEN 0 AND 1),
    
    -- Metadata
    calibration_data JSONB DEFAULT '{}',
    last_calibrated TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_bkt_subject FOREIGN KEY (subject_id) REFERENCES subject_registry(subject_id) ON DELETE CASCADE,
    CONSTRAINT unique_concept_subject UNIQUE(concept_id, subject_id)
);

-- Student Mastery States
CREATE TABLE IF NOT EXISTS student_mastery_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(100) NOT NULL,
    concept_id VARCHAR(200) NOT NULL,
    subject_id VARCHAR(150) NOT NULL,
    
    -- Current state
    mastery_probability DECIMAL(6,5) DEFAULT 0.3 CHECK (mastery_probability BETWEEN 0 AND 1),
    confidence_level DECIMAL(6,5) DEFAULT 0.5 CHECK (confidence_level BETWEEN 0 AND 1),
    practice_count INTEGER DEFAULT 0 CHECK (practice_count >= 0),
    
    -- Timestamps
    last_interaction TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_student_concept UNIQUE(student_id, concept_id, subject_id),
    CONSTRAINT fk_mastery_subject FOREIGN KEY (subject_id) REFERENCES subject_registry(subject_id) ON DELETE CASCADE
);

-- BKT Interaction Logs
CREATE TABLE IF NOT EXISTS bkt_interaction_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(100) NOT NULL,
    concept_id VARCHAR(200) NOT NULL,
    question_id VARCHAR(500),
    
    -- Response data
    is_correct BOOLEAN NOT NULL,
    response_time_ms INTEGER CHECK (response_time_ms >= 0),
    
    -- BKT state changes
    previous_mastery DECIMAL(6,5) CHECK (previous_mastery BETWEEN 0 AND 1),
    new_mastery DECIMAL(6,5) NOT NULL CHECK (new_mastery BETWEEN 0 AND 1),
    mastery_change DECIMAL(6,5) GENERATED ALWAYS AS (new_mastery - previous_mastery) STORED,
    
    -- Cognitive load data
    cognitive_load_total DECIMAL(5,3),
    overload_risk DECIMAL(5,4) CHECK (overload_risk BETWEEN 0 AND 1),
    
    -- Context
    interaction_context JSONB DEFAULT '{}',
    bkt_parameters_used JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- NEW: TIME CONTEXT TABLES
-- =============================================================================

-- Exam Schedules (for time context processing)
CREATE TABLE IF NOT EXISTS exam_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exam_id VARCHAR(100) NOT NULL,
    student_id VARCHAR(100),  -- NULL means applies to all students
    
    -- Key dates
    target_exam_date DATE NOT NULL,
    preparation_start_date DATE NOT NULL,
    
    -- Phase configurations
    foundation_phase_days INTEGER DEFAULT 90,
    building_phase_days INTEGER DEFAULT 60,  
    mastery_phase_days INTEGER DEFAULT 30,
    confidence_phase_days INTEGER DEFAULT 30,
    
    -- Study targets
    daily_study_hours DECIMAL(3,1) DEFAULT 6.0,
    phase_configs JSONB DEFAULT '{}',
    
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'COMPLETED', 'PAUSED')),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_schedule_exam FOREIGN KEY (exam_id) REFERENCES exam_registry(exam_id) ON DELETE CASCADE,
    CONSTRAINT valid_dates CHECK (target_exam_date > preparation_start_date)
);

-- Time Context Tracking
CREATE TABLE IF NOT EXISTS time_context_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id VARCHAR(100) NOT NULL,
    exam_id VARCHAR(100) NOT NULL,
    
    -- Context snapshot
    days_remaining INTEGER NOT NULL,
    current_phase VARCHAR(20) NOT NULL CHECK (current_phase IN ('foundation', 'building', 'mastery', 'confidence')),
    urgency_level VARCHAR(20) NOT NULL CHECK (urgency_level IN ('low', 'medium', 'high', 'critical')),
    
    -- Recommendations generated
    focus_recommendations TEXT[],
    daily_targets JSONB DEFAULT '{}',
    risk_assessment JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- CONCEPT RELATIONSHIPS (for transfer learning)
-- =============================================================================

CREATE TABLE IF NOT EXISTS concept_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_concept VARCHAR(200) NOT NULL,
    target_concept VARCHAR(200) NOT NULL,
    subject_id VARCHAR(150) NOT NULL,
    
    -- Relationship strength (0-1)
    transfer_strength DECIMAL(4,3) NOT NULL CHECK (transfer_strength BETWEEN 0 AND 1),
    relationship_type VARCHAR(50) DEFAULT 'prerequisite' CHECK (relationship_type IN ('prerequisite', 'related', 'builds_on', 'applies_to')),
    
    -- Metadata
    evidence_strength DECIMAL(4,3) DEFAULT 0.5,
    validated BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_rel_subject FOREIGN KEY (subject_id) REFERENCES subject_registry(subject_id) ON DELETE CASCADE,
    CONSTRAINT unique_concept_pair UNIQUE(source_concept, target_concept, subject_id)
);

-- =============================================================================
-- ENHANCED INDEXES FOR PERFORMANCE
-- =============================================================================

-- BKT Performance Indexes
CREATE INDEX IF NOT EXISTS idx_bkt_parameters_concept ON bkt_parameters(concept_id);
CREATE INDEX IF NOT EXISTS idx_bkt_parameters_subject ON bkt_parameters(subject_id);

CREATE INDEX IF NOT EXISTS idx_mastery_states_student ON student_mastery_states(student_id);
CREATE INDEX IF NOT EXISTS idx_mastery_states_concept ON student_mastery_states(concept_id);
CREATE INDEX IF NOT EXISTS idx_mastery_states_updated ON student_mastery_states(updated_at DESC);

-- Partitioned index for interaction logs (high volume)
CREATE INDEX IF NOT EXISTS idx_interaction_logs_student_time ON bkt_interaction_logs(student_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_interaction_logs_concept_time ON bkt_interaction_logs(concept_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_interaction_logs_performance ON bkt_interaction_logs(is_correct, mastery_change);

-- Time Context Indexes
CREATE INDEX IF NOT EXISTS idx_exam_schedules_student ON exam_schedules(student_id);
CREATE INDEX IF NOT EXISTS idx_exam_schedules_exam ON exam_schedules(exam_id);
CREATE INDEX IF NOT EXISTS idx_exam_schedules_date ON exam_schedules(target_exam_date);

CREATE INDEX IF NOT EXISTS idx_time_context_student_exam ON time_context_logs(student_id, exam_id);
CREATE INDEX IF NOT EXISTS idx_time_context_phase ON time_context_logs(current_phase, urgency_level);

-- Concept Relationships Indexes
CREATE INDEX IF NOT EXISTS idx_concept_rel_source ON concept_relationships(source_concept);
CREATE INDEX IF NOT EXISTS idx_concept_rel_target ON concept_relationships(target_concept);
CREATE INDEX IF NOT EXISTS idx_concept_rel_strength ON concept_relationships(transfer_strength DESC);

-- =============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =============================================================================

-- Update timestamp trigger (reuse existing function)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to new tables
CREATE TRIGGER update_bkt_parameters_updated_at BEFORE UPDATE ON bkt_parameters
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_student_mastery_states_updated_at BEFORE UPDATE ON student_mastery_states
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_exam_schedules_updated_at BEFORE UPDATE ON exam_schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_concept_relationships_updated_at BEFORE UPDATE ON concept_relationships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- INITIAL DATA SEEDING
-- =============================================================================

-- Insert default BKT parameters for common concepts
INSERT INTO bkt_parameters (concept_id, subject_id, prior_knowledge, learn_rate, slip_rate, guess_rate) VALUES
-- Physics concepts
('kinematics_1d', 'PHY', 0.3, 0.25, 0.1, 0.2),
('kinematics_2d', 'PHY', 0.25, 0.22, 0.12, 0.22),
('dynamics_newton_laws', 'PHY', 0.28, 0.24, 0.11, 0.21),
('energy_work_power', 'PHY', 0.26, 0.26, 0.09, 0.19),
('thermodynamics_first_law', 'PHY', 0.22, 0.20, 0.15, 0.25),

-- Chemistry concepts  
('atomic_structure', 'CHE', 0.35, 0.28, 0.08, 0.18),
('periodic_table', 'CHE', 0.40, 0.30, 0.07, 0.16),
('chemical_bonding', 'CHE', 0.25, 0.22, 0.12, 0.23),
('organic_reactions', 'CHE', 0.20, 0.18, 0.16, 0.28),

-- Mathematics concepts
('algebra_quadratics', 'MAT', 0.45, 0.35, 0.06, 0.15),
('calculus_derivatives', 'MAT', 0.30, 0.25, 0.10, 0.20),
('coordinate_geometry', 'MAT', 0.35, 0.28, 0.08, 0.18)

ON CONFLICT (concept_id, subject_id) DO UPDATE SET
    prior_knowledge = EXCLUDED.prior_knowledge,
    learn_rate = EXCLUDED.learn_rate,
    slip_rate = EXCLUDED.slip_rate,
    guess_rate = EXCLUDED.guess_rate,
    updated_at = CURRENT_TIMESTAMP;

-- Insert concept relationships for transfer learning
INSERT INTO concept_relationships (source_concept, target_concept, subject_id, transfer_strength, relationship_type) VALUES
-- Physics relationships
('kinematics_1d', 'kinematics_2d', 'PHY', 0.8, 'prerequisite'),
('kinematics_2d', 'dynamics_newton_laws', 'PHY', 0.7, 'prerequisite'),
('dynamics_newton_laws', 'energy_work_power', 'PHY', 0.6, 'related'),

-- Chemistry relationships
('atomic_structure', 'periodic_table', 'CHE', 0.9, 'prerequisite'),
('periodic_table', 'chemical_bonding', 'CHE', 0.8, 'prerequisite'),
('chemical_bonding', 'organic_reactions', 'CHE', 0.6, 'applies_to'),

-- Mathematics relationships
('algebra_quadratics', 'calculus_derivatives', 'MAT', 0.7, 'prerequisite'),
('algebra_quadratics', 'coordinate_geometry', 'MAT', 0.8, 'related')

ON CONFLICT (source_concept, target_concept, subject_id) DO UPDATE SET
    transfer_strength = EXCLUDED.transfer_strength,
    relationship_type = EXCLUDED.relationship_type,
    updated_at = CURRENT_TIMESTAMP;

-- =============================================================================
-- FUNCTIONS FOR BKT OPERATIONS
-- =============================================================================

-- Function to get student's current mastery level
CREATE OR REPLACE FUNCTION get_student_mastery(
    p_student_id VARCHAR(100),
    p_concept_id VARCHAR(200)
) RETURNS DECIMAL(6,5) AS $$
DECLARE
    mastery_level DECIMAL(6,5);
BEGIN
    SELECT mastery_probability INTO mastery_level
    FROM student_mastery_states
    WHERE student_id = p_student_id AND concept_id = p_concept_id;
    
    RETURN COALESCE(mastery_level, 0.3); -- Return default if not found
END;
$$ LANGUAGE plpgsql;

-- Function to update mastery after interaction
CREATE OR REPLACE FUNCTION update_student_mastery(
    p_student_id VARCHAR(100),
    p_concept_id VARCHAR(200),
    p_subject_id VARCHAR(150),
    p_new_mastery DECIMAL(6,5),
    p_confidence DECIMAL(6,5) DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO student_mastery_states (student_id, concept_id, subject_id, mastery_probability, confidence_level, practice_count)
    VALUES (p_student_id, p_concept_id, p_subject_id, p_new_mastery, COALESCE(p_confidence, 0.5), 1)
    ON CONFLICT (student_id, concept_id, subject_id) 
    DO UPDATE SET
        mastery_probability = p_new_mastery,
        confidence_level = COALESCE(p_confidence, student_mastery_states.confidence_level),
        practice_count = student_mastery_states.practice_count + 1,
        last_interaction = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PERFORMANCE MONITORING VIEWS
-- =============================================================================

-- View for BKT performance monitoring
CREATE OR REPLACE VIEW bkt_performance_summary AS
SELECT 
    concept_id,
    COUNT(DISTINCT student_id) as total_students,
    AVG(mastery_probability) as avg_mastery,
    COUNT(*) as total_interactions,
    AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) as accuracy_rate,
    AVG(mastery_change) as avg_mastery_gain,
    AVG(cognitive_load_total) as avg_cognitive_load
FROM bkt_interaction_logs bil
JOIN student_mastery_states sms ON bil.student_id = sms.student_id AND bil.concept_id = sms.concept_id
WHERE bil.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY concept_id
ORDER BY total_interactions DESC;

-- View for time context monitoring  
CREATE OR REPLACE VIEW time_context_summary AS
SELECT 
    current_phase,
    urgency_level,
    COUNT(DISTINCT student_id) as student_count,
    AVG(days_remaining) as avg_days_remaining,
    COUNT(*) as context_updates
FROM time_context_logs
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY current_phase, urgency_level
ORDER BY current_phase, urgency_level;

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Verify BKT tables
SELECT 'bkt_parameters' as table_name, COUNT(*) as rows FROM bkt_parameters
UNION ALL
SELECT 'student_mastery_states', COUNT(*) FROM student_mastery_states  
UNION ALL
SELECT 'bkt_interaction_logs', COUNT(*) FROM bkt_interaction_logs
UNION ALL
SELECT 'concept_relationships', COUNT(*) FROM concept_relationships;

-- Verify time context tables
SELECT 'exam_schedules' as table_name, COUNT(*) as rows FROM exam_schedules
UNION ALL  
SELECT 'time_context_logs', COUNT(*) FROM time_context_logs;

-- Test BKT functions
SELECT get_student_mastery('test_student', 'kinematics_1d') as test_mastery;