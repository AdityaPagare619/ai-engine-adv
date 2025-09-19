-- =============================================================================
-- JEE Smart AI Platform - Complete Foundation Database Schema (FIXED)
-- Industry-Grade Educational Assessment System
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================================================
-- CORE REGISTRY TABLES (Admin Controlled) - WITH ALL REQUIRED COLUMNS
-- =============================================================================

-- Exam Registry (Top Level Container) - COMPLETE VERSION
CREATE TABLE IF NOT EXISTS exam_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exam_id VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    exam_type VARCHAR(50) NOT NULL,
    academic_year INTEGER NOT NULL,
    created_by_admin VARCHAR(100) NOT NULL,
    admin_key_hash VARCHAR(500) NOT NULL DEFAULT 'default_hash',
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE', 'ARCHIVED')),
    total_subjects INTEGER DEFAULT 0,  -- ✅ ADDED MISSING COLUMN
    total_questions INTEGER DEFAULT 0, -- ✅ ADDED MISSING COLUMN
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_exam_type_year UNIQUE(exam_type, academic_year),
    CONSTRAINT valid_academic_year CHECK (academic_year >= 2020 AND academic_year <= 2030)
);

-- Subject Registry (Within Exams) - COMPLETE VERSION
CREATE TABLE IF NOT EXISTS subject_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id VARCHAR(150) UNIQUE NOT NULL,
    exam_id VARCHAR(100) NOT NULL,
    subject_code VARCHAR(10) NOT NULL,
    subject_name VARCHAR(100) NOT NULL,
    total_questions INTEGER DEFAULT 0,
    total_sheets INTEGER DEFAULT 0,
    folder_path VARCHAR(500),
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key constraint with proper reference
    CONSTRAINT fk_subject_exam FOREIGN KEY (exam_id) REFERENCES exam_registry(exam_id) ON DELETE CASCADE,
    -- Constraints
    CONSTRAINT valid_subject_codes CHECK (subject_code IN ('PHY', 'CHE', 'MAT', 'BIO', 'ENG'))
);

-- Question Sheets (CSV Import Tracking) - COMPLETE VERSION
CREATE TABLE IF NOT EXISTS question_sheets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sheet_id VARCHAR(200) UNIQUE NOT NULL,
    subject_id VARCHAR(150) NOT NULL,
    sheet_name VARCHAR(200) NOT NULL,
    file_path VARCHAR(1000),
    version INTEGER DEFAULT 1,
    total_questions INTEGER DEFAULT 0,
    imported_questions INTEGER DEFAULT 0,
    failed_questions INTEGER DEFAULT 0,
    import_status VARCHAR(30) DEFAULT 'PENDING' CHECK (import_status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'PARTIAL')),
    file_checksum VARCHAR(128),
    last_imported_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key constraint
    CONSTRAINT fk_sheet_subject FOREIGN KEY (subject_id) REFERENCES subject_registry(subject_id) ON DELETE CASCADE
);

-- System Configuration (Admin Settings) - COMPLETE VERSION
CREATE TABLE IF NOT EXISTS system_configuration (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(20) NOT NULL CHECK (config_type IN ('STRING', 'INTEGER', 'BOOLEAN', 'JSON')),
    description TEXT,
    is_sensitive BOOLEAN DEFAULT FALSE,
    last_modified_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ID Sequences (For Hierarchical ID Generation) - COMPLETE VERSION
CREATE TABLE IF NOT EXISTS id_sequences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sequence_type VARCHAR(50) NOT NULL,
    sequence_key VARCHAR(200) NOT NULL,
    current_value INTEGER NOT NULL DEFAULT 0,
    prefix VARCHAR(50),
    suffix VARCHAR(50),
    format_template VARCHAR(200),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Ensure unique sequence per type and key
    CONSTRAINT unique_sequence_type_key UNIQUE(sequence_type, sequence_key)
);

-- Import Operations (Audit Trail) - COMPLETE VERSION
CREATE TABLE IF NOT EXISTS import_operations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operation_id VARCHAR(100) UNIQUE NOT NULL,
    operation_type VARCHAR(30) NOT NULL CHECK (operation_type IN ('CSV_IMPORT', 'ASSET_IMPORT', 'BULK_UPDATE', 'SHEET_UPLOAD')),
    initiated_by VARCHAR(100) NOT NULL,
    source_file VARCHAR(1000),
    target_subject_id VARCHAR(150),
    status VARCHAR(20) DEFAULT 'STARTED' CHECK (status IN ('STARTED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'CANCELLED')),
    total_items INTEGER DEFAULT 0,
    processed_items INTEGER DEFAULT 0,
    successful_items INTEGER DEFAULT 0,
    failed_items INTEGER DEFAULT 0,
    error_log TEXT,
    success_log TEXT,
    performance_metrics JSONB DEFAULT '{}',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,

    -- Foreign key constraint
    CONSTRAINT fk_operation_subject FOREIGN KEY (target_subject_id) REFERENCES subject_registry(subject_id) ON DELETE SET NULL
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- Exam Registry Indexes
CREATE INDEX IF NOT EXISTS idx_exam_registry_exam_id ON exam_registry(exam_id);
CREATE INDEX IF NOT EXISTS idx_exam_registry_type_year ON exam_registry(exam_type, academic_year);
CREATE INDEX IF NOT EXISTS idx_exam_registry_status ON exam_registry(status);

-- Subject Registry Indexes
CREATE INDEX IF NOT EXISTS idx_subject_registry_subject_id ON subject_registry(subject_id);
CREATE INDEX IF NOT EXISTS idx_subject_registry_exam_id ON subject_registry(exam_id);
CREATE INDEX IF NOT EXISTS idx_subject_registry_code ON subject_registry(subject_code);

-- Question Sheets Indexes
CREATE INDEX IF NOT EXISTS idx_question_sheets_sheet_id ON question_sheets(sheet_id);
CREATE INDEX IF NOT EXISTS idx_question_sheets_subject_id ON question_sheets(subject_id);
CREATE INDEX IF NOT EXISTS idx_question_sheets_status ON question_sheets(import_status);

-- System Configuration Indexes
CREATE INDEX IF NOT EXISTS idx_system_configuration_key ON system_configuration(config_key);
CREATE INDEX IF NOT EXISTS idx_system_configuration_type ON system_configuration(config_type);

-- ID Sequences Indexes
CREATE INDEX IF NOT EXISTS idx_id_sequences_type_key ON id_sequences(sequence_type, sequence_key);

-- Import Operations Indexes
CREATE INDEX IF NOT EXISTS idx_import_operations_operation_id ON import_operations(operation_id);
CREATE INDEX IF NOT EXISTS idx_import_operations_status ON import_operations(status);
CREATE INDEX IF NOT EXISTS idx_import_operations_type ON import_operations(operation_type);

-- =============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =============================================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers to all relevant tables
DROP TRIGGER IF EXISTS update_exam_registry_updated_at ON exam_registry;
CREATE TRIGGER update_exam_registry_updated_at BEFORE UPDATE ON exam_registry
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_subject_registry_updated_at ON subject_registry;
CREATE TRIGGER update_subject_registry_updated_at BEFORE UPDATE ON subject_registry
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_question_sheets_updated_at ON question_sheets;
CREATE TRIGGER update_question_sheets_updated_at BEFORE UPDATE ON question_sheets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_system_configuration_updated_at ON system_configuration;
CREATE TRIGGER update_system_configuration_updated_at BEFORE UPDATE ON system_configuration
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- INITIAL SYSTEM CONFIGURATION
-- =============================================================================

INSERT INTO system_configuration (config_key, config_value, config_type, description) VALUES
('SYSTEM_VERSION', '1.0.0', 'STRING', 'Current system version'),
('MAX_QUESTIONS_PER_SHEET', '1000', 'INTEGER', 'Maximum questions allowed per CSV sheet'),
('SUPPORTED_IMAGE_FORMATS', '["png", "jpg", "jpeg", "webp", "svg"]', 'JSON', 'Supported image formats for assets'),
('DEFAULT_DIFFICULTY_LEVEL', '0.5', 'STRING', 'Default difficulty level for new questions'),
('ENABLE_AUTO_VALIDATION', 'true', 'BOOLEAN', 'Enable automatic question validation'),
('MAX_FILE_SIZE_MB', '50', 'INTEGER', 'Maximum file size for uploads in MB'),
('ASSET_OPTIMIZATION_LEVEL', 'STANDARD', 'STRING', 'Default asset optimization level'),
('ID_GENERATION_PREFIX', 'EXM', 'STRING', 'Prefix for exam ID generation'),
('BACKUP_RETENTION_DAYS', '90', 'INTEGER', 'Number of days to retain backups'),
('ENABLE_PERFORMANCE_MONITORING', 'true', 'BOOLEAN', 'Enable system performance monitoring'),
('ADMIN_KEY_VALID', 'jee-admin-2025-secure', 'STRING', 'Valid admin key for authentication')
ON CONFLICT (config_key) DO UPDATE SET
    config_value = EXCLUDED.config_value,
    updated_at = CURRENT_TIMESTAMP;

-- Initialize ID sequences for different types
INSERT INTO id_sequences (sequence_type, sequence_key, current_value, prefix, format_template) VALUES
('EXAM_ID', 'GLOBAL', 0, 'EXM', 'EXM-{year}-{type}-{seq:03d}'),
('SUBJECT_ID', 'GLOBAL', 0, 'SUB', '{exam_id}-SUB-{code}'),
('SHEET_ID', 'GLOBAL', 0, 'SHT', '{subject_id}-SHT-V{version:02d}'),
('QUESTION_ID', 'GLOBAL', 0, 'Q', '{sheet_id}-Q-{seq:05d}'),
('ASSET_ID', 'GLOBAL', 0, 'AST', '{question_id}-AST-{type}-{seq:03d}')
ON CONFLICT (sequence_type, sequence_key) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- Sample exam registry entries for testing
INSERT INTO exam_registry (exam_id, display_name, exam_type, academic_year, created_by_admin, admin_key_hash, status, total_subjects) VALUES
('EXM-2025-JEE_MAIN-001', 'JEE Main 2025 January Session', 'JEE_MAIN', 2025, 'system_admin', crypt('jee-admin-2025-secure', gen_salt('bf')), 'ACTIVE', 3),
('EXM-2025-JEE_ADV-001', 'JEE Advanced 2025', 'JEE_ADVANCED', 2025, 'system_admin', crypt('jee-admin-2025-secure', gen_salt('bf')), 'ACTIVE', 3),
('EXM-2025-NEET-001', 'NEET 2025', 'NEET', 2025, 'system_admin', crypt('jee-admin-2025-secure', gen_salt('bf')), 'ACTIVE', 3)
ON CONFLICT (exam_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- Subject registry for JEE Main
INSERT INTO subject_registry (subject_id, exam_id, subject_code, subject_name, folder_path) VALUES
('EXM-2025-JEE_MAIN-001-SUB-PHY', 'EXM-2025-JEE_MAIN-001', 'PHY', 'Physics', 'data/exam-registry/EXM-2025-JEE_MAIN-001/subjects/physics'),
('EXM-2025-JEE_MAIN-001-SUB-CHE', 'EXM-2025-JEE_MAIN-001', 'CHE', 'Chemistry', 'data/exam-registry/EXM-2025-JEE_MAIN-001/subjects/chemistry'),
('EXM-2025-JEE_MAIN-001-SUB-MAT', 'EXM-2025-JEE_MAIN-001', 'MAT', 'Mathematics', 'data/exam-registry/EXM-2025-JEE_MAIN-001/subjects/mathematics')
ON CONFLICT (subject_id) DO UPDATE SET
    updated_at = CURRENT_TIMESTAMP;

-- Update sequence counters
UPDATE id_sequences SET current_value = 3 WHERE sequence_type = 'EXAM_ID';
UPDATE id_sequences SET current_value = 9 WHERE sequence_type = 'SUBJECT_ID';

-- =============================================================================
-- COMPLETION MESSAGE
-- =============================================================================
DO $$
BEGIN
    RAISE NOTICE 'JEE Smart AI Platform - Foundation Schema Created Successfully';
    RAISE NOTICE 'Total Tables: 8';
    RAISE NOTICE 'Total Indexes: 15';
    RAISE NOTICE 'Total Triggers: 4';
    RAISE NOTICE 'Extensions Installed: uuid-ossp, pgcrypto, btree_gin, pg_trgm';
    RAISE NOTICE 'System Ready for Phase 1 Operations';
END $$;
