#!/usr/bin/env python3
import sys
import asyncio
sys.path.insert(0, 'ai_engine/src')

async def test_bkt():
    from bkt_engine import EnhancedBKTService, EnhancedTraceRequest, ExamType
    
    print("=== Testing Enhanced BKT System ===")
    service = EnhancedBKTService()
    
    # Test learning progression
    student_id = 'demo_student'
    concept_id = 'basic_algebra'
    
    interactions = [
        {'correct': False, 'difficulty': 0.3, 'note': 'Initial struggle'},
        {'correct': False, 'difficulty': 0.3, 'note': 'Still learning'},
        {'correct': True, 'difficulty': 0.3, 'note': 'First success'},
        {'correct': True, 'difficulty': 0.4, 'note': 'Building confidence'},
        {'correct': True, 'difficulty': 0.5, 'note': 'Mastering concept'},
    ]
    
    mastery_progression = []
    
    for i, interaction in enumerate(interactions):
        request = EnhancedTraceRequest(
            student_id=student_id,
            concept_id=concept_id,
            is_correct=interaction['correct'],
            difficulty=interaction['difficulty'],
            stress_level=0.4 - i * 0.08,
            cognitive_load=interaction['difficulty'] * 0.8,
            exam_type=ExamType.JEE_MAIN
        )
        
        response = await service.trace_knowledge(request)
        
        if response.success:
            mastery_progression.append(response.new_mastery)
            check = "✅" if interaction['correct'] else "❌"
            print(f"Step {i+1}: {check} | Mastery: {response.previous_mastery:.3f} → {response.new_mastery:.3f} | {interaction['note']}")
        else:
            print(f"Step {i+1}: ERROR - {interaction['note']}")
    
    if mastery_progression:
        print("\n📊 Learning Summary:")
        print(f"Initial mastery: {mastery_progression[0]:.3f}")
        print(f"Final mastery: {mastery_progression[-1]:.3f}")
        improvement = mastery_progression[-1] - mastery_progression[0]
        print(f"Improvement: {improvement:.3f}")
        print(f"BKT Working: {'✅ YES' if improvement > 0 else '❌ NO'}")
    
    # Test system status
    status = await service.get_system_status()
    print(f"\n🔧 System Status: {status['service_status']}")
    print(f"Requests processed: {status['requests_processed']}")
    print(f"Current accuracy: {status['current_accuracy']:.3f}")
    
    # Test transfer learning
    print("\n=== Testing Transfer Learning ===")
    
    # First master basic algebra more
    for i in range(3):
        request = EnhancedTraceRequest(
            student_id=student_id,
            concept_id='basic_algebra',
            is_correct=True,
            difficulty=0.5
        )
        await service.trace_knowledge(request)
    
    # Now try quadratic equations (should benefit from transfer)
    request = EnhancedTraceRequest(
        student_id=student_id,
        concept_id='quadratic_equations',
        is_correct=True,
        difficulty=0.5
    )
    
    response = await service.trace_knowledge(request)
    print(f"Quadratic equations initial mastery: {response.new_mastery:.3f}")
    print(f"Transfer learning: {'✅ YES' if response.new_mastery > 0.2 else '❌ NO'}")
    
    if response.transfer_updates:
        print("Transfer updates:", response.transfer_updates)
    
    return len(mastery_progression) > 0

if __name__ == "__main__":
    try:
        result = asyncio.run(test_bkt())
        print(f"\n🎉 Enhanced BKT System: {'WORKING' if result else 'NEEDS FIXES'}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()