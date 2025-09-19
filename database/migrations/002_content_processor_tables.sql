-- =============================================================================
-- 002_content_processor_tables.sql
-- JEE Smart AI Platform – Content Processor Phase 2A Schema
-- =============================================================================

-- Enable extensions for advanced features
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Question Sheets Table (CSV import tracking)
CREATE TABLE IF NOT EXISTS question_sheets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sheet_id VARCHAR(200) UNIQUE NOT NULL,
    subject_id VARCHAR(150) DEFAULT 'SUBJECT_PENDING',
    sheet_name VARCHAR(200) NOT NULL,
    file_path VARCHAR(1000),
    version INTEGER DEFAULT 1,
    total_questions INTEGER DEFAULT 0,
    imported_questions INTEGER DEFAULT 0,
    failed_questions INTEGER DEFAULT 0,
    import_status VARCHAR(30) NOT NULL DEFAULT 'PENDING'
        CHECK(import_status IN ('PENDING','PROCESSING','COMPLETED','FAILED','PARTIAL')),
    file_checksum VARCHAR(128),
    last_imported_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Questions Table
CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id VARCHAR(250) UNIQUE NOT NULL,
    sheet_id VARCHAR(200) NOT NULL REFERENCES question_sheets(sheet_id) ON DELETE CASCADE,
    subject_id VARCHAR(150) DEFAULT 'SUBJECT_PENDING',
    question_number VARCHAR(20) NOT NULL,
    question_text TEXT,
    question_latex TEXT,
    question_type VARCHAR(30) DEFAULT 'MCQ'
        CHECK(question_type IN ('MCQ','NUMERICAL','ASSERTION_REASON','MATRIX_MATCH')),
    difficulty_level DECIMAL(3,2) DEFAULT 0.5
        CHECK(difficulty_level >= 0 AND difficulty_level <= 1),
    correct_option VARCHAR(10),
    numerical_answer DECIMAL(10,4),
    explanation TEXT,
    explanation_latex TEXT,
    has_images BOOLEAN DEFAULT FALSE,
    image_count INTEGER DEFAULT 0,
    topic_tags TEXT[],
    bloom_taxonomy VARCHAR(20),
    original_question_number VARCHAR(20),
    import_source VARCHAR(200),
    validation_status VARCHAR(20) DEFAULT 'PENDING'
        CHECK(validation_status IN ('PENDING','VALIDATED','REJECTED','NEEDS_REVIEW')),
    confidence_score DECIMAL(3,2) DEFAULT 0.8,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_question_per_sheet UNIQUE(sheet_id, question_number)
);

-- Question Options Table
CREATE TABLE IF NOT EXISTS question_options (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    option_id VARCHAR(300) UNIQUE NOT NULL,
    question_id VARCHAR(250) NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
    option_number INTEGER NOT NULL CHECK(option_number BETWEEN 1 AND 4),
    option_text TEXT,
    option_latex TEXT,
    is_correct BOOLEAN DEFAULT FALSE,
    has_image BOOLEAN DEFAULT FALSE,
    image_reference VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_option_per_question UNIQUE(question_id, option_number)
);

-- Import Operations Table
CREATE TABLE IF NOT EXISTS import_operations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operation_id VARCHAR(100) UNIQUE NOT NULL,
    operation_type VARCHAR(30) NOT NULL DEFAULT 'CSV_IMPORT'
        CHECK(operation_type IN ('CSV_IMPORT','ASSET_IMPORT','BULK_UPDATE','SHEET_UPLOAD')),
    initiated_by VARCHAR(100) NOT NULL,
    source_file VARCHAR(1000),
    target_subject_id VARCHAR(150),
    status VARCHAR(20) DEFAULT 'IN_PROGRESS'
        CHECK(status IN ('STARTED','IN_PROGRESS','COMPLETED','FAILED','CANCELLED')),
    total_rows INTEGER DEFAULT 0,
    imported_rows INTEGER DEFAULT 0,
    skipped_rows INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    CONSTRAINT fk_import_subject FOREIGN KEY(target_subject_id)
        REFERENCES subject_registry(subject_id) ON DELETE SET NULL
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_question_sheets_checksum ON question_sheets(file_checksum);
CREATE INDEX IF NOT EXISTS idx_question_sheets_status ON question_sheets(import_status);
CREATE INDEX IF NOT EXISTS idx_questions_sheet_id ON questions(sheet_id);
CREATE INDEX IF NOT EXISTS idx_questions_question_id ON questions(question_id);
CREATE INDEX IF NOT EXISTS idx_import_operations_operation_id ON import_operations(operation_id);
CREATE INDEX IF NOT EXISTS idx_import_operations_status ON import_operations(status);

-- =============================================================================
-- TRIGGERS TO MAINTAIN updated_at
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_qs_updated_at'
    ) THEN
        CREATE TRIGGER trg_qs_updated_at
        BEFORE UPDATE ON question_sheets
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_q_updated_at'
    ) THEN
        CREATE TRIGGER trg_q_updated_at
        BEFORE UPDATE ON questions
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_io_updated_at'
    ) THEN
        CREATE TRIGGER trg_io_updated_at
        BEFORE UPDATE ON import_operations
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END;
$$;

-- =============================================================================
-- DEFAULT SEED CONFIGURATION
-- =============================================================================

INSERT INTO system_configuration (config_key, config_value, config_type, description)
VALUES
('MAX_UPLOAD_SIZE', '50000000', 'NUMBER', 'Max CSV upload size (bytes)'),
('CSV_REQUIRED_COLUMNS',
 '["question_number","question_text","option_1_text","option_2_text","option_3_text","option_4_text","correct_option_number"]',
 'JSON', 'Required CSV columns'),
('UPLOAD_DIR', '"uploads"', 'STRING', 'Directory for CSV uploads')
ON CONFLICT (config_key) DO NOTHING;

-- Completion notice
DO $$
BEGIN
    RAISE NOTICE 'Phase 2A: Content Processor schema deployed successfully';
END;
$$;
