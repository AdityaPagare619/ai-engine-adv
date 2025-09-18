-- =============================================================================
-- JEE Smart AI Platform - Initial Seed Data
-- =============================================================================

-- Initialize ID sequences for different types
INSERT INTO id_sequences (sequence_type, sequence_key, current_value, prefix, format_template) VALUES
('EXAM_ID', 'GLOBAL', 0, 'EXM', 'EXM-{year}-{type}-{seq:03d}'),
('SUBJECT_ID', 'GLOBAL', 0, 'SUB', '{exam_id}-SUB-{code}'),
('SHEET_ID', 'GLOBAL', 0, 'SHT', '{subject_id}-SHT-V{version:02d}'),
('QUESTION_ID', 'GLOBAL', 0, 'Q', '{sheet_id}-Q-{seq:05d}'),
('ASSET_ID', 'GLOBAL', 0, 'AST', '{question_id}-AST-{type}-{seq:03d}');

-- Sample exam registry entries for testing
INSERT INTO exam_registry (exam_id, display_name, exam_type, academic_year, created_by_admin, admin_key_hash, status) VALUES
('EXM-2025-JEE_MAIN-001', 'JEE Main 2025 January Session', 'JEE_MAIN', 2025, 'system_admin', '$2b$12$LQv3c1yqBWVHxkd0LQ1NGO.NxBYNGkVLNzYK0hGN4z6fwF2qV2tWy', 'ACTIVE'),
('EXM-2025-JEE_ADV-001', 'JEE Advanced 2025', 'JEE_ADVANCED', 2025, 'system_admin', '$2b$12$LQv3c1yqBWVHxkd0LQ1NGO.NxBYNGkVLNzYK0hGN4z6fwF2qV2tWy', 'ACTIVE'),
('EXM-2025-NEET-001', 'NEET 2025', 'NEET', 2025, 'system_admin', '$2b$12$LQv3c1yqBWVHxkd0LQ1NGO.NxBYNGkVLNzYK0hGN4z6fwF2qV2tWy', 'ACTIVE');

-- Subject registry for JEE Main
INSERT INTO subject_registry (subject_id, exam_id, subject_code, subject_name, folder_path) VALUES
('EXM-2025-JEE_MAIN-001-SUB-PHY', 'EXM-2025-JEE_MAIN-001', 'PHY', 'Physics', 'data/exam-registry/EXM-2025-JEE_MAIN-001/subjects/physics'),
('EXM-2025-JEE_MAIN-001-SUB-CHE', 'EXM-2025-JEE_MAIN-001', 'CHE', 'Chemistry', 'data/exam-registry/EXM-2025-JEE_MAIN-001/subjects/chemistry'),
('EXM-2025-JEE_MAIN-001-SUB-MAT', 'EXM-2025-JEE_MAIN-001', 'MAT', 'Mathematics', 'data/exam-registry/EXM-2025-JEE_MAIN-001/subjects/mathematics');

-- Subject registry for JEE Advanced
INSERT INTO subject_registry (subject_id, exam_id, subject_code, subject_name, folder_path) VALUES
('EXM-2025-JEE_ADV-001-SUB-PHY', 'EXM-2025-JEE_ADV-001', 'PHY', 'Physics', 'data/exam-registry/EXM-2025-JEE_ADV-001/subjects/physics'),
('EXM-2025-JEE_ADV-001-SUB-CHE', 'EXM-2025-JEE_ADV-001', 'CHE', 'Chemistry', 'data/exam-registry/EXM-2025-JEE_ADV-001/subjects/chemistry'),
('EXM-2025-JEE_ADV-001-SUB-MAT', 'EXM-2025-JEE_ADV-001', 'MAT', 'Mathematics', 'data/exam-registry/EXM-2025-JEE_ADV-001/subjects/mathematics');

-- Subject registry for NEET
INSERT INTO subject_registry (subject_id, exam_id, subject_code, subject_name, folder_path) VALUES
('EXM-2025-NEET-001-SUB-PHY', 'EXM-2025-NEET-001', 'PHY', 'Physics', 'data/exam-registry/EXM-2025-NEET-001/subjects/physics'),
('EXM-2025-NEET-001-SUB-CHE', 'EXM-2025-NEET-001', 'CHE', 'Chemistry', 'data/exam-registry/EXM-2025-NEET-001/subjects/chemistry'),
('EXM-2025-NEET-001-SUB-BIO', 'EXM-2025-NEET-001', 'BIO', 'Biology', 'data/exam-registry/EXM-2025-NEET-001/subjects/biology');

-- Update sequence counters
UPDATE id_sequences SET current_value = 3 WHERE sequence_type = 'EXAM_ID';
UPDATE id_sequences SET current_value = 9 WHERE sequence_type = 'SUBJECT_ID';

COMMIT;
