#!/usr/bin/env bash
set -euo pipefail

echo "[Phase4A] Running database migrations..."
psql "$POSTGRES_URL" -f database/migrations/005_create_bkt_evaluation_tables.sql
psql "$POSTGRES_URL" -f database/migrations/006_create_selection_feedback_table.sql

echo "[Phase4A] Syncing question metadata cache to Supabase..."
python ai_engine/scripts/sync_question_metadata.py

echo "[Phase4A] Running unit tests..."
pytest ai_engine/tests/unit -q

echo "[Phase4A] Running integration tests (requires local services)..."
pytest ai_engine/tests/integration -q || echo "[WARN] Integration tests failed or services unavailable."

echo "[Phase4A] Starting API (dev mode)..."
# Replace with your app entrypoint/ASGI path
uvicorn services.admin-management.app:app --host 0.0.0.0 --port 8001 --reload
