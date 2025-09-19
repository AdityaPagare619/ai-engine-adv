-- Create question metadata cache in Supabase for fast BKT lookups
CREATE TABLE IF NOT EXISTS question_metadata_cache (
    question_id             VARCHAR(250) PRIMARY KEY,  -- Updated to match your constraint
    subject                 VARCHAR(20),
    topic                   TEXT,
    difficulty_calibrated   NUMERIC(5,3),
    bloom_level            VARCHAR(20),
    estimated_time_seconds  INTEGER,
    required_process_skills TEXT[],
    question_type          VARCHAR(30),  -- Updated to match your constraint
    last_synced            TIMESTAMPTZ DEFAULT NOW(),
    created_at             TIMESTAMPTZ DEFAULT NOW(),
    updated_at             TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX idx_question_cache_lookup ON question_metadata_cache(question_id);
CREATE INDEX idx_question_cache_difficulty ON question_metadata_cache(difficulty_calibrated);
CREATE INDEX idx_question_cache_topic ON question_metadata_cache(subject, topic);
