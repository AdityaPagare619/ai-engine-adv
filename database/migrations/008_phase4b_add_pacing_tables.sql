-- migrations/008_phase4b_add_pacing_tables.sql

-- Student load profiles for cognitive load breakdown
CREATE TABLE IF NOT EXISTS student_load_profiles (
    student_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    intrinsic_load DOUBLE PRECISION NOT NULL,
    extraneous_load DOUBLE PRECISION NOT NULL,
    germane_load DOUBLE PRECISION NOT NULL,
    total_load DOUBLE PRECISION NOT NULL,
    overload_risk DOUBLE PRECISION NOT NULL,
    recommendations JSONB
);

-- Stress monitoring logs
CREATE TABLE IF NOT EXISTS stress_monitoring_logs (
    log_id SERIAL PRIMARY KEY,
    student_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    stress_level DOUBLE PRECISION NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    indicators TEXT[],
    intervention TEXT
);

-- Adaptive pacing decisions
CREATE TABLE IF NOT EXISTS adaptive_pacing_decisions (
    decision_id SERIAL PRIMARY KEY,
    student_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    base_time_ms INT NOT NULL,
    final_time_ms INT NOT NULL,
    factor DOUBLE PRECISION NOT NULL,
    breakdown JSONB
);

-- Enhance selection feedback table to record pressure context
ALTER TABLE IF EXISTS selection_feedback
ADD COLUMN IF NOT EXISTS stress_level DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS cognitive_load DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS pacing_policy_version TEXT;
