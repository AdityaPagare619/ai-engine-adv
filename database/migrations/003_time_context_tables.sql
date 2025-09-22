-- Time Context Tables for Exam Countdown Intelligence
-- Phase 1 Implementation - Time-aware Exam Preparation
-- Created: 2025-09-22

-- =====================================================
-- 1. Student Exam Timeline Table
-- =====================================================

CREATE TABLE IF NOT EXISTS student_exam_timeline (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) NOT NULL,
    exam_type VARCHAR(50) NOT NULL, -- 'JEE_MAIN', 'JEE_ADVANCED', 'NEET', etc.
    exam_date DATE NOT NULL,
    registration_date DATE,
    target_score INTEGER,
    preparation_start_date DATE,
    
    -- Current Context
    days_remaining INTEGER GENERATED ALWAYS AS (exam_date - CURRENT_DATE) STORED,
    current_phase VARCHAR(20), -- 'foundation', 'building', 'mastery', 'confidence'
    urgency_level VARCHAR(20), -- 'low', 'medium', 'high', 'critical'
    
    -- Study Plan Configuration
    daily_study_hours DECIMAL(4,2) DEFAULT 6.0,
    preferred_study_sessions INTEGER DEFAULT 3,
    break_duration_minutes INTEGER DEFAULT 15,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_completed BOOLEAN DEFAULT FALSE,
    completion_date DATE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(student_id, exam_type, exam_date)
);

CREATE INDEX idx_student_exam_timeline_student ON student_exam_timeline(student_id);
CREATE INDEX idx_student_exam_timeline_exam_date ON student_exam_timeline(exam_date);
CREATE INDEX idx_student_exam_timeline_days_remaining ON student_exam_timeline(days_remaining);
CREATE INDEX idx_student_exam_timeline_phase ON student_exam_timeline(current_phase);
CREATE INDEX idx_student_exam_timeline_active ON student_exam_timeline(is_active);

-- =====================================================
-- 2. Phase-Based Study Targets Table
-- =====================================================

CREATE TABLE IF NOT EXISTS phase_study_targets (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) NOT NULL,
    exam_timeline_id INTEGER REFERENCES student_exam_timeline(id) ON DELETE CASCADE,
    phase VARCHAR(20) NOT NULL, -- 'foundation', 'building', 'mastery', 'confidence'
    
    -- Phase Duration
    phase_start_date DATE NOT NULL,
    phase_end_date DATE NOT NULL,
    total_days INTEGER GENERATED ALWAYS AS (phase_end_date - phase_start_date + 1) STORED,
    
    -- Weekly Targets
    new_concepts_per_week INTEGER DEFAULT 0,
    practice_problems_per_week INTEGER DEFAULT 0,
    revision_hours_per_week INTEGER DEFAULT 0,
    mock_tests_per_week INTEGER DEFAULT 0,
    
    -- Progress Tracking
    concepts_completed INTEGER DEFAULT 0,
    problems_solved INTEGER DEFAULT 0,
    revision_hours_completed DECIMAL(5,2) DEFAULT 0.00,
    mock_tests_completed INTEGER DEFAULT 0,
    
    -- Performance Metrics
    target_mastery_level DECIMAL(4,3) DEFAULT 0.600, -- 60% target mastery
    current_mastery_level DECIMAL(4,3) DEFAULT 0.000,
    mastery_gap DECIMAL(4,3) GENERATED ALWAYS AS (target_mastery_level - current_mastery_level) STORED,
    
    -- Status
    phase_status VARCHAR(20) DEFAULT 'not_started', -- 'not_started', 'in_progress', 'completed', 'extended'
    completion_percentage DECIMAL(5,2) DEFAULT 0.00,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(student_id, exam_timeline_id, phase)
);

CREATE INDEX idx_phase_targets_student ON phase_study_targets(student_id);
CREATE INDEX idx_phase_targets_timeline ON phase_study_targets(exam_timeline_id);
CREATE INDEX idx_phase_targets_phase ON phase_study_targets(phase);
CREATE INDEX idx_phase_targets_status ON phase_study_targets(phase_status);
CREATE INDEX idx_phase_targets_mastery_gap ON phase_study_targets(mastery_gap);

-- =====================================================
-- 3. Daily Study Schedules Table
-- =====================================================

CREATE TABLE IF NOT EXISTS daily_study_schedules (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) NOT NULL,
    exam_timeline_id INTEGER REFERENCES student_exam_timeline(id) ON DELETE CASCADE,
    schedule_date DATE NOT NULL,
    
    -- Schedule Configuration
    total_planned_hours DECIMAL(4,2) NOT NULL DEFAULT 6.0,
    morning_session_hours DECIMAL(4,2) DEFAULT 3.0,
    afternoon_session_hours DECIMAL(4,2) DEFAULT 2.5,
    evening_session_hours DECIMAL(4,2) DEFAULT 2.5,
    
    -- Session Focus Areas
    morning_focus VARCHAR(50), -- 'new_concepts', 'practice', 'revision'
    afternoon_focus VARCHAR(50) DEFAULT 'practice_problems',
    evening_focus VARCHAR(50) DEFAULT 'revision_and_weak_areas',
    
    -- Actual Completion
    actual_study_hours DECIMAL(4,2) DEFAULT 0.0,
    morning_completed_hours DECIMAL(4,2) DEFAULT 0.0,
    afternoon_completed_hours DECIMAL(4,2) DEFAULT 0.0,
    evening_completed_hours DECIMAL(4,2) DEFAULT 0.0,
    
    -- Performance Metrics
    concepts_learned INTEGER DEFAULT 0,
    problems_solved INTEGER DEFAULT 0,
    revision_topics INTEGER DEFAULT 0,
    breaks_taken INTEGER DEFAULT 0,
    
    -- Schedule Adherence
    adherence_percentage DECIMAL(5,2) GENERATED ALWAYS AS 
        (CASE WHEN total_planned_hours > 0 THEN (actual_study_hours / total_planned_hours * 100) ELSE 0 END) STORED,
    schedule_rating INTEGER CHECK (schedule_rating >= 1 AND schedule_rating <= 5), -- Self-assessment
    
    -- Notes and Adjustments
    daily_notes TEXT,
    adjustment_reason VARCHAR(200),
    energy_level VARCHAR(20), -- 'low', 'medium', 'high'
    stress_level VARCHAR(20), -- 'low', 'medium', 'high', 'very_high'
    
    -- Status
    schedule_status VARCHAR(20) DEFAULT 'planned', -- 'planned', 'in_progress', 'completed', 'skipped'
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(student_id, schedule_date)
);

CREATE INDEX idx_daily_schedules_student ON daily_study_schedules(student_id);
CREATE INDEX idx_daily_schedules_timeline ON daily_study_schedules(exam_timeline_id);
CREATE INDEX idx_daily_schedules_date ON daily_study_schedules(schedule_date);
CREATE INDEX idx_daily_schedules_status ON daily_study_schedules(schedule_status);
CREATE INDEX idx_daily_schedules_adherence ON daily_study_schedules(adherence_percentage);

-- =====================================================
-- 4. Study Milestones Table
-- =====================================================

CREATE TABLE IF NOT EXISTS study_milestones (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) NOT NULL,
    exam_timeline_id INTEGER REFERENCES student_exam_timeline(id) ON DELETE CASCADE,
    
    -- Milestone Definition
    milestone_name VARCHAR(200) NOT NULL,
    milestone_type VARCHAR(50) NOT NULL, -- 'syllabus_coverage', 'mastery_target', 'mock_test', 'revision_completion'
    target_date DATE NOT NULL,
    priority_level VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    
    -- Progress Tracking
    target_value DECIMAL(8,4), -- Flexible field for different milestone types
    current_value DECIMAL(8,4) DEFAULT 0.0000,
    completion_percentage DECIMAL(5,2) GENERATED ALWAYS AS 
        (CASE WHEN target_value > 0 THEN (current_value / target_value * 100) ELSE 0 END) STORED,
    
    -- Status
    milestone_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'overdue', 'skipped'
    completion_date DATE,
    days_overdue INTEGER GENERATED ALWAYS AS 
        (CASE WHEN milestone_status = 'overdue' THEN (CURRENT_DATE - target_date) ELSE 0 END) STORED,
    
    -- Performance Assessment
    quality_rating INTEGER CHECK (quality_rating >= 1 AND quality_rating <= 5),
    effort_rating INTEGER CHECK (effort_rating >= 1 AND effort_rating <= 5),
    satisfaction_rating INTEGER CHECK (satisfaction_rating >= 1 AND satisfaction_rating <= 5),
    
    -- Notes
    milestone_description TEXT,
    completion_notes TEXT,
    lessons_learned TEXT,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_milestones_student ON study_milestones(student_id);
CREATE INDEX idx_milestones_timeline ON study_milestones(exam_timeline_id);
CREATE INDEX idx_milestones_target_date ON study_milestones(target_date);
CREATE INDEX idx_milestones_status ON study_milestones(milestone_status);
CREATE INDEX idx_milestones_type ON study_milestones(milestone_type);
CREATE INDEX idx_milestones_priority ON study_milestones(priority_level);

-- =====================================================
-- 5. Time Context Recommendations Table
-- =====================================================

CREATE TABLE IF NOT EXISTS time_context_recommendations (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) NOT NULL,
    exam_timeline_id INTEGER REFERENCES student_exam_timeline(id) ON DELETE CASCADE,
    
    -- Recommendation Context
    recommendation_date DATE DEFAULT CURRENT_DATE,
    days_remaining_at_recommendation INTEGER NOT NULL,
    current_phase VARCHAR(20) NOT NULL,
    urgency_level VARCHAR(20) NOT NULL,
    
    -- Recommendation Details
    recommendation_type VARCHAR(50) NOT NULL, -- 'immediate_action', 'study_plan_adjustment', 'focus_shift', 'risk_mitigation'
    recommendation_title VARCHAR(200) NOT NULL,
    recommendation_description TEXT NOT NULL,
    priority_level VARCHAR(20) DEFAULT 'medium',
    
    -- Implementation
    action_items JSONB, -- Array of specific action items
    estimated_time_hours DECIMAL(4,2),
    difficulty_level VARCHAR(20) DEFAULT 'medium', -- 'easy', 'medium', 'hard'
    
    -- Status Tracking
    recommendation_status VARCHAR(20) DEFAULT 'new', -- 'new', 'acknowledged', 'in_progress', 'completed', 'dismissed'
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    dismissed_at TIMESTAMP WITH TIME ZONE,
    dismissal_reason VARCHAR(200),
    
    -- Effectiveness Tracking
    effectiveness_rating INTEGER CHECK (effectiveness_rating >= 1 AND effectiveness_rating <= 5),
    implementation_difficulty INTEGER CHECK (implementation_difficulty >= 1 AND implementation_difficulty <= 5),
    impact_on_performance DECIMAL(4,3) DEFAULT 0.000,
    
    -- AI Context
    generated_by_ai BOOLEAN DEFAULT TRUE,
    ai_confidence_score DECIMAL(4,3) DEFAULT 1.000,
    source_algorithm VARCHAR(50) DEFAULT 'time_context_processor',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_time_recommendations_student ON time_context_recommendations(student_id);
CREATE INDEX idx_time_recommendations_timeline ON time_context_recommendations(exam_timeline_id);
CREATE INDEX idx_time_recommendations_date ON time_context_recommendations(recommendation_date);
CREATE INDEX idx_time_recommendations_status ON time_context_recommendations(recommendation_status);
CREATE INDEX idx_time_recommendations_type ON time_context_recommendations(recommendation_type);
CREATE INDEX idx_time_recommendations_priority ON time_context_recommendations(priority_level);

-- =====================================================
-- 6. Exam Preparation Risk Assessment Table
-- =====================================================

CREATE TABLE IF NOT EXISTS exam_preparation_risk_assessment (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) NOT NULL,
    exam_timeline_id INTEGER REFERENCES student_exam_timeline(id) ON DELETE CASCADE,
    
    -- Assessment Context
    assessment_date DATE DEFAULT CURRENT_DATE,
    days_remaining INTEGER NOT NULL,
    current_phase VARCHAR(20) NOT NULL,
    
    -- Risk Factors
    overall_risk_level VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high', 'critical'
    mastery_gap_risk DECIMAL(4,3) DEFAULT 0.000,
    time_constraint_risk DECIMAL(4,3) DEFAULT 0.000,
    pace_consistency_risk DECIMAL(4,3) DEFAULT 0.000,
    weak_areas_risk DECIMAL(4,3) DEFAULT 0.000,
    
    -- Performance Indicators
    current_mastery_level DECIMAL(4,3) NOT NULL,
    required_mastery_level DECIMAL(4,3) NOT NULL,
    mastery_velocity DECIMAL(6,4) DEFAULT 0.0000, -- Mastery gain per day
    study_consistency_score DECIMAL(4,3) DEFAULT 1.000,
    
    -- Risk Mitigation
    recommended_actions JSONB, -- Array of risk mitigation actions
    intervention_urgency VARCHAR(20) DEFAULT 'none', -- 'none', 'low', 'medium', 'high', 'immediate'
    estimated_recovery_days INTEGER,
    success_probability DECIMAL(4,3) DEFAULT 0.500,
    
    -- Historical Tracking
    risk_trend VARCHAR(20) DEFAULT 'stable', -- 'improving', 'stable', 'declining'
    previous_risk_level VARCHAR(20),
    risk_change_factor DECIMAL(4,3) DEFAULT 0.000,
    
    -- Assessment Metadata
    assessment_algorithm VARCHAR(50) DEFAULT 'time_context_risk_assessor',
    confidence_score DECIMAL(4,3) DEFAULT 1.000,
    factors_considered JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_risk_assessment_student ON exam_preparation_risk_assessment(student_id);
CREATE INDEX idx_risk_assessment_timeline ON exam_preparation_risk_assessment(exam_timeline_id);
CREATE INDEX idx_risk_assessment_date ON exam_preparation_risk_assessment(assessment_date);
CREATE INDEX idx_risk_assessment_risk_level ON exam_preparation_risk_assessment(overall_risk_level);
CREATE INDEX idx_risk_assessment_intervention ON exam_preparation_risk_assessment(intervention_urgency);

-- =====================================================
-- 7. Functions and Triggers
-- =====================================================

-- Function to update phase based on days remaining
CREATE OR REPLACE FUNCTION update_exam_timeline_phase()
RETURNS TRIGGER AS $$
BEGIN
    -- Update current phase based on days remaining
    NEW.current_phase = CASE
        WHEN NEW.days_remaining > 90 THEN 'foundation'
        WHEN NEW.days_remaining > 60 THEN 'building'
        WHEN NEW.days_remaining > 30 THEN 'mastery'
        ELSE 'confidence'
    END;
    
    -- Update urgency level
    NEW.urgency_level = CASE
        WHEN NEW.days_remaining < 7 THEN 'critical'
        WHEN NEW.days_remaining < 30 THEN 'high'
        WHEN NEW.days_remaining < 90 THEN 'medium'
        ELSE 'low'
    END;
    
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for automatic phase updates
CREATE TRIGGER update_exam_timeline_phase_trigger
    BEFORE INSERT OR UPDATE ON student_exam_timeline
    FOR EACH ROW EXECUTE FUNCTION update_exam_timeline_phase();

-- Triggers for updated_at
CREATE TRIGGER update_phase_targets_updated_at 
    BEFORE UPDATE ON phase_study_targets 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_daily_schedules_updated_at 
    BEFORE UPDATE ON daily_study_schedules 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_milestones_updated_at 
    BEFORE UPDATE ON study_milestones 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recommendations_updated_at 
    BEFORE UPDATE ON time_context_recommendations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_risk_assessment_updated_at 
    BEFORE UPDATE ON exam_preparation_risk_assessment 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate study statistics
CREATE OR REPLACE FUNCTION calculate_study_statistics(student_id_param VARCHAR, days_count INTEGER DEFAULT 30)
RETURNS TABLE(
    total_planned_hours DECIMAL,
    total_actual_hours DECIMAL,
    average_adherence DECIMAL,
    study_consistency DECIMAL,
    concepts_learned_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        SUM(ds.total_planned_hours)::DECIMAL(8,2) as total_planned_hours,
        SUM(ds.actual_study_hours)::DECIMAL(8,2) as total_actual_hours,
        AVG(ds.adherence_percentage)::DECIMAL(5,2) as average_adherence,
        -- Consistency = (days with >80% adherence) / total days
        (COUNT(CASE WHEN ds.adherence_percentage > 80 THEN 1 END)::DECIMAL / COUNT(*)::DECIMAL)::DECIMAL(4,3) as study_consistency,
        SUM(ds.concepts_learned)::INTEGER as concepts_learned_count
    FROM daily_study_schedules ds
    WHERE ds.student_id = student_id_param 
        AND ds.schedule_date > (CURRENT_DATE - INTERVAL '1 day' * days_count)
        AND ds.schedule_status = 'completed';
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 8. Views for Common Queries
-- =====================================================

-- View for active exam timelines with current status
CREATE OR REPLACE VIEW active_exam_timelines AS
SELECT 
    et.id,
    et.student_id,
    et.exam_type,
    et.exam_date,
    et.days_remaining,
    et.current_phase,
    et.urgency_level,
    et.daily_study_hours,
    -- Recent study statistics
    COALESCE(ss.avg_adherence, 0) as recent_adherence_percentage,
    COALESCE(ss.concepts_learned, 0) as recent_concepts_learned,
    -- Risk assessment
    COALESCE(ra.overall_risk_level, 'unknown') as current_risk_level,
    COALESCE(ra.mastery_gap_risk, 0) as mastery_gap_risk,
    et.created_at,
    et.updated_at
FROM student_exam_timeline et
LEFT JOIN (
    SELECT 
        student_id,
        AVG(adherence_percentage) as avg_adherence,
        SUM(concepts_learned) as concepts_learned
    FROM daily_study_schedules 
    WHERE schedule_date > (CURRENT_DATE - INTERVAL '7 days')
        AND schedule_status = 'completed'
    GROUP BY student_id
) ss ON et.student_id = ss.student_id
LEFT JOIN (
    SELECT DISTINCT ON (student_id) 
        student_id,
        overall_risk_level,
        mastery_gap_risk
    FROM exam_preparation_risk_assessment
    ORDER BY student_id, assessment_date DESC
) ra ON et.student_id = ra.student_id
WHERE et.is_active = TRUE;

-- View for pending recommendations
CREATE OR REPLACE VIEW pending_recommendations AS
SELECT 
    r.id,
    r.student_id,
    r.recommendation_title,
    r.recommendation_description,
    r.priority_level,
    r.days_remaining_at_recommendation,
    r.current_phase,
    r.urgency_level,
    r.estimated_time_hours,
    r.recommendation_status,
    r.created_at,
    CURRENT_DATE - r.recommendation_date as days_since_recommendation
FROM time_context_recommendations r
WHERE r.recommendation_status IN ('new', 'acknowledged', 'in_progress')
ORDER BY r.priority_level DESC, r.created_at DESC;

-- View for milestone tracking
CREATE OR REPLACE VIEW milestone_tracking AS
SELECT 
    m.student_id,
    m.milestone_name,
    m.milestone_type,
    m.target_date,
    m.completion_percentage,
    m.milestone_status,
    m.priority_level,
    CASE 
        WHEN m.target_date < CURRENT_DATE AND m.milestone_status != 'completed' THEN 'overdue'
        WHEN m.target_date = CURRENT_DATE THEN 'due_today'
        WHEN m.target_date <= (CURRENT_DATE + INTERVAL '3 days') THEN 'due_soon'
        ELSE 'on_track'
    END as timeline_status,
    m.target_date - CURRENT_DATE as days_until_due
FROM study_milestones m
WHERE m.milestone_status != 'completed'
ORDER BY m.target_date ASC;

-- =====================================================
-- 9. Initial Data and Configuration
-- =====================================================

-- Insert default phase configurations (can be customized per student)
INSERT INTO phase_study_targets (student_id, exam_timeline_id, phase, phase_start_date, phase_end_date, 
                               new_concepts_per_week, practice_problems_per_week, revision_hours_per_week, mock_tests_per_week, target_mastery_level)
SELECT 
    'DEFAULT_CONFIG' as student_id,
    0 as exam_timeline_id,
    phase_name,
    CURRENT_DATE as phase_start_date,
    CURRENT_DATE as phase_end_date,
    concepts_per_week,
    problems_per_week,
    revision_hours,
    mock_tests,
    mastery_target
FROM (VALUES
    ('foundation', 15, 50, 10, 1, 0.400),
    ('building', 10, 80, 15, 2, 0.600),
    ('mastery', 5, 120, 20, 3, 0.800),
    ('confidence', 0, 150, 25, 4, 0.900)
) AS phase_configs(phase_name, concepts_per_week, problems_per_week, revision_hours, mock_tests, mastery_target)
ON CONFLICT (student_id, exam_timeline_id, phase) DO NOTHING;

-- =====================================================
-- 10. Comments and Documentation
-- =====================================================

COMMENT ON TABLE student_exam_timeline IS 'Core exam timeline and preparation tracking for students';
COMMENT ON TABLE phase_study_targets IS 'Phase-based study targets and progress tracking';
COMMENT ON TABLE daily_study_schedules IS 'Daily study schedules and adherence tracking';
COMMENT ON TABLE study_milestones IS 'Important milestones and deadlines in exam preparation';
COMMENT ON TABLE time_context_recommendations IS 'AI-generated recommendations based on time context';
COMMENT ON TABLE exam_preparation_risk_assessment IS 'Risk assessment for exam preparation success';

-- Migration completion
INSERT INTO schema_migrations (version, applied_at) VALUES ('003_time_context_tables', CURRENT_TIMESTAMP)
ON CONFLICT (version) DO NOTHING;