-- V4__create_rag_time_aware_system.sql  
-- Phase 2-3 Migration: RAG system integration and time-aware testing capabilities
-- Aligns with PDF roadmap for advanced question quality and strategic test planning

-- =======================================================================================
-- RAG SYSTEM INTEGRATION TABLES
-- =======================================================================================

-- RAG exemplar questions database (100K+ exemplars as per PDF)
CREATE TABLE IF NOT EXISTS rag_exemplar_questions (
    exemplar_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Question Content
    question_text TEXT NOT NULL,
    options JSONB NULL, -- For MCQ questions
    correct_answer TEXT NOT NULL,
    solution_steps JSONB NULL,
    explanation TEXT,
    
    -- Classification and Metadata
    subject TEXT NOT NULL CHECK (subject IN ('PHYSICS', 'CHEMISTRY', 'MATHEMATICS', 'BIOLOGY')),
    chapter TEXT NOT NULL,
    sub_chapter TEXT,
    concept_tags TEXT[] NOT NULL,
    
    -- Difficulty and Quality Metrics
    difficulty_level NUMERIC(3,2) NOT NULL CHECK (difficulty_level BETWEEN 0.0 AND 1.0),
    bloom_taxonomy_level INTEGER CHECK (bloom_taxonomy_level BETWEEN 1 AND 6),
    complexity_score NUMERIC(3,2) DEFAULT 0.5,
    
    -- Quality Assessment
    expert_validation_score NUMERIC(3,2) CHECK (expert_validation_score BETWEEN 0.0 AND 1.0),
    peer_review_score NUMERIC(3,2) CHECK (peer_review_score BETWEEN 0.0 AND 1.0),
    student_feedback_score NUMERIC(3,2) CHECK (student_feedback_score BETWEEN 0.0 AND 1.0),
    overall_quality_score NUMERIC(3,2) GENERATED ALWAYS AS (
        (COALESCE(expert_validation_score, 0.8) * 0.5 + 
         COALESCE(peer_review_score, 0.7) * 0.3 + 
         COALESCE(student_feedback_score, 0.6) * 0.2)
    ) STORED,
    
    -- Usage and Performance Tracking
    usage_count INTEGER DEFAULT 0,
    success_rate NUMERIC(4,3) DEFAULT NULL, -- Student success rate
    avg_solve_time_seconds INTEGER DEFAULT NULL,
    discrimination_index NUMERIC(4,3) DEFAULT NULL, -- Item analysis
    
    -- Vector Embeddings for Semantic Search
    question_embedding_vector VECTOR(384), -- Sentence transformer embeddings
    concept_embedding_vector VECTOR(384),
    
    -- Source Information
    source_type TEXT CHECK (source_type IN ('JEE_MAIN', 'JEE_ADVANCED', 'NEET', 'NCERT', 'MOCK_TEST', 'COACHING_MATERIAL')),
    source_year INTEGER,
    source_reference TEXT,
    
    -- Metadata
    created_by TEXT DEFAULT 'rag_system',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    quality_review_status TEXT DEFAULT 'PENDING' CHECK (quality_review_status IN ('PENDING', 'APPROVED', 'REJECTED', 'NEEDS_REVISION'))
);

-- RAG quality assessment logs (tracks AI quality decisions)
CREATE TABLE IF NOT EXISTS rag_quality_assessments (
    assessment_id BIGSERIAL PRIMARY KEY,
    question_id TEXT, -- From question generation logs
    template_id UUID, -- From templates table
    generated_question_text TEXT NOT NULL,
    
    -- RAG Assessment Results
    alignment_score NUMERIC(4,3) NOT NULL CHECK (alignment_score BETWEEN 0.0 AND 1.0),
    similar_exemplar_ids UUID[] NOT NULL, -- Array of matching exemplar IDs
    similarity_scores NUMERIC(4,3)[] NOT NULL, -- Corresponding similarity scores
    
    -- Quality Dimensions
    content_quality_score NUMERIC(4,3) DEFAULT NULL,
    difficulty_alignment_score NUMERIC(4,3) DEFAULT NULL,
    concept_coverage_score NUMERIC(4,3) DEFAULT NULL,
    language_quality_score NUMERIC(4,3) DEFAULT NULL,
    
    -- AI Assessment Details
    assessment_model_version TEXT DEFAULT 'rag_v1.0',
    processing_time_ms INTEGER NOT NULL,
    confidence_level NUMERIC(4,3) DEFAULT NULL,
    
    -- Recommendation
    quality_recommendation TEXT CHECK (quality_recommendation IN ('ACCEPT', 'REGENERATE', 'MANUAL_REVIEW')),
    improvement_suggestions TEXT[],
    
    -- Context
    student_id TEXT,
    exam_context JSONB, -- Target exam, subject, difficulty, etc.
    
    -- Metadata
    assessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Cross-reference table for exemplar-concept relationships
CREATE TABLE IF NOT EXISTS exemplar_concept_mappings (
    mapping_id BIGSERIAL PRIMARY KEY,
    exemplar_id UUID NOT NULL REFERENCES rag_exemplar_questions(exemplar_id) ON DELETE CASCADE,
    concept_id TEXT NOT NULL,
    
    -- Relationship Strength
    relevance_score NUMERIC(4,3) NOT NULL DEFAULT 1.0 CHECK (relevance_score BETWEEN 0.0 AND 1.0),
    is_primary_concept BOOLEAN DEFAULT TRUE,
    
    -- Transfer Learning Support
    prerequisite_concepts TEXT[],
    related_concepts TEXT[],
    difficulty_contribution NUMERIC(3,2) DEFAULT 0.0,
    
    UNIQUE(exemplar_id, concept_id)
);

-- =======================================================================================
-- TIME-AWARE SYSTEM TABLES
-- =======================================================================================

-- Exam calendar and timeline management
CREATE TABLE IF NOT EXISTS exam_calendar (
    calendar_id SERIAL PRIMARY KEY,
    exam_type TEXT NOT NULL CHECK (exam_type IN ('JEE_MAIN', 'JEE_ADVANCED', 'NEET')),
    exam_year INTEGER NOT NULL,
    session_name TEXT, -- 'January Session', 'April Session', etc.
    
    -- Important Dates
    registration_start_date DATE NOT NULL,
    registration_end_date DATE NOT NULL,
    exam_date DATE NOT NULL,
    result_declaration_date DATE,
    counselling_start_date DATE,
    
    -- Preparation Milestones
    syllabus_completion_target DATE, -- 80% syllabus target
    intensive_revision_start DATE,   -- Last 3 months
    mock_test_phase_start DATE,      -- Final 2 months
    confidence_building_start DATE,  -- Final month
    
    -- Metadata
    is_tentative BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    UNIQUE(exam_type, exam_year, session_name)
);

-- Strategic test planning and time-aware configurations
CREATE TABLE IF NOT EXISTS strategic_test_plans (
    plan_id BIGSERIAL PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES student_profiles(student_id) ON DELETE CASCADE,
    
    -- Target Context
    target_exam_type TEXT NOT NULL,
    target_exam_date DATE NOT NULL,
    current_preparation_phase TEXT NOT NULL CHECK (current_preparation_phase IN ('FOUNDATION', 'BUILDING', 'MASTERY', 'CONFIDENCE')),
    
    -- Strategic Configuration
    days_remaining INTEGER GENERATED ALWAYS AS (target_exam_date - CURRENT_DATE) STORED,
    weekly_test_frequency INTEGER NOT NULL DEFAULT 3,
    daily_question_target INTEGER NOT NULL DEFAULT 50,
    
    -- Subject-wise Time Allocation (percentages that sum to 100)
    physics_time_percentage NUMERIC(3,1) DEFAULT 33.3 CHECK (physics_time_percentage BETWEEN 0.0 AND 100.0),
    chemistry_time_percentage NUMERIC(3,1) DEFAULT 33.3 CHECK (chemistry_time_percentage BETWEEN 0.0 AND 100.0),
    mathematics_time_percentage NUMERIC(3,1) DEFAULT 33.3 CHECK (mathematics_time_percentage BETWEEN 0.0 AND 100.0),
    biology_time_percentage NUMERIC(3,1) DEFAULT 0.0 CHECK (biology_time_percentage BETWEEN 0.0 AND 100.0),
    
    -- Difficulty Progression Strategy
    confidence_builders_percentage NUMERIC(3,1) DEFAULT 60.0, -- Easy-medium questions
    skill_maintainers_percentage NUMERIC(3,1) DEFAULT 25.0,   -- Medium questions
    strategic_improvement_percentage NUMERIC(3,1) DEFAULT 15.0, -- Challenging questions
    
    -- Adaptive Parameters
    stress_management_focus BOOLEAN DEFAULT FALSE,
    speed_improvement_focus BOOLEAN DEFAULT FALSE,
    concept_strengthening_focus BOOLEAN DEFAULT TRUE,
    
    -- Progress Tracking
    plan_effectiveness_score NUMERIC(4,3) DEFAULT NULL,
    last_performance_review DATE DEFAULT CURRENT_DATE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    
    -- Constraint: time percentages should sum to 100 for active plans
    CONSTRAINT check_time_allocation CHECK (
        NOT is_active OR 
        (physics_time_percentage + chemistry_time_percentage + mathematics_time_percentage + biology_time_percentage = 100.0)
    )
);

-- Chapter coverage and sequencing for systematic preparation
CREATE TABLE IF NOT EXISTS chapter_coverage_tracking (
    tracking_id BIGSERIAL PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES student_profiles(student_id) ON DELETE CASCADE,
    subject TEXT NOT NULL CHECK (subject IN ('PHYSICS', 'CHEMISTRY', 'MATHEMATICS', 'BIOLOGY')),
    chapter_name TEXT NOT NULL,
    
    -- Coverage Status
    coverage_status TEXT NOT NULL DEFAULT 'NOT_STARTED' CHECK (coverage_status IN ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'REVISION_NEEDED', 'MASTERED')),
    coverage_percentage NUMERIC(3,1) DEFAULT 0.0 CHECK (coverage_percentage BETWEEN 0.0 AND 100.0),
    
    -- Time Tracking
    start_date DATE,
    target_completion_date DATE,
    actual_completion_date DATE,
    total_time_spent_hours NUMERIC(5,1) DEFAULT 0.0,
    
    -- Performance Metrics
    average_accuracy NUMERIC(4,3) DEFAULT NULL,
    questions_attempted INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    
    -- Difficulty Progression
    easy_questions_mastered INTEGER DEFAULT 0,
    medium_questions_mastered INTEGER DEFAULT 0,
    hard_questions_mastered INTEGER DEFAULT 0,
    
    -- Priority and Sequencing
    priority_level INTEGER DEFAULT 5 CHECK (priority_level BETWEEN 1 AND 10), -- 1 = highest priority
    prerequisite_chapters TEXT[], -- Chapters that should be completed first
    dependent_chapters TEXT[],    -- Chapters that depend on this one
    
    -- Strategic Importance
    exam_weightage_percentage NUMERIC(3,1) DEFAULT 5.0, -- Expected % of questions in exam
    student_strength_indicator NUMERIC(3,2) DEFAULT 0.5, -- How strong student is in this chapter
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    UNIQUE(student_id, subject, chapter_name)
);

-- Time-based performance analytics for strategic insights
CREATE TABLE IF NOT EXISTS time_based_performance (
    performance_id BIGSERIAL PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES student_profiles(student_id) ON DELETE CASCADE,
    
    -- Time Context
    analysis_date DATE NOT NULL DEFAULT CURRENT_DATE,
    time_period_type TEXT NOT NULL CHECK (time_period_type IN ('DAILY', 'WEEKLY', 'MONTHLY')),
    days_to_exam INTEGER, -- Calculated field
    
    -- Performance Metrics
    questions_attempted INTEGER DEFAULT 0,
    accuracy_percentage NUMERIC(4,2) DEFAULT 0.0,
    avg_time_per_question_seconds NUMERIC(6,2) DEFAULT 0.0,
    
    -- Subject-wise Breakdown
    physics_accuracy NUMERIC(4,2) DEFAULT NULL,
    chemistry_accuracy NUMERIC(4,2) DEFAULT NULL,
    mathematics_accuracy NUMERIC(4,2) DEFAULT NULL,
    biology_accuracy NUMERIC(4,2) DEFAULT NULL,
    
    -- Difficulty-wise Performance
    easy_questions_accuracy NUMERIC(4,2) DEFAULT NULL,
    medium_questions_accuracy NUMERIC(4,2) DEFAULT NULL,
    hard_questions_accuracy NUMERIC(4,2) DEFAULT NULL,
    
    -- Strategic Insights
    improvement_rate NUMERIC(5,3) DEFAULT 0.0, -- % improvement from previous period
    consistency_score NUMERIC(4,3) DEFAULT 0.5, -- How consistent performance is
    confidence_trend TEXT CHECK (confidence_trend IN ('INCREASING', 'STABLE', 'DECREASING')),
    
    -- Recommendations
    focus_areas TEXT[], -- Areas needing attention
    recommended_adjustments JSONB,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    UNIQUE(student_id, analysis_date, time_period_type)
);

-- =======================================================================================
-- CROSS-CHAPTER INTEGRATION AND TRANSFER LEARNING TABLES
-- =======================================================================================

-- Concept relationship mapping for transfer learning
CREATE TABLE IF NOT EXISTS concept_relationships (
    relationship_id BIGSERIAL PRIMARY KEY,
    source_concept_id TEXT NOT NULL,
    target_concept_id TEXT NOT NULL,
    
    -- Relationship Details
    relationship_type TEXT NOT NULL CHECK (relationship_type IN ('PREREQUISITE', 'BUILDS_ON', 'RELATED', 'APPLIES_TO', 'EXAMPLE_OF')),
    relationship_strength NUMERIC(4,3) NOT NULL DEFAULT 0.5 CHECK (relationship_strength BETWEEN 0.0 AND 1.0),
    
    -- Transfer Learning Parameters
    knowledge_transfer_coefficient NUMERIC(4,3) DEFAULT 0.1, -- How much mastery transfers
    difficulty_transfer_coefficient NUMERIC(4,3) DEFAULT 0.05, -- How difficulty understanding transfers
    
    -- Subject and Chapter Context
    source_subject TEXT NOT NULL,
    target_subject TEXT NOT NULL,
    cross_subject_relationship BOOLEAN GENERATED ALWAYS AS (source_subject != target_subject) STORED,
    
    -- Bidirectional indicator
    is_bidirectional BOOLEAN DEFAULT FALSE,
    
    -- Validation and Quality
    expert_verified BOOLEAN DEFAULT FALSE,
    usage_effectiveness_score NUMERIC(4,3) DEFAULT NULL,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    UNIQUE(source_concept_id, target_concept_id, relationship_type)
);

-- =======================================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- =======================================================================================

-- RAG Exemplar Questions Indexes
CREATE INDEX idx_rag_exemplars_subject_difficulty ON rag_exemplar_questions(subject, difficulty_level);
CREATE INDEX idx_rag_exemplars_quality ON rag_exemplar_questions(overall_quality_score DESC, is_active);
CREATE INDEX idx_rag_exemplars_usage ON rag_exemplar_questions(usage_count DESC, success_rate DESC);
CREATE INDEX idx_rag_exemplars_source ON rag_exemplar_questions(source_type, source_year);
CREATE INDEX idx_rag_exemplars_concepts ON rag_exemplar_questions USING GIN (concept_tags);

-- Vector similarity search indexes (for semantic search)
-- Note: Requires pgvector extension
-- CREATE INDEX idx_rag_exemplars_question_embedding ON rag_exemplar_questions USING ivfflat (question_embedding_vector vector_cosine_ops);
-- CREATE INDEX idx_rag_exemplars_concept_embedding ON rag_exemplar_questions USING ivfflat (concept_embedding_vector vector_cosine_ops);

-- RAG Quality Assessments Indexes
CREATE INDEX idx_rag_assessments_alignment ON rag_quality_assessments(alignment_score DESC, assessed_at DESC);
CREATE INDEX idx_rag_assessments_question ON rag_quality_assessments(question_id, assessed_at DESC);
CREATE INDEX idx_rag_assessments_student ON rag_quality_assessments(student_id, assessed_at DESC);

-- Time-Aware System Indexes
CREATE INDEX idx_exam_calendar_type_year ON exam_calendar(exam_type, exam_year);
CREATE INDEX idx_exam_calendar_dates ON exam_calendar(exam_date, registration_start_date);

CREATE INDEX idx_strategic_plans_student_active ON strategic_test_plans(student_id, is_active, target_exam_date);
CREATE INDEX idx_strategic_plans_phase ON strategic_test_plans(current_preparation_phase, days_remaining);

CREATE INDEX idx_chapter_coverage_student_subject ON chapter_coverage_tracking(student_id, subject, coverage_status);
CREATE INDEX idx_chapter_coverage_priority ON chapter_coverage_tracking(priority_level, coverage_percentage);
CREATE INDEX idx_chapter_coverage_timeline ON chapter_coverage_tracking(target_completion_date, coverage_status);

CREATE INDEX idx_time_performance_student_date ON time_based_performance(student_id, analysis_date DESC);
CREATE INDEX idx_time_performance_accuracy ON time_based_performance(accuracy_percentage DESC, days_to_exam);

-- Concept Relationships Indexes
CREATE INDEX idx_concept_relationships_source ON concept_relationships(source_concept_id, relationship_type);
CREATE INDEX idx_concept_relationships_target ON concept_relationships(target_concept_id, relationship_type);
CREATE INDEX idx_concept_relationships_cross_subject ON concept_relationships(cross_subject_relationship, relationship_strength DESC);

-- =======================================================================================
-- TRIGGERS AND FUNCTIONS
-- =======================================================================================

-- Update timestamp triggers
CREATE TRIGGER update_rag_exemplars_modtime 
    BEFORE UPDATE ON rag_exemplar_questions 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_exam_calendar_modtime 
    BEFORE UPDATE ON exam_calendar 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_strategic_plans_modtime 
    BEFORE UPDATE ON strategic_test_plans 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_chapter_coverage_modtime 
    BEFORE UPDATE ON chapter_coverage_tracking 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_concept_relationships_modtime 
    BEFORE UPDATE ON concept_relationships 
    FOR EACH ROW EXECUTE FUNCTION update_modified_column();

-- Function to calculate preparation phase based on days remaining
CREATE OR REPLACE FUNCTION determine_preparation_phase(days_remaining INTEGER)
RETURNS TEXT AS $$
BEGIN
    IF days_remaining > 180 THEN
        RETURN 'FOUNDATION';
    ELSIF days_remaining > 90 THEN
        RETURN 'BUILDING';
    ELSIF days_remaining > 30 THEN
        RETURN 'MASTERY';
    ELSE
        RETURN 'CONFIDENCE';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to update strategic test plans based on exam timeline
CREATE OR REPLACE FUNCTION update_strategic_test_phase()
RETURNS void AS $$
BEGIN
    UPDATE strategic_test_plans 
    SET current_preparation_phase = determine_preparation_phase(days_remaining)
    WHERE is_active = true AND 
          current_preparation_phase != determine_preparation_phase(days_remaining);
END;
$$ LANGUAGE plpgsql;

-- =======================================================================================
-- SAMPLE DATA FOR TESTING
-- =======================================================================================

-- Insert sample exam calendar data
INSERT INTO exam_calendar (exam_type, exam_year, session_name, registration_start_date, registration_end_date, exam_date) VALUES
('JEE_MAIN', 2025, 'January Session', '2024-11-01', '2024-11-30', '2025-01-24'),
('JEE_MAIN', 2025, 'April Session', '2025-02-01', '2025-02-28', '2025-04-04'),
('JEE_ADVANCED', 2025, 'Main Session', '2025-04-15', '2025-05-15', '2025-05-26'),
('NEET', 2025, 'Main Session', '2025-02-01', '2025-03-15', '2025-05-05');

-- Insert sample RAG exemplar questions
INSERT INTO rag_exemplar_questions (
    question_text, correct_answer, subject, chapter, concept_tags, 
    difficulty_level, source_type, source_year
) VALUES 
('A particle moves in a straight line with constant acceleration. If it covers 100m in the first 10s and 150m in the next 10s, find the acceleration.', 
 '2.5 m/s²', 'PHYSICS', 'Motion in Straight Line', 
 ARRAY['kinematics', 'constant_acceleration', 'equations_of_motion'], 
 0.4, 'JEE_MAIN', 2023),
 
('Calculate the molarity of a solution prepared by dissolving 40g of NaOH in 500ml of water.', 
 '2 M', 'CHEMISTRY', 'Solutions', 
 ARRAY['molarity', 'concentration', 'solutions'], 
 0.3, 'NEET', 2023),
 
('Find the derivative of f(x) = x³ + 2x² - 5x + 1.', 
 'f''(x) = 3x² + 4x - 5', 'MATHEMATICS', 'Differential Calculus', 
 ARRAY['derivatives', 'polynomial', 'calculus'], 
 0.35, 'JEE_MAIN', 2023);

-- Insert sample strategic test plans
INSERT INTO strategic_test_plans (
    student_id, target_exam_type, target_exam_date, current_preparation_phase
) VALUES 
('student_001', 'JEE_MAIN', '2025-01-24', 'CONFIDENCE'),
('student_002', 'NEET', '2025-05-05', 'BUILDING'),
('student_003', 'JEE_ADVANCED', '2025-05-26', 'MASTERY');

-- Insert sample concept relationships for transfer learning
INSERT INTO concept_relationships (
    source_concept_id, target_concept_id, relationship_type, 
    relationship_strength, source_subject, target_subject
) VALUES 
('PHY_MECHANICS_KINEMATICS', 'PHY_MECHANICS_DYNAMICS', 'PREREQUISITE', 0.8, 'PHYSICS', 'PHYSICS'),
('MATH_CALCULUS_LIMITS', 'PHY_MECHANICS_KINEMATICS', 'APPLIES_TO', 0.6, 'MATHEMATICS', 'PHYSICS'),
('CHEM_ATOMIC_STRUCTURE', 'CHEM_CHEMICAL_BONDING', 'BUILDS_ON', 0.9, 'CHEMISTRY', 'CHEMISTRY');

-- Comments for documentation
COMMENT ON TABLE rag_exemplar_questions IS 'Vector database with 100K+ exemplar questions for RAG-powered quality assessment as per Phase 2 PDF requirements';
COMMENT ON TABLE strategic_test_plans IS 'Time-aware strategic test planning system implementing Phase 3 preparation timeline intelligence';
COMMENT ON TABLE concept_relationships IS 'Cross-chapter integration and transfer learning support for advanced student profiling';
COMMENT ON TABLE time_based_performance IS 'Time-aware performance analytics for strategic exam preparation insights';