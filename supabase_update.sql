-- Add missing engine_version column to bkt_update_logs table
-- Run this in Supabase SQL Editor if the column is missing

ALTER TABLE bkt_update_logs 
ADD COLUMN IF NOT EXISTS engine_version text DEFAULT 'v1.0';

-- Verify the column was added
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'bkt_update_logs' 
  AND column_name = 'engine_version';