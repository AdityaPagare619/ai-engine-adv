-- =============================================================================
-- JEE Smart AI Platform - JEE Specific Tables (Complete)
-- Includes Phase 1 and Phase 2 schema updates
-- =============================================================================

-- Exam Registry Table
CREATE TABLE IF NOT EXISTS exam_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exam_id VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    exam_type VARCHAR(50) NOT NULL,
    academic_year INTEGER NOT NULL,
    created_by_admin VARCHAR(100) NOT NULL,
    admin_key_hash VARCHAR(500) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE','INACTIVE','ARCHIVED')),
    total_subjects INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_exam_type_year UNIQUE(exam_type,academic_year),
    CONSTRAINT valid_academic_year CHECK(academic_year>=2020 AND academic_year<=2030)
);

-- Subject Registry Table
CREATE TABLE IF NOT EXISTS subject_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id VARCHAR(150) UNIQUE NOT NULL,
    exam_id VARCHAR(100) NOT NULL REFERENCES exam_registry(exam_id) ON DELETE CASCADE,
    subject_code VARCHAR(10) NOT NULL,
    subject_name VARCHAR(100) NOT NULL,
    total_questions INTEGER DEFAULT 0,
    total_sheets INTEGER DEFAULT 0,
    folder_path VARCHAR(500),
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE','INACTIVE')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_subject_codes CHECK(subject_code IN ('PHY','CHE','MAT','BIO','ENG'))
);

-- Question Sheets Table (CSV import tracking)
CREATE TABLE IF NOT EXISTS question_sheets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sheet_id VARCHAR(200) UNIQUE NOT NULL,
    subject_id VARCHAR(150) NOT NULL REFERENCES subject_registry(subject_id) ON DELETE CASCADE,
    sheet_name VARCHAR(200) NOT NULL,
    file_path VARCHAR(1000),
    version INTEGER DEFAULT 1,
    total_questions INTEGER DEFAULT 0,
    imported_questions INTEGER DEFAULT 0,
    failed_questions INTEGER DEFAULT 0,
    import_status VARCHAR(30) NOT NULL DEFAULT 'PENDING' CHECK(import_status IN ('PENDING','PROCESSING','COMPLETED','FAILED','PARTIAL')),
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
    subject_id VARCHAR(150) NOT NULL REFERENCES subject_registry(subject_id),
    question_number VARCHAR(20) NOT NULL,
    question_text TEXT,
    question_latex TEXT,
    question_type VARCHAR(30) DEFAULT 'MCQ' CHECK(question_type IN ('MCQ','NUMERICAL','ASSERTION_REASON','MATRIX_MATCH')),
    difficulty_level DECIMAL(3,2) DEFAULT 0.5 CHECK(difficulty_level>=0 AND difficulty_level<=1),
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
    validation_status VARCHAR(20) DEFAULT 'PENDING' CHECK(validation_status IN ('PENDING','VALIDATED','REJECTED','NEEDS_REVIEW')),
    confidence_score DECIMAL(3,2) DEFAULT 0.8,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_question_per_sheet UNIQUE(sheet_id,question_number)
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
    CONSTRAINT unique_option_per_question UNIQUE(question_id,option_number)
);

-- Question Assets Table
CREATE TABLE IF NOT EXISTS question_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id VARCHAR(300) UNIQUE NOT NULL,
    question_id VARCHAR(250) REFERENCES questions(question_id) ON DELETE CASCADE,
    option_id VARCHAR(300) REFERENCES question_options(option_id) ON DELETE CASCADE,
    asset_type VARCHAR(20) NOT NULL CHECK(asset_type IN ('IMAGE','DIAGRAM','GRAPH','TABLE','FORMULA')),
    asset_role VARCHAR(30) NOT NULL CHECK(asset_role IN ('QUESTION_IMAGE','OPTION_IMAGE','EXPLANATION_IMAGE','COMPLETE_QUESTION')),
    original_filename VARCHAR(500),
    storage_path VARCHAR(1000),
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    formats JSONB DEFAULT '{}',
    dimensions JSONB DEFAULT '{}',
    processing_status VARCHAR(20) DEFAULT 'PENDING' CHECK(processing_status IN ('PENDING','PROCESSING','COMPLETED','FAILED')),
    optimization_level VARCHAR(10) DEFAULT 'STANDARD' CHECK(optimization_level IN ('BASIC','STANDARD','HIGH')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT asset_belongs_to_question_or_option CHECK(
        (question_id IS NOT NULL AND option_id IS NULL) OR
        (question_id IS NULL AND option_id IS NOT NULL)
    )
);

-- Import Operations Table
CREATE TABLE IF NOT EXISTS import_operations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operation_id VARCHAR(100) UNIQUE NOT NULL,
    operation_type VARCHAR(30) NOT NULL CHECK(operation_type IN ('CSV_IMPORT','ASSET_IMPORT','BULK_UPDATE','SHEET_UPLOAD')),
    initiated_by VARCHAR(100) NOT NULL,
    source_file VARCHAR(1000),
    target_subject_id VARCHAR(150),
    status VARCHAR(20) DEFAULT 'IN_PROGRESS' CHECK(status IN ('STARTED','IN_PROGRESS','COMPLETED','FAILED','CANCELLED')),
    total_rows INTEGER DEFAULT 0,
    imported_rows INTEGER DEFAULT 0,
    skipped_rows INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    CONSTRAINT fk_import_subject FOREIGN KEY(target_subject_id) REFERENCES subject_registry(subject_id) ON DELETE SET NULL
);

-- System Configuration Table
CREATE TABLE IF NOT EXISTS system_configuration (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    config_type VARCHAR(20) NOT NULL CHECK(config_type IN ('STRING','NUMBER','BOOLEAN','JSON')),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    updated_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_question_sheets_checksum ON question_sheets(file_checksum);
CREATE INDEX IF NOT EXISTS idx_import_operations_operation_id ON import_operations(operation_id);
CREATE INDEX IF NOT EXISTS idx_import_operations_status ON import_operations(status);

-- =============================================================================
-- TRIGGERS FOR UPDATED_AT COLUMNS
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables
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
-- DEFAULT SEED DATA
-- =============================================================================

INSERT INTO system_configuration (config_key, config_value, config_type, description)
VALUES
('MAX_UPLOAD_SIZE', '50000000', 'NUMBER', 'Max CSV upload size (bytes)'),
('CSV_REQUIRED_COLUMNS', '["question_number","question_text","option_1_text","option_2_text","option_3_text","option_4_text","correct_option_number"]', 'JSON', 'Required CSV columns'),
('UPLOAD_DIR', '"uploads"', 'STRING', 'Directory for uploaded CSV files')
ON CONFLICT (config_key) DO NOTHING;
