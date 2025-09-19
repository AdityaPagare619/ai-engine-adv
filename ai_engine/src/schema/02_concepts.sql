-- Knowledge concept hierarchy
CREATE TABLE public.knowledge_concepts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    concept_code VARCHAR(100) UNIQUE NOT NULL,
    concept_name VARCHAR(255) NOT NULL,
    subject VARCHAR(50) NOT NULL,
    chapter VARCHAR(100),
    topic VARCHAR(100),
    subtopic VARCHAR(100),

    -- Concept properties
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
    bloom_taxonomy VARCHAR(20) CHECK (bloom_taxonomy IN ('remember', 'understand', 'apply', 'analyze', 'evaluate', 'create')),
    prerequisite_concepts UUID[] DEFAULT '{}',

    -- Graph relationships
    parent_concept_id UUID REFERENCES knowledge_concepts(id),
    concept_depth INTEGER DEFAULT 1,
    is_leaf_concept BOOLEAN DEFAULT TRUE,

    -- Metadata
    estimated_learning_time_minutes INTEGER,
    concept_metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Student knowledge states (core of the AI engine)
CREATE TABLE public.student_knowledge_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES student_profiles(id) ON DELETE CASCADE,
    concept_id UUID REFERENCES knowledge_concepts(id) ON DELETE CASCADE,

    -- BKT Parameters
    mastery_probability DECIMAL(6,5) CHECK (mastery_probability BETWEEN 0 AND 1),
    confidence_interval DECIMAL(6,5) DEFAULT 0.1,

    -- Learning dynamics
    learning_rate DECIMAL(6,5) DEFAULT 0.3,
    forgetting_rate DECIMAL(6,5) DEFAULT 0.1,
    slip_probability DECIMAL(6,5) DEFAULT 0.1,
    guess_probability DECIMAL(6,5) DEFAULT 0.2,

    -- Practice statistics
    practice_count INTEGER DEFAULT 0,
    correct_count INTEGER DEFAULT 0,
    total_time_spent_seconds INTEGER DEFAULT 0,

    -- Temporal tracking
    first_encounter_at TIMESTAMPTZ,
    last_practice_at TIMESTAMPTZ,
    last_correct_at TIMESTAMPTZ,
    last_incorrect_at TIMESTAMPTZ,

    -- Advanced features
    misconceptions JSONB DEFAULT '[]'::jsonb,
    learning_curve_params JSONB DEFAULT '{}'::jsonb,
    attention_patterns JSONB DEFAULT '{}'::jsonb,

    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure uniqueness and performance
    UNIQUE(student_id, concept_id)
);

-- Create indexes for performance
CREATE INDEX idx_knowledge_states_student_mastery
ON student_knowledge_states (student_id, mastery_probability DESC);

CREATE INDEX idx_knowledge_states_concept_performance
ON student_knowledge_states (concept_id, mastery_probability);

CREATE INDEX idx_knowledge_states_last_practice
ON student_knowledge_states (last_practice_at DESC) WHERE last_practice_at IS NOT NULL;
