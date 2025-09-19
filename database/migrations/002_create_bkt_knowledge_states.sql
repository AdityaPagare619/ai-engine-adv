-- Stores student-concept mastery and counts
CREATE TABLE IF NOT EXISTS bkt_knowledge_states (
  student_id          UUID       NOT NULL REFERENCES students(id),
  concept_id          VARCHAR(100) NOT NULL REFERENCES bkt_parameters(concept_id),
  mastery_probability NUMERIC(5,4) NOT NULL CHECK (mastery_probability BETWEEN 0 AND 1),
  practice_count      INTEGER    NOT NULL DEFAULT 0 CHECK (practice_count >= 0),
  last_updated        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (student_id, concept_id)
);
