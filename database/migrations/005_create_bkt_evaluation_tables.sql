-- database/migrations/005_create_bkt_evaluation_tables.sql

-- Window-level evaluation results (per run, per concept or global)
CREATE TABLE IF NOT EXISTS bkt_evaluation_windows (
  eval_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  concept_id TEXT NULL,
  start_ts TIMESTAMPTZ NULL,
  end_ts TIMESTAMPTZ NULL,
  next_step_auc DOUBLE PRECISION NOT NULL,
  next_step_accuracy DOUBLE PRECISION NOT NULL,
  brier_score DOUBLE PRECISION NOT NULL,
  calibration_error DOUBLE PRECISION NOT NULL,
  trajectory_validity DOUBLE PRECISION NOT NULL,
  recommendation TEXT NOT NULL,
  details JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bkt_eval_windows_concept ON bkt_evaluation_windows (concept_id);
CREATE INDEX IF NOT EXISTS idx_bkt_eval_windows_time ON bkt_evaluation_windows (start_ts, end_ts);

-- Daily per-concept rollups for monitoring and alerts
CREATE TABLE IF NOT EXISTS bkt_evaluation_concept_daily (
  day DATE NOT NULL,
  concept_id TEXT NOT NULL,
  next_step_auc_avg DOUBLE PRECISION NOT NULL,
  brier_score_avg DOUBLE PRECISION NOT NULL,
  calibration_error_avg DOUBLE PRECISION NOT NULL,
  trajectory_validity_avg DOUBLE PRECISION NOT NULL,
  runs_count INTEGER NOT NULL,
  PRIMARY KEY (day, concept_id)
);

-- Optional MV to compute latest per-concept snapshot
CREATE MATERIALIZED VIEW IF NOT EXISTS bkt_evaluation_latest AS
SELECT DISTINCT ON (concept_id)
  concept_id,
  next_step_auc,
  brier_score,
  calibration_error,
  trajectory_validity,
  recommendation,
  created_at
FROM bkt_evaluation_windows
WHERE concept_id IS NOT NULL
ORDER BY concept_id, created_at DESC;

CREATE INDEX IF NOT EXISTS idx_bkt_eval_latest_concept ON bkt_evaluation_latest (concept_id);
