#!/usr/bin/env python3
import os, sys
# Add ai_engine/src to path
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src_path = os.path.join(ROOT, 'ai_engine', 'src')
print('SRC_PATH', src_path, 'exists', os.path.exists(src_path))
sys.path.insert(0, ROOT)
import sys as _sys
print('SYS_PATH_HEAD', _sys.path[:3])

from ai_engine.src.knowledge_tracing.pacing.time_allocator import DynamicTimeAllocator, TimeAllocationRequest
from ai_engine.src.knowledge_tracing.selection.candidate_provider import CandidateProvider

# Time allocator sanity: caps per exam
alloc = DynamicTimeAllocator()
for exam in ['JEE_Mains','NEET','JEE_Advanced']:
    req = TimeAllocationRequest(student_id='s', question_id='q', base_time_ms=999999, stress_level=0.3,
                                fatigue_level=0.2, mastery=0.4, difficulty=0.8, session_elapsed_ms=3600000,
                                exam_code=exam)
    resp = alloc.allocate(req)
    print('ALLOC', exam, resp.final_time_ms)

# Candidate gating sanity: by default mock datasource emits A(0.8),B(0.5),C(0.3) with mastery=0.6
# To test gating, we simulate low mastery by adjusting returned items would require a datasource; here we at least
# check that default includes all arms and relies on mastery feature per item.
cp = CandidateProvider(datasource=None, exam_code='JEE_Mains')
cands = cp.build_candidates(student_id='s', concept_id='c', stress_level=0.1, cognitive_load=0.1)
print('CANDS', [c['arm_id'] for c in cands])
