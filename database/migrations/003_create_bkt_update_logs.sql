-- Append-only log of each mastery update
CREATE TABLE IF NOT EXISTS bkt_update_logs (
  log_id          BIGSERIAL PRIMARY KEY,
  student_id      UUID       NOT NULL REFERENCES students(id),
  concept_id      VARCHAR(100) NOT NULL REFERENCES bkt_parameters(concept_id),
  previous_mastery NUMERIC(5,4) NOT NULL,
  new_mastery     NUMERIC(5,4) NOT NULL,
  is_correct      BOOLEAN    NOT NULL,
  response_time_ms INTEGER,
  timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
