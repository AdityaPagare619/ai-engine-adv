-- Creates table for per-concept BKT parameters
CREATE TABLE IF NOT EXISTS bkt_parameters (
  concept_id     VARCHAR(100) PRIMARY KEY,
  learn_rate     NUMERIC(5,4) NOT NULL CHECK (learn_rate BETWEEN 0 AND 1),
  slip_rate      NUMERIC(5,4) NOT NULL CHECK (slip_rate BETWEEN 0 AND 0.5),
  guess_rate     NUMERIC(5,4) NOT NULL CHECK (guess_rate BETWEEN 0 AND 0.5),
  updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
