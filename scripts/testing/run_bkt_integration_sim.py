import sys, os, asyncio

sys.path.append(os.getcwd())
from ai_engine.src.knowledge_tracing.bkt.integration import BKTInterventionIntegration

async def main():
    bi = BKTInterventionIntegration()
    sid = 'student2'
    cid = 'physics_kinematics'

    # 3 correct answers
    for i in range(3):
        res = {'previous_mastery':0.4 + i*0.1,'new_mastery':0.5 + i*0.1}
        _ = await bi.process_response(student_id=sid, concept_id=cid, is_correct=True,
                                      response_time_ms=2000, bkt_model=None, bkt_result=res,
                                      question_difficulty=0.5, time_pressure=0.2)

    # 5 incorrect answers with increasing time pressure
    last = None
    for i in range(5):
        res = {'previous_mastery':0.7 - i*0.1,'new_mastery':0.6 - i*0.1}
        last = await bi.process_response(student_id=sid, concept_id=cid, is_correct=False,
                                         response_time_ms=3000 + i*1000, bkt_model=None, bkt_result=res,
                                         question_difficulty=0.5, time_pressure=0.5 + i*0.1)

    print('last_return:', last)
    key = f"{sid}_{cid}"
    hist = bi.intervention_manager.detector.performance_history.get(key, [])
    print('history_len:', len(hist))
    print('recent_last5_correct_flags:', [1 if i['is_correct'] else 0 for i in hist[-5:]])
    det = bi.intervention_manager.detector.detect_decline(sid, cid)
    print('detect_decline:', det)
    print('intervention_now:', bi.intervention_manager.get_intervention(sid, cid))

if __name__ == '__main__':
    asyncio.run(main())