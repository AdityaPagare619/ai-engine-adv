#!/usr/bin/env python3
"""
Run a full, enterprise-grade AI engine simulation for a single student across multiple exams.
Pipeline per step: Stress → Cognitive Load → Time Allocation → Bandit Selection → BKT Update → Intervention
- Reads Supabase credentials from env files via repository client
- Persists knowledge state and logs
- Prints objective, non-predefined results for analysis
"""
import os
import sys
import math
import time
import random
import asyncio
from statistics import mean

# Project root
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
print('PY_PATH_HEAD', sys.path[:3])

# Ensure Supabase env present without shell

def _parse_env_file(path: str):
    if not os.path.exists(path):
        return
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip(); v = v.strip().strip('"')
                    if k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY") and not os.getenv(k):
                        os.environ[k] = v
    except Exception:
        pass

_parse_env_file(os.path.join(ROOT, 'ai_engine', '.env'))
_parse_env_file(os.path.join(ROOT, '.env'))

# Engine imports
from ai_engine.src.config.exam_config import EXAM_CONFIGS
from ai_engine.src.knowledge_tracing.bkt.repository import BKTRepository
from ai_engine.src.knowledge_tracing.bkt.model import BayesianKnowledgeTracing
from ai_engine.src.knowledge_tracing.bkt.integration import BKTInterventionIntegration
from ai_engine.src.knowledge_tracing.core.bkt_core import CanonicalBKTCore
from ai_engine.src.knowledge_tracing.stress.detection_engine import MultiModalStressDetector
from ai_engine.src.knowledge_tracing.congnitive.load_manager import CognitiveLoadManager
from ai_engine.src.knowledge_tracing.pacing.time_allocator import DynamicTimeAllocator, TimeAllocationRequest
from ai_engine.src.knowledge_tracing.selection.candidate_provider import CandidateProvider
from ai_engine.src.knowledge_tracing.selection.bandit_policy import BanditContext
from ai_engine.src.knowledge_tracing.selection.pressure_linucb import PressureAwareLinUCB

async def simulate_session(exam_code: str, concept_id: str, student_id: str, steps: int = 20):
    repo = BKTRepository()  # Supabase-backed (reads .env via client)
    bkt_model = BayesianKnowledgeTracing(concept_id=concept_id, repo=repo)
    await bkt_model.initialize_with_context(student_id)

    stress = MultiModalStressDetector(window_size=12)
    cog = CognitiveLoadManager()
    allocator = DynamicTimeAllocator()
    provider = CandidateProvider(datasource=None, exam_code=exam_code)
    bandit = PressureAwareLinUCB(alpha=0.3, d=7)  # exploration parameter
    integrator = BKTInterventionIntegration()

    exam_cfg = EXAM_CONFIGS.get(exam_code, EXAM_CONFIGS["JEE_Mains"])

    # Histories
    times_ms = []
    correctness = []
    mastery_series = []
    interventions = 0

    # Session loop
    for i in range(steps):
        # Current state
        state = repo.get_state(student_id, concept_id)
        mastery = state.mastery_probability

        # Build candidate list (mock source) and bandit contexts
        candidates = provider.build_candidates(student_id=student_id, concept_id=concept_id,
                                               stress_level=0.0, cognitive_load=0.0)
        contexts = []
        for c in candidates:
            f = c["features"].copy()
            f["mastery_level"] = mastery
            f["correct_score"] = exam_cfg.scoring_scheme.correct_score
            f["incorrect_score"] = exam_cfg.scoring_scheme.incorrect_score
            contexts.append(BanditContext(arm_id=c["arm_id"], features=f))

        # Detect stress using last RT/correctness; use 0 for first iterations
        last_rt = times_ms[-1] if times_ms else 30000.0
        last_correct = correctness[-1] if correctness else True
        stress_level = stress.detect(response_time=last_rt, correct=last_correct,
                                     hesitation_ms=0.0, keystroke_dev=0.0).level

        # Compute cognitive load for a nominal item (approx based on last selection or first candidate)
        item_md = {
            "solution_steps": 4,
            "concepts_required": [concept_id],
            "prerequisites": [],
            "learning_value": 0.6,
            "schema_complexity": 0.4,
        }
        student_state = {
            "session_duration_minutes": i*2,
            f"mastery_{concept_id}": mastery,
            "flow_state_factor": 1.0,
            "cognitive_capacity_modifier": 1.0,
        }
        context_factors = {
            "time_pressure_ratio": 0.8,
            "interface_complexity_score": 0.3,
            "distraction_level": 0.2,
            "presentation_quality": 0.9,
            "exam_code": exam_code,
        }
        load_assess = cog.assess_cognitive_load(item_metadata=item_md,
                                                student_state=student_state,
                                                context_factors=context_factors,
                                                stress_level=stress_level,
                                                device_profile={"type":"mobile","screen_class":"small","bandwidth":"medium"})

        # Update stress/cog in feature vectors
        for ctx in contexts:
            x = ctx.feature_vector()
            x[3] = float(stress_level)
            x[4] = float(load_assess.total_load)

        # Select question via bandit
        arm_id, _meta = bandit.select_with_pressure(contexts)
        chosen = next(c for c in contexts if c.arm_id == arm_id)
        difficulty = float(chosen.features.get("difficulty", 0.5))
        est_ms = float(chosen.features.get("estimated_time_ms", 30000))

        # Allocate time (exam-aware)
        req = TimeAllocationRequest(
            student_id=student_id,
            question_id=arm_id,
            base_time_ms=int(max(10000, est_ms)),
            stress_level=float(stress_level),
            fatigue_level=min(1.0, i/float(steps)),
            mastery=float(mastery),
            difficulty=float(difficulty),
            session_elapsed_ms=i*120000,
            exam_code=exam_code,
        )
        time_resp = allocator.allocate(req, mobile_headers={"device_type":"mobile","screen_class":"small","network":"medium"})
        # Simulate actual response time with variance around allocated
        response_time_ms = int(max(1000, random.gauss(time_resp.final_time_ms, time_resp.final_time_ms*0.15)))

        # Predict correctness probability using current params
        params = repo.get_parameters(concept_id)
        p_correct = CanonicalBKTCore.predict_correctness(mastery, params.slip_rate, params.guess_rate)
        # Penalize by stress and load
        penalty = 0.15*stress_level + 0.1*min(1.0, load_assess.total_load/6.0)
        p = max(0.01, min(0.99, p_correct * (1.0 - penalty)))
        is_correct = random.random() < p

        # Update BKT
        update_result = await bkt_model.update(student_id=student_id,
                                               correct=is_correct,
                                               response_time_ms=response_time_ms,
                                               question_id=arm_id)

        # Intervention check
        intervention = await integrator.process_response(student_id=student_id,
                                                         concept_id=concept_id,
                                                         is_correct=is_correct,
                                                         response_time_ms=response_time_ms,
                                                         bkt_model=bkt_model,
                                                         bkt_result=update_result,
                                                         question_difficulty=float(difficulty),
                                                         time_pressure=1.0 - context_factors["time_pressure_ratio"])
        if intervention:
            interventions += 1

        # Track series
        times_ms.append(response_time_ms)
        correctness.append(is_correct)
        mastery_series.append(update_result["new_mastery"]) 

        # Optional: update bandit with observed reward per time
        # Reward = exam score per 30s window
        score = exam_cfg.scoring_scheme.correct_score if is_correct else exam_cfg.scoring_scheme.incorrect_score
        bandit.update_with_outcome(chosen, correct=is_correct, observed_time_ms=response_time_ms)

        # Print step summary
        print(f"{exam_code} Step {i+1:02d} | Q={arm_id} diff={difficulty:.2f} alloc={time_resp.final_time_ms}ms rt={response_time_ms}ms "
              f"stress={stress_level:.2f} load={load_assess.total_load:.2f} p={p:.2f} corr={'✅' if is_correct else '❌'} "
              f"mastery={update_result['new_mastery']:.3f} {'INTV' if intervention else ''}")

    # Session summary
    acc = sum(1 for c in correctness if c)/len(correctness)
    print(f"\n{exam_code} SUMMARY: accuracy={acc:.2%}, avg_rt={int(mean(times_ms))}ms, final_mastery={mastery_series[-1]:.3f}, interventions={interventions}")

    return {
        "accuracy": acc,
        "avg_rt": int(mean(times_ms)),
        "final_mastery": mastery_series[-1],
        "interventions": interventions,
    }

async def main():
    student_id = f"sim_{int(time.time())}"
    concept_id = "kinematics_basic"

    results = {}
    for exam in ["JEE_Mains", "NEET", "JEE_Advanced"]:
        print("\n" + "="*20 + f" {exam} " + "="*20)
        results[exam] = await simulate_session(exam, concept_id, student_id, steps=15)

    # Verify logs written
    repo = BKTRepository()
    logs = repo.client.table("bkt_update_logs").select("student_id, concept_id, previous_mastery, new_mastery, is_correct, created_at").eq("student_id", student_id).execute().data
    print(f"\nLOGS WRITTEN: {len(logs)} rows for student {student_id}")

if __name__ == "__main__":
    asyncio.run(main())
