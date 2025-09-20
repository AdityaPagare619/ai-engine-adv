-- database/migrations/007_add_params_json_to_logs.sql

-- Ensure table exists before altering
ALTER TABLE IF EXISTS bkt_update_logs
ADD COLUMN IF NOT EXISTS params_used JSONB NULL;  -- {"learn_rate":..., "slip_rate":..., "guess_rate":...}

-- Set default value for params_used
ALTER TABLE bkt_update_logs
ALTER COLUMN params_used SET DEFAULT '{}'::jsonb;

-- Add engine version column for reproducibility
ALTER TABLE bkt_update_logs
ADD COLUMN IF NOT EXISTS engine_version TEXT;

-- Optional: lightweight GIN index for analytics queries on params_used
CREATE INDEX IF NOT EXISTS idx_bkt_update_logs_params_used ON bkt_update_logs USING GIN (params_used);

-- Optional: ensure timestamp is indexed for window scans
CREATE INDEX IF NOT EXISTS idx_bkt_update_logs_timestamp ON bkt_update_logs (timestamp);
