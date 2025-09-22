-- Enhanced BKT Integration Tables
-- Phase 1 Implementation - Multi-Concept BKT with Transfer Learning
-- Created: 2025-09-22

-- =====================================================
-- 1. Enhanced Concept Relationships Table
-- =====================================================

CREATE TABLE IF NOT EXISTS concept_relationships (
    id SERIAL PRIMARY KEY,
    source_concept_id VARCHAR(100) NOT NULL,
    target_concept_id VARCHAR(100) NOT NULL,
    relationship_type VARCHAR(50) NOT NULL, -- 'prerequisite', 'enables', 'related', 'cross_subject'
    strength DECIMAL(4,3) NOT NULL CHECK (strength >= 0 AND strength <= 1),
    subject_area VARCHAR(50) NOT NULL, -- 'physics', 'chemistry', 'mathematics'
    bidirectional BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_concept_id, target_concept_id, relationship_type)
);

CREATE INDEX idx_concept_relationships_source ON concept_relationships(source_concept_id);
CREATE INDEX idx_concept_relationships_target ON concept_relationships(target_concept_id);
CREATE INDEX idx_concept_relationships_type ON concept_relationships(relationship_type);
CREATE INDEX idx_concept_relationships_subject ON concept_relationships(subject_area);

-- =====================================================
-- 2. Enhanced Student Concept Mastery Table
-- =====================================================

CREATE TABLE IF NOT EXISTS student_concept_mastery_enhanced (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) NOT NULL,
    concept_id VARCHAR(100) NOT NULL,
    mastery_probability DECIMAL(6,4) NOT NULL DEFAULT 0.3000 CHECK (mastery_probability >= 0 AND mastery_probability <= 1),
    confidence_level DECIMAL(6,4) NOT NULL DEFAULT 0.5000 CHECK (confidence_level >= 0 AND confidence_level <= 1),
    practice_count INTEGER NOT NULL DEFAULT 0,
    last_interaction TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- BKT Parameters (student-specific)
    learning_rate DECIMAL(6,4) NOT NULL DEFAULT 0.2500,
    slip_rate DECIMAL(6,4) NOT NULL DEFAULT 0.1000,
    guess_rate DECIMAL(6,4) NOT NULL DEFAULT 0.2000,
    decay_rate DECIMAL(6,4) NOT NULL DEFAULT 0.0500,
    
    -- Transfer Learning Tracking
    total_transfer_boost DECIMAL(6,4) DEFAULT 0.0000,
    transfer_event_count INTEGER DEFAULT 0,
    
    -- Performance Metrics
    correct_responses INTEGER DEFAULT 0,
    total_responses INTEGER DEFAULT 0,
    average_response_time INTEGER DEFAULT 0, -- milliseconds
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(student_id, concept_id)
);

CREATE INDEX idx_student_mastery_student ON student_concept_mastery_enhanced(student_id);
CREATE INDEX idx_student_mastery_concept ON student_concept_mastery_enhanced(concept_id);
CREATE INDEX idx_student_mastery_last_interaction ON student_concept_mastery_enhanced(last_interaction);
CREATE INDEX idx_student_mastery_probability ON student_concept_mastery_enhanced(mastery_probability);

-- =====================================================
-- 3. Transfer Learning Events Table
-- =====================================================

CREATE TABLE IF NOT EXISTS transfer_learning_events (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) NOT NULL,
    source_concept_id VARCHAR(100) NOT NULL,
    target_concept_id VARCHAR(100) NOT NULL,
    transfer_type VARCHAR(50) NOT NULL, -- 'prerequisite', 'related', 'cross_subject', 'similarity', 'temporal'
    transfer_strength DECIMAL(6,4) NOT NULL,
    boost_amount DECIMAL(6,4) NOT NULL,
    trigger_mastery DECIMAL(6,4) NOT NULL,
    
    -- Context Information
    source_mastery_at_transfer DECIMAL(6,4),
    target_mastery_before DECIMAL(6,4),
    target_mastery_after DECIMAL(6,4),
    
    -- Timestamps
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transfer_events_student ON transfer_learning_events(student_id);
CREATE INDEX idx_transfer_events_source ON transfer_learning_events(source_concept_id);
CREATE INDEX idx_transfer_events_target ON transfer_learning_events(target_concept_id);
CREATE INDEX idx_transfer_events_type ON transfer_learning_events(transfer_type);
CREATE INDEX idx_transfer_events_timestamp ON transfer_learning_events(event_timestamp);

-- =====================================================
-- 4. BKT Interaction Logs Enhanced
-- =====================================================

CREATE TABLE IF NOT EXISTS bkt_interaction_logs_enhanced (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) NOT NULL,
    question_id VARCHAR(100),
    concept_id VARCHAR(100) NOT NULL,
    
    -- Response Data
    is_correct BOOLEAN NOT NULL,
    response_time_ms INTEGER NOT NULL DEFAULT 0,
    
    -- BKT State Changes
    mastery_before DECIMAL(6,4) NOT NULL,
    mastery_after DECIMAL(6,4) NOT NULL,
    mastery_change DECIMAL(6,4) NOT NULL,
    confidence_before DECIMAL(6,4),
    confidence_after DECIMAL(6,4),
    
    -- Cognitive Load Context
    cognitive_load DECIMAL(6,4),
    overload_risk DECIMAL(6,4),
    stress_level VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
    
    -- Transfer Learning
    transfer_boost_applied DECIMAL(6,4) DEFAULT 0.0000,
    transfer_sources JSONB, -- Array of transfer source information
    
    -- BKT Parameters Used
    learn_rate_used DECIMAL(6,4),
    slip_rate_used DECIMAL(6,4),
    guess_rate_used DECIMAL(6,4),
    
    -- Session Context
    session_id VARCHAR(100),
    question_difficulty DECIMAL(3,2),
    time_pressure_factor DECIMAL(3,2),
    
    -- Metadata
    interaction_metadata JSONB,
    
    -- Timestamps
    interaction_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bkt_logs_student ON bkt_interaction_logs_enhanced(student_id);
CREATE INDEX idx_bkt_logs_concept ON bkt_interaction_logs_enhanced(concept_id);
CREATE INDEX idx_bkt_logs_timestamp ON bkt_interaction_logs_enhanced(interaction_timestamp);
CREATE INDEX idx_bkt_logs_session ON bkt_interaction_logs_enhanced(session_id);
CREATE INDEX idx_bkt_logs_mastery_change ON bkt_interaction_logs_enhanced(mastery_change);

-- =====================================================
-- 5. Concept Difficulty Analysis Table
-- =====================================================

CREATE TABLE IF NOT EXISTS concept_difficulty_analysis (
    id SERIAL PRIMARY KEY,
    concept_id VARCHAR(100) NOT NULL UNIQUE,
    subject_area VARCHAR(50) NOT NULL,
    base_difficulty INTEGER NOT NULL CHECK (base_difficulty >= 1 AND base_difficulty <= 5),
    
    -- Complexity Factors
    prerequisite_complexity DECIMAL(4,2) DEFAULT 0.00,
    enabling_complexity DECIMAL(4,2) DEFAULT 0.00,
    relationship_complexity DECIMAL(4,2) DEFAULT 0.00,
    total_complexity DECIMAL(5,2) DEFAULT 0.00,
    
    -- Dynamic Difficulty (based on student performance)
    empirical_difficulty DECIMAL(6,4),
    success_rate DECIMAL(6,4),
    average_time_to_mastery INTEGER, -- in interactions
    
    -- Statistics
    total_students INTEGER DEFAULT 0,
    mastered_students INTEGER DEFAULT 0,
    average_mastery DECIMAL(6,4) DEFAULT 0.0000,
    
    -- Timestamps
    last_calculated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_concept_difficulty_concept ON concept_difficulty_analysis(concept_id);
CREATE INDEX idx_concept_difficulty_subject ON concept_difficulty_analysis(subject_area);
CREATE INDEX idx_concept_difficulty_base ON concept_difficulty_analysis(base_difficulty);
CREATE INDEX idx_concept_difficulty_empirical ON concept_difficulty_analysis(empirical_difficulty);

-- =====================================================
-- 6. BKT Performance Analytics Table
-- =====================================================

CREATE TABLE IF NOT EXISTS bkt_performance_analytics (
    id SERIAL PRIMARY KEY,
    analysis_period VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly'
    analysis_date DATE NOT NULL,
    
    -- Overall System Metrics
    total_interactions INTEGER DEFAULT 0,
    total_students INTEGER DEFAULT 0,
    total_concepts INTEGER DEFAULT 0,
    
    -- Accuracy Metrics
    overall_accuracy DECIMAL(6,4),
    precision_score DECIMAL(6,4),
    recall_score DECIMAL(6,4),
    f1_score DECIMAL(6,4),
    auc_roc DECIMAL(6,4),
    calibration_error DECIMAL(6,4),
    
    -- Transfer Learning Metrics
    transfer_events_count INTEGER DEFAULT 0,
    avg_transfer_boost DECIMAL(6,4),
    transfer_effectiveness DECIMAL(6,4),
    
    -- Learning Progress Metrics
    avg_mastery_gain DECIMAL(6,4),
    convergence_rate DECIMAL(6,4),
    plateau_detection_rate DECIMAL(6,4),
    
    -- System Health
    engine_health VARCHAR(20), -- 'excellent', 'good', 'fair', 'needs_attention'
    performance_grade VARCHAR(20), -- 'A', 'B', 'C', 'D', 'F'
    
    -- Detailed Analytics (JSON)
    subject_breakdown JSONB,
    concept_performance JSONB,
    student_distribution JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(analysis_period, analysis_date)
);

CREATE INDEX idx_bkt_analytics_period ON bkt_performance_analytics(analysis_period);
CREATE INDEX idx_bkt_analytics_date ON bkt_performance_analytics(analysis_date);
CREATE INDEX idx_bkt_analytics_health ON bkt_performance_analytics(engine_health);
CREATE INDEX idx_bkt_analytics_grade ON bkt_performance_analytics(performance_grade);

-- =====================================================
-- 7. Student Learning Patterns Table
-- =====================================================

CREATE TABLE IF NOT EXISTS student_learning_patterns (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) NOT NULL UNIQUE,
    
    -- Learning Characteristics
    learning_velocity DECIMAL(6,4) DEFAULT 0.0000,
    learning_style VARCHAR(50), -- 'visual', 'auditory', 'kinesthetic', 'mixed'
    plateau_tendency DECIMAL(6,4) DEFAULT 0.0000,
    transfer_learning_affinity DECIMAL(6,4) DEFAULT 0.0000,
    
    -- Cognitive Profile
    cognitive_load_tolerance DECIMAL(6,4) DEFAULT 1.0000,
    stress_resilience DECIMAL(6,4) DEFAULT 0.5000,
    attention_span_minutes INTEGER DEFAULT 45,
    
    -- Performance Patterns
    best_performance_time VARCHAR(20), -- 'morning', 'afternoon', 'evening'
    optimal_session_duration INTEGER DEFAULT 60, -- minutes
    break_frequency_preference INTEGER DEFAULT 20, -- minutes
    
    -- Subject Preferences
    strongest_subject VARCHAR(50),
    weakest_subject VARCHAR(50),
    preferred_difficulty_progression VARCHAR(20), -- 'gradual', 'mixed', 'challenge'
    
    -- Intervention Triggers
    intervention_needed BOOLEAN DEFAULT FALSE,
    intervention_type VARCHAR(50),
    last_intervention TIMESTAMP WITH TIME ZONE,
    
    -- Statistics
    total_study_time_minutes INTEGER DEFAULT 0,
    total_concepts_attempted INTEGER DEFAULT 0,
    total_concepts_mastered INTEGER DEFAULT 0,
    overall_progress_rate DECIMAL(6,4) DEFAULT 0.0000,
    
    -- Timestamps
    profile_created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_learning_patterns_student ON student_learning_patterns(student_id);
CREATE INDEX idx_learning_patterns_velocity ON student_learning_patterns(learning_velocity);
CREATE INDEX idx_learning_patterns_intervention ON student_learning_patterns(intervention_needed);
CREATE INDEX idx_learning_patterns_last_active ON student_learning_patterns(last_active);

-- =====================================================
-- 8. Functions and Triggers
-- =====================================================

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_concept_relationships_updated_at 
    BEFORE UPDATE ON concept_relationships 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_student_mastery_updated_at 
    BEFORE UPDATE ON student_concept_mastery_enhanced 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_concept_difficulty_updated_at 
    BEFORE UPDATE ON concept_difficulty_analysis 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_patterns_updated_at 
    BEFORE UPDATE ON student_learning_patterns 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate mastery statistics
CREATE OR REPLACE FUNCTION calculate_concept_statistics(concept_id_param VARCHAR)
RETURNS TABLE(
    concept_id VARCHAR,
    total_students INTEGER,
    mastered_students INTEGER,
    avg_mastery DECIMAL,
    success_rate DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        concept_id_param,
        COUNT(*)::INTEGER as total_students,
        COUNT(CASE WHEN mastery_probability > 0.8 THEN 1 END)::INTEGER as mastered_students,
        AVG(mastery_probability)::DECIMAL(6,4) as avg_mastery,
        CASE 
            WHEN COUNT(*) > 0 THEN (COUNT(CASE WHEN mastery_probability > 0.8 THEN 1 END)::DECIMAL / COUNT(*)::DECIMAL)::DECIMAL(6,4)
            ELSE 0.0000
        END as success_rate
    FROM student_concept_mastery_enhanced 
    WHERE student_concept_mastery_enhanced.concept_id = concept_id_param;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 9. Initial Data Population
-- =====================================================

-- Insert basic concept relationships (will be expanded by the Python initialization)
INSERT INTO concept_relationships (source_concept_id, target_concept_id, relationship_type, strength, subject_area) VALUES
-- Mathematics foundations
('basic_algebra', 'quadratic_equations', 'enables', 0.9, 'mathematics'),
('quadratic_equations', 'complex_numbers', 'enables', 0.7, 'mathematics'),
('coordinate_geometry', 'conic_sections', 'enables', 0.8, 'mathematics'),
('limits', 'derivatives', 'enables', 0.9, 'mathematics'),
('derivatives', 'integrals', 'enables', 0.7, 'mathematics'),

-- Physics foundations  
('kinematics', 'dynamics', 'enables', 0.9, 'physics'),
('dynamics', 'work_energy', 'enables', 0.8, 'physics'),
('electrostatics', 'current_electricity', 'enables', 0.7, 'physics'),

-- Chemistry foundations
('atomic_structure', 'periodic_table', 'enables', 0.9, 'chemistry'),
('periodic_table', 'chemical_bonding', 'enables', 0.8, 'chemistry'),
('chemical_bonding', 'organic_structure', 'enables', 0.8, 'chemistry'),

-- Cross-subject relationships
('calculus', 'kinematics', 'related', 0.4, 'mathematics'),
('vectors', 'electrostatics', 'related', 0.7, 'mathematics'),
('thermodynamics', 'thermochemistry', 'related', 0.8, 'physics'),
('atomic_physics', 'atomic_structure', 'related', 0.9, 'physics')
ON CONFLICT (source_concept_id, target_concept_id, relationship_type) DO NOTHING;

-- =====================================================
-- 10. Views for Common Queries
-- =====================================================

-- View for student mastery summary
CREATE OR REPLACE VIEW student_mastery_summary AS
SELECT 
    s.student_id,
    COUNT(s.concept_id) as total_concepts,
    AVG(s.mastery_probability) as overall_mastery,
    AVG(s.confidence_level) as overall_confidence,
    COUNT(CASE WHEN s.mastery_probability > 0.8 THEN 1 END) as mastered_concepts,
    COUNT(CASE WHEN s.mastery_probability < 0.4 THEN 1 END) as weak_concepts,
    SUM(s.practice_count) as total_practice_count,
    MAX(s.last_interaction) as last_activity
FROM student_concept_mastery_enhanced s
GROUP BY s.student_id;

-- View for concept performance overview
CREATE OR REPLACE VIEW concept_performance_overview AS
SELECT 
    c.concept_id,
    c.subject_area,
    c.base_difficulty,
    c.total_complexity,
    COUNT(s.student_id) as students_attempted,
    AVG(s.mastery_probability) as avg_mastery,
    COUNT(CASE WHEN s.mastery_probability > 0.8 THEN 1 END) as students_mastered,
    AVG(s.practice_count) as avg_practice_needed
FROM concept_difficulty_analysis c
LEFT JOIN student_concept_mastery_enhanced s ON c.concept_id = s.concept_id
GROUP BY c.concept_id, c.subject_area, c.base_difficulty, c.total_complexity;

-- View for recent transfer learning activity
CREATE OR REPLACE VIEW recent_transfer_activity AS
SELECT 
    t.student_id,
    t.target_concept_id,
    t.transfer_type,
    SUM(t.boost_amount) as total_boost,
    COUNT(*) as transfer_events,
    MAX(t.event_timestamp) as latest_transfer
FROM transfer_learning_events t
WHERE t.event_timestamp > (CURRENT_TIMESTAMP - INTERVAL '7 days')
GROUP BY t.student_id, t.target_concept_id, t.transfer_type
ORDER BY total_boost DESC;

-- =====================================================
-- 11. Comments and Documentation
-- =====================================================

COMMENT ON TABLE concept_relationships IS 'Stores relationships between concepts for transfer learning';
COMMENT ON TABLE student_concept_mastery_enhanced IS 'Enhanced student mastery tracking with BKT parameters';
COMMENT ON TABLE transfer_learning_events IS 'Logs all transfer learning events and their effectiveness';
COMMENT ON TABLE bkt_interaction_logs_enhanced IS 'Comprehensive logging of all BKT interactions';
COMMENT ON TABLE concept_difficulty_analysis IS 'Analysis and tracking of concept difficulty metrics';
COMMENT ON TABLE bkt_performance_analytics IS 'System-wide BKT performance analytics and monitoring';
COMMENT ON TABLE student_learning_patterns IS 'Individual student learning patterns and characteristics';

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO jee_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO jee_app_user;

-- Migration completion
INSERT INTO schema_migrations (version, applied_at) VALUES ('002_bkt_integration_tables', CURRENT_TIMESTAMP)
ON CONFLICT (version) DO NOTHING;