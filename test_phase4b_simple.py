#!/usr/bin/env python3
"""
Simplified Phase 4B Component Test
Tests what's available and identifies missing components
"""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add ai_engine to path
ai_engine_path = os.path.join(os.getcwd(), 'ai_engine', 'src')
if ai_engine_path not in sys.path:
    sys.path.insert(0, ai_engine_path)

print("🧪 PHASE 4B COMPONENT AVAILABILITY TEST")
print("="*50)

# Test component imports
components = {}

# Test Time Allocator
print("\n1. Testing Time Allocator Component...")
try:
    from knowledge_tracing.pacing.time_allocator import DynamicTimeAllocator, TimeAllocationRequest
    allocator = DynamicTimeAllocator()
    
    # Test basic functionality
    request = TimeAllocationRequest(
        student_id="test_student",
        question_id="q_001", 
        base_time_ms=30000,
        stress_level=0.3,
        fatigue_level=0.2,
        mastery=0.7,
        difficulty=1.0,
        session_elapsed_ms=600000
    )
    
    result = allocator.allocate(request)
    
    components['time_allocator'] = {
        'status': 'available',
        'test_result': {
            'allocated_time_ms': result.final_time_ms,
            'factor': result.factor,
            'breakdown': result.breakdown
        }
    }
    print(f"  ✅ Time Allocator: WORKING")
    print(f"    📊 Result: {result.final_time_ms}ms (factor: {result.factor})")
    
except Exception as e:
    components['time_allocator'] = {'status': 'error', 'error': str(e)}
    print(f"  ❌ Time Allocator: ERROR - {e}")

# Test Cognitive Load Manager  
print("\n2. Testing Cognitive Load Manager...")
try:
    from knowledge_tracing.congnitive.load_manager import CognitiveLoadManager
    load_manager = CognitiveLoadManager()
    
    # Test load assessment
    assessment = load_manager.assess(
        problem_steps=4,
        concept_mastery=0.6,
        prerequisites_gap=0.3,
        time_pressure=0.4,
        interface_score=0.2,
        distractions=0.1,
        stress_level=0.3,
        fatigue_level=0.2
    )
    
    components['cognitive_load'] = {
        'status': 'available',
        'test_result': {
            'total_load': assessment.total_load,
            'overload_risk': assessment.overload_risk,
            'recommendations': assessment.recommendations
        }
    }
    print(f"  ✅ Cognitive Load Manager: WORKING")
    print(f"    📊 Result: Total Load: {assessment.total_load:.2f}, Risk: {assessment.overload_risk:.2f}")
    
except Exception as e:
    components['cognitive_load'] = {'status': 'error', 'error': str(e)}
    print(f"  ❌ Cognitive Load Manager: ERROR - {e}")

# Test Stress Detection
print("\n3. Testing Stress Detection Engine...")
try:
    from knowledge_tracing.stress.detection_engine import MultiModalStressDetector
    detector = MultiModalStressDetector(window_size=5)
    
    # Test stress detection
    stress_result = detector.detect(
        response_time=2500.0,
        correct=False,
        hesitation_ms=1500.0,
        keystroke_dev=0.4
    )
    
    components['stress_detection'] = {
        'status': 'available',
        'test_result': {
            'stress_level': stress_result.level,
            'confidence': stress_result.confidence,
            'indicators': stress_result.indicators,
            'intervention': stress_result.intervention
        }
    }
    print(f"  ✅ Stress Detection: WORKING")
    print(f"    📊 Result: Stress: {stress_result.level:.2f}, Intervention: {stress_result.intervention}")
    
except Exception as e:
    components['stress_detection'] = {'status': 'error', 'error': str(e)}
    print(f"  ❌ Stress Detection: ERROR - {e}")

# Test Enhanced BKT
print("\n4. Testing Enhanced BKT System...")
try:
    from enhanced_bkt_system import PedagogicalBKT
    bkt = PedagogicalBKT()
    
    # Test BKT update
    result = bkt.update_mastery(
        student_id="test_student",
        topic="algebra_basics",
        is_correct=True,
        difficulty=1.0,
        response_time_ms=2000,
        confidence_score=0.8
    )
    
    components['bkt_system'] = {
        'status': 'available',
        'test_result': {
            'previous_mastery': result['previous_mastery'],
            'new_mastery': result['new_mastery']
        }
    }
    print(f"  ✅ Enhanced BKT: WORKING")
    print(f"    📊 Result: Mastery: {result['previous_mastery']:.3f} → {result['new_mastery']:.3f}")
    
except Exception as e:
    components['bkt_system'] = {'status': 'error', 'error': str(e)}
    print(f"  ❌ Enhanced BKT: ERROR - {e}")

# Test Pressure-Aware LinUCB
print("\n5. Testing Pressure-Aware Selection...")
try:
    from knowledge_tracing.selection.pressure_linucb import PressureAwareLinUCB
    from knowledge_tracing.selection.bandit_policy import BanditContext
    
    # This will likely fail due to missing dependencies
    # but let's see what we get
    components['pressure_selection'] = {'status': 'available'}
    print(f"  ✅ Pressure-Aware Selection: AVAILABLE")
    
except Exception as e:
    components['pressure_selection'] = {'status': 'error', 'error': str(e)}
    print(f"  ❌ Pressure-Aware Selection: ERROR - {e}")

# Test Gemini API Manager
print("\n6. Testing Gemini API Manager...")
try:
    from gemini_api_manager import GeminiAPIManager
    
    api_keys = [
        "AIzaSyC7lW99lDFrBFS3e5mYxZNJzIn4tyFNFE",
        "AIzaSyAq7dfXdFagW2j2AdbfgCkj8s6nahUMjOg", 
        "AIzaSyA5SqoM2v_9VFG2O6DbxBGKftm3onsHGpM",
        "AIzaSyAuiUoHva-1iZFJh2C4asr9pTL7gQLNci4"
    ]
    
    manager = GeminiAPIManager(api_keys)
    stats = manager.get_usage_stats()
    
    components['api_manager'] = {
        'status': 'available',
        'test_result': {
            'total_keys': stats['total_keys'],
            'active_keys': stats['active_keys']
        }
    }
    print(f"  ✅ Gemini API Manager: WORKING")
    print(f"    📊 Result: {stats['active_keys']}/{stats['total_keys']} keys active")
    
    # Print current usage
    manager.print_usage_report()
    
except Exception as e:
    components['api_manager'] = {'status': 'error', 'error': str(e)}
    print(f"  ❌ Gemini API Manager: ERROR - {e}")

# Test Database Migration
print("\n7. Testing Database Migration...")
try:
    migration_file = "database/migrations/008_phase4b_add_pacing_tables.sql"
    if os.path.exists(migration_file):
        with open(migration_file, 'r') as f:
            migration_content = f.read()
        
        components['database_migration'] = {
            'status': 'available',
            'test_result': {
                'file_exists': True,
                'content_length': len(migration_content),
                'tables_defined': migration_content.count('CREATE TABLE')
            }
        }
        print(f"  ✅ Database Migration: AVAILABLE")
        print(f"    📊 Migration defines {migration_content.count('CREATE TABLE')} new tables")
    else:
        components['database_migration'] = {'status': 'missing', 'error': 'Migration file not found'}
        print(f"  ❌ Database Migration: MISSING FILE")
        
except Exception as e:
    components['database_migration'] = {'status': 'error', 'error': str(e)}
    print(f"  ❌ Database Migration: ERROR - {e}")

# Generate Summary Report
print("\n" + "="*60)
print("📊 PHASE 4B COMPONENT SUMMARY")
print("="*60)

available_components = [k for k, v in components.items() if v['status'] == 'available']
error_components = [k for k, v in components.items() if v['status'] == 'error']
missing_components = [k for k, v in components.items() if v['status'] == 'missing']

print(f"✅ Available Components: {len(available_components)}")
for comp in available_components:
    print(f"  • {comp}")

if error_components:
    print(f"\n❌ Components with Errors: {len(error_components)}")
    for comp in error_components:
        print(f"  • {comp}: {components[comp]['error'][:80]}...")

if missing_components:
    print(f"\n⚠️ Missing Components: {len(missing_components)}")
    for comp in missing_components:
        print(f"  • {comp}: {components[comp]['error']}")

# Integration Test
print(f"\n🔗 INTEGRATION TEST")
print("="*30)

if len(available_components) >= 3:
    print("✅ Sufficient components for integration testing")
    
    # Try a simple workflow
    try:
        if 'time_allocator' in available_components and 'cognitive_load' in available_components:
            print("\n🧪 Running Simple Integration Test...")
            
            # Time allocation
            from knowledge_tracing.pacing.time_allocator import DynamicTimeAllocator, TimeAllocationRequest
            allocator = DynamicTimeAllocator()
            
            time_req = TimeAllocationRequest(
                student_id="integration_test",
                question_id="q_integration",
                base_time_ms=25000,
                stress_level=0.4,
                fatigue_level=0.3,
                mastery=0.6,
                difficulty=1.2,
                session_elapsed_ms=900000
            )
            
            time_result = allocator.allocate(time_req)
            
            # Cognitive load  
            from knowledge_tracing.congnitive.load_manager import CognitiveLoadManager
            load_manager = CognitiveLoadManager()
            
            load_result = load_manager.assess(
                problem_steps=5,
                concept_mastery=0.6,
                prerequisites_gap=0.3,
                time_pressure=0.4,
                interface_score=0.2,
                distractions=0.1,
                stress_level=0.4,
                fatigue_level=0.3
            )
            
            print(f"  ✅ Integration Test PASSED")
            print(f"    Time Allocated: {time_result.final_time_ms}ms")
            print(f"    Cognitive Load: {load_result.total_load:.2f}")
            print(f"    Overload Risk: {load_result.overload_risk:.2f}")
            
            integration_success = True
            
        else:
            print("⚠️ Insufficient components for integration test")
            integration_success = False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        integration_success = False
        
else:
    print("❌ Insufficient components available")
    integration_success = False

# Save detailed report
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report_file = f"phase4b_component_test_{timestamp}.json"

report = {
    'timestamp': datetime.now().isoformat(),
    'summary': {
        'total_components_tested': len(components),
        'available_components': len(available_components),
        'error_components': len(error_components),
        'missing_components': len(missing_components),
        'integration_test_passed': integration_success
    },
    'component_details': components,
    'recommendations': []
}

# Generate recommendations
if error_components:
    report['recommendations'].append("Fix component errors before proceeding with full Phase 4B testing")

if missing_components:
    report['recommendations'].append("Implement missing components for complete Phase 4B functionality")

if len(available_components) >= 4:
    report['recommendations'].append("Ready for comprehensive Phase 4B integration testing")

with open(report_file, 'w') as f:
    json.dump(report, f, indent=2, default=str)

print(f"\n📋 Detailed report saved to: {report_file}")

# Final Status
print(f"\n🎯 PHASE 4B READINESS STATUS")
print("="*40)

if integration_success and len(available_components) >= 4:
    status = "🟢 READY FOR TESTING"
    readiness = "High"
elif len(available_components) >= 3:
    status = "🟡 PARTIAL READINESS"  
    readiness = "Medium"
else:
    status = "🔴 NEEDS WORK"
    readiness = "Low"

print(f"Status: {status}")
print(f"Readiness: {readiness}")
print(f"Components Available: {len(available_components)}/{len(components)}")

if integration_success:
    print("\n🚀 Recommendation: Proceed with comprehensive Phase 4B simulation testing")
else:
    print("\n⚙️ Recommendation: Fix component issues before full testing")

print("\n✅ Phase 4B Component Test Complete!")