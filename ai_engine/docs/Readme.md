# Phase 4A — Bayesian Knowledge Tracing Engine

This document is the engineering guide for the mathematically rigorous, production-grade BKT system with calibration metrics, contextual selection, and spacing. It maps equations → APIs → tests so implementation and ops stay aligned.

## Core math
- Posterior updates (Corbett–Anderson) and transition are implemented in `core/bkt_core.py`, with numerically safe denominators and predictive correctness used for AUC/Brier.  
- Constraints (identifiability, performance ordering, JEDM bound) are enforced in `core/constraint_validator.py` with solver-free feasible projection.  

## Orchestration
- `service/advanced_bkt_service.py` sequences: fetch state/params → contextual modulation (difficulty, Bloom, RT) → validate → canonical update → persist/log with explanations.  
- Public endpoints: `/ai/trace/update`, `/ai/trace/evaluate`, `/ai/trace/evaluate_and_save`, `/ai/trace/select`, `/ai/trace/feedback`.  

## Evaluation and calibration
- `evaluation/data_provider.py` reconstructs next-step predictions from logs + base params + item context; `evaluation/metrics.py` computes AUC/ACC, Brier/ECE, and trajectory validity.  
- Batch jobs: `run_evaluation_job.py` persists `bkt_evaluation_windows`; `persist_rollups_job.py` maintains `bkt_evaluation_concept_daily`.  

## Selection and spacing
- LinUCB policy in `selection/bandit_policy.py` with interpretable features (uncertainty, recency, difficulty) and feedback logging via `/feedback`.  
- HLR spacing in `scheduling/hlr_scheduler.py` proposes next review gaps to maintain target recall; combine with BKT updates for retention.  

## Modern extensions
- SAKT stub in `models/sakt_model.py` and `models/ensemble_gate.py` blends BKT and attention predictions with bounded weights and calibration-aware gating.  
- Parameter estimation in `params/estimation.py` (spectral init + constrained EM scaffold).  

## Settings, migrations, and scripts
- Feature flags and thresholds in `config/settings.py`; migrations `005_*` and `006_*` for evaluation and selection feedback; `scripts/deploy_phase4a.sh` for dev/CI flows.  

## Test strategy
- Unit: core math, constraints, estimation, HLR, bandit, ensemble.  
- Integration: BKT with context, evaluate endpoint, selection endpoint.  

## Acceptance targets
- AUC ≥ 0.75, Brier ≤ 0.20, ECE ≤ 0.10, trajectory validity ≥ 0.60 on validation windows.  
- p95 latency < 100 ms for `/ai/trace/update` and `/ai/trace/select` on standard loads.  
