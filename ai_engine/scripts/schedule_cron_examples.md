# Scheduling Phase 4A Jobs

## Cron (Linux)
# Nightly evaluation (global + concept-specific)
0 2 * * *  /usr/bin/env KT_ENV=prod EVAL_CONCEPT_ID=  python -m ai_engine.src.knowledge_tracing.evaluation.run_evaluation_job
5 2 * * *  /usr/bin/env KT_ENV=prod EVAL_CONCEPT_ID=kinematics_basic python -m ai_engine.src.knowledge_tracing.evaluation.run_evaluation_job

# Daily rollups (aggregate yesterday’s windows)
15 2 * * * /usr/bin/env KT_ENV=prod python -m ai_engine.src.knowledge_tracing.evaluation.persist_rollups_job

# Alerts (SLO guardrails: AUC/ECE)
25 2 * * * /usr/bin/env KT_ENV=prod ALERT_WEBHOOK_URL=${ALERT_WEBHOOK_URL} python -m ai_engine.src.knowledge_tracing.monitoring.alerts_job

## systemd timer (snippet)
[Unit]
Description=Phase4A Evaluation Window Job

[Service]
Type=oneshot
Environment=KT_ENV=prod
ExecStart=/usr/bin/python -m ai_engine.src.knowledge_tracing.evaluation.run_evaluation_job

[Install]
WantedBy=timers.target

## GitHub Actions (nightly)
name: nightly-eval
on:
  schedule:
    - cron: "0 2 * * *"
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - env:
          KT_ENV: prod
        run: python -m ai_engine.src.knowledge_tracing.evaluation.run_evaluation_job
