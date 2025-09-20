-- database/migrations/006_create_selection_feedback_table.sql

-- Logs each bandit decision with features, score, and realized reward
CREATE TABLE IF NOT EXISTS bkt_selection_feedback (
  feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  student_id TEXT NOT NULL,
  concept_id TEXT NOT NULL,
  question_id TEXT NOT NULL,
  policy TEXT NOT NULL DEFAULT 'LinUCB',
  score DOUBLE PRECISION NOT NULL,
  reward DOUBLE PRECISION NULL,         -- e.g., correctness (0/1) or learning gain
  features JSONB NOT NULL,              -- serialized context feature vector and metadata
  debug JSONB NOT NULL DEFAULT '{}'::jsonb,
  decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bkt_sel_fb_student_concept ON bkt_selection_feedback (student_id, concept_id);
CREATE INDEX IF NOT EXISTS idx_bkt_sel_fb_question ON bkt_selection_feedback (question_id);
CREATE INDEX IF NOT EXISTS idx_bkt_sel_fb_time ON bkt_selection_feedback (decided_at);

-- Optional lightweight reward view by concept/day
CREATE MATERIALIZED VIEW IF NOT EXISTS bkt_selection_rewards_daily AS
SELECT
  DATE_TRUNC('day', decided_at) AS day,
  concept_id,
  COUNT(*) AS n_decisions,
  AVG(COALESCE(reward, 0)) AS avg_reward
FROM bkt_selection_feedback
GROUP BY 1, 2;

CREATE INDEX IF NOT EXISTS idx_bkt_sel_rewards_daily ON bkt_selection_rewards_daily (day, concept_id);
