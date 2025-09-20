# Phase 4A API Reference

All endpoints are served under your FastAPI application and grouped under the /ai/trace prefix.

## POST /ai/trace/update
Updates mastery for a student–concept using canonical BKT with contextual parameter modulation and constraint projection.

Request (application/json):
{
  "student_id": "s1",
  "concept_id": "kinematics_basic",
  "question_id": "PHY_MECH_0001",
  "is_correct": true,
  "response_time_ms": 2300,
  "difficulty_level": null,
  "bloom_level": null
}

Response (application/json):
{
  "previous_mastery": 0.50,
  "posterior_mastery": 0.59,
  "new_mastery": 0.70,
  "p_correct_pred": 0.68,
  "adjusted_params": {"learn_rate":0.25,"slip_rate":0.11,"guess_rate":0.22},
  "constraint_violations": [],
  "explanation": {
    "context": {...},
    "param_adjustments": {...},
    "bkt": {"p_correct": 0.68, "posterior_formula": "..." }
  }
}

Notes:
- p_correct_pred corresponds to \(m(1-s)+(1-m)g\) before observing the current answer; equations trace to Corbett–Anderson BKT. 
- adjusted_params are feasible after identifiability, ordering, and JEDM-style bounds are enforced.

## POST /ai/trace/evaluate
Computes next-step AUC/ACC, Brier, ECE, and a trajectory validity score using production data providers.

Request:
{"concept_id":"kinematics_basic","start_ts":"ISO|optional","end_ts":"ISO|optional"}

Response:
{"next_step_auc":0.78,"next_step_accuracy":0.72,"brier_score":0.19,"calibration_error":0.08,"trajectory_validity":0.65,"recommendation":"PASS","details":{...}}

## POST /ai/trace/evaluate_and_save
Runs evaluation and persists a row into bkt_evaluation_windows for dashboards and SLO monitoring.

## GET /ai/trace/select
Returns the next question based on LinUCB with interpretable features (uncertainty, recency, difficulty, time-cost).

Query:
?student_id=s1&concept_id=kinematics_basic&subject=Physics&topic=Kinematics

Response:
{"chosen_question_id":"PHY_MECH_0007","debug":{"scores":[{"arm_id":"...","score":...}], "chosen":{...}}}

## POST /ai/trace/feedback
Ingests bandit decision feedback for online policy learning and audits.

Request:
{"student_id":"s1","concept_id":"kinematics_basic","question_id":"Q1","policy":"LinUCB","score":1.42,"reward":1.0,"features":{...},"debug":{...}}

## GET /ai/trace/calibration
Returns reliability bins (confidence vs accuracy) for plotting calibration curves (ECE from evaluation suite).

Query:
?concept_id=kinematics_basic&bins=10
