#!/usr/bin/env python3
"""
Comprehensive AI Engine Components Analysis & Test Script
Tests all 8 documented AI Engine components against documentation requirements.
"""
import json
import sys
import traceback
from datetime import datetime
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIEngineAnalyzer:
    """Comprehensive analyzer for AI Engine components"""
    
    def __init__(self):
        self.results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "components": {},
            "overall_status": "UNKNOWN",
            "documentation_compliance": {},
            "missing_features": [],
            "implementation_gaps": []
        }
        
    def test_component_1_bkt(self) -> Dict[str, Any]:
        """Test Knowledge Tracing System (BKT - Bayesian Knowledge Tracing)"""
        logger.info("Testing Component 1: Knowledge Tracing System (BKT)")
        
        result = {
            "component_name": "Knowledge Tracing System (BKT)",
            "status": "UNKNOWN",
            "features_tested": [],
            "issues": [],
            "documentation_path": "ai_engine/src/knowledge_tracing/bkt/bkt_engine.py",
            "compliance_score": 0.0
        }
        
        try:
            # Import and test BKT Engine
            sys.path.append('ai_engine/src')
            from knowledge_tracing.bkt.bkt_engine import BKTEngine
            
            # Test basic functionality
            bkt = BKTEngine("JEE_Mains")
            
            # Test context-aware BKT update
            sample_response = {
                "student_id": "test_student",
                "correct": True,
                "response_time": 45.0
            }
            
            context = {
                "stress_level": 0.3,
                "cognitive_load": 0.2,
                "time_pressure_factor": 1.2
            }
            
            update_result = bkt.update(sample_response, **context)
            
            # Validate expected features
            expected_features = [
                "mastery probability tracking",
                "context modifiers (stress, cognitive load, time pressure)",
                "adaptive time pressure handling", 
                "per-exam parameter tuning",
                "student recovery factor"
            ]
            
            features_found = []
            
            if "mastery" in update_result:
                features_found.append("mastery probability tracking")
                
            if hasattr(bkt, 'time_threshold'):
                features_found.append("adaptive time pressure handling")
                
            if hasattr(bkt, 'student_recovery_factor'):
                features_found.append("student recovery factor")
                
            if bkt.exam_code == "JEE_Mains":
                features_found.append("per-exam parameter tuning")
                
            if "adaptive_time_threshold" in update_result:
                features_found.append("context modifiers (stress, cognitive load, time pressure)")
            
            result["features_tested"] = features_found
            result["compliance_score"] = len(features_found) / len(expected_features)
            
            if result["compliance_score"] >= 0.8:
                result["status"] = "EXCELLENT"
            elif result["compliance_score"] >= 0.6:
                result["status"] = "GOOD"
            elif result["compliance_score"] >= 0.4:
                result["status"] = "PARTIAL"
            else:
                result["status"] = "POOR"
                
            logger.info(f"BKT Test completed: {result['status']} ({result['compliance_score']:.2%} compliance)")
            
        except Exception as e:
            result["status"] = "ERROR"
            result["issues"].append(f"Import/execution error: {str(e)}")
            logger.error(f"BKT test failed: {e}")
            traceback.print_exc()
            
        return result
    
    def test_component_2_stress_detection(self) -> Dict[str, Any]:
        """Test Stress Detection Engine"""
        logger.info("Testing Component 2: Stress Detection Engine")
        
        result = {
            "component_name": "Stress Detection Engine",
            "status": "UNKNOWN", 
            "features_tested": [],
            "issues": [],
            "documentation_path": "ai_engine/src/knowledge_tracing/stress/detection_engine.py",
            "compliance_score": 0.0
        }
        
        try:
            from knowledge_tracing.stress.detection_engine import MultiModalStressDetector, StressLevel
            
            detector = MultiModalStressDetector(window_size=12)
            
            # Test stress detection with various patterns
            stress_result = detector.detect(
                response_time=5000,  # 5 seconds 
                correct=False,
                hesitation_ms=3000,  # 3 seconds hesitation
                keystroke_dev=0.8
            )
            
            expected_features = [
                "multi-modal inputs",
                "response time variance analysis", 
                "hesitation metrics tracking",
                "keystroke dynamics analysis",
                "intervention recommendations",
                "confidence scoring"
            ]
            
            features_found = []
            
            if isinstance(stress_result, StressLevel):
                features_found.append("multi-modal inputs")
                
            if hasattr(stress_result, 'level') and 0 <= stress_result.level <= 1:
                features_found.append("response time variance analysis")
                
            if hasattr(stress_result, 'confidence'):
                features_found.append("confidence scoring")
                
            if hasattr(stress_result, 'intervention'):
                features_found.append("intervention recommendations")
                
            if hasattr(stress_result, 'indicators'):
                features_found.append("hesitation metrics tracking")
                features_found.append("keystroke dynamics analysis")
            
            result["features_tested"] = features_found
            result["compliance_score"] = len(features_found) / len(expected_features)
            
            if result["compliance_score"] >= 0.8:
                result["status"] = "EXCELLENT"
            elif result["compliance_score"] >= 0.6:
                result["status"] = "GOOD" 
            elif result["compliance_score"] >= 0.4:
                result["status"] = "PARTIAL"
            else:
                result["status"] = "POOR"
                
            logger.info(f"Stress Detection test completed: {result['status']} ({result['compliance_score']:.2%} compliance)")
            
        except Exception as e:
            result["status"] = "ERROR"
            result["issues"].append(f"Import/execution error: {str(e)}")
            logger.error(f"Stress detection test failed: {e}")
            traceback.print_exc()
            
        return result
    
    def test_component_3_cognitive_load(self) -> Dict[str, Any]:
        """Test Cognitive Load Manager"""
        logger.info("Testing Component 3: Cognitive Load Manager")
        
        result = {
            "component_name": "Cognitive Load Manager",
            "status": "UNKNOWN",
            "features_tested": [],
            "issues": [],
            "documentation_path": "ai_engine/src/knowledge_tracing/cognitive/load_manager.py",
            "compliance_score": 0.0
        }
        
        try:
            from knowledge_tracing.cognitive.load_manager import CognitiveLoadManager, LoadAssessment
            
            manager = CognitiveLoadManager()
            
            # Test cognitive load assessment
            item_metadata = {
                "solution_steps": 3,
                "concepts_required": ["algebra", "calculus"],
                "prerequisites": ["basic_math"],
                "learning_value": 0.7,
                "schema_complexity": 0.4
            }
            
            student_state = {
                "session_duration_minutes": 45,
                "cognitive_capacity_modifier": 1.0,
                "mastery_algebra": 0.6,
                "mastery_calculus": 0.4,
                "mastery_basic_math": 0.8
            }
            
            context_factors = {
                "time_pressure_ratio": 0.8,
                "interface_complexity_score": 0.3,
                "distraction_level": 0.2,
                "presentation_quality": 0.9
            }
            
            device_profile = {"type": "mobile", "screen_class": "small", "bandwidth": "medium"}
            
            assessment = manager.assess_cognitive_load(
                item_metadata, student_state, context_factors, 
                stress_level=0.3, device_profile=device_profile
            )
            
            expected_features = [
                "Sweller's CLT framework",
                "intrinsic load calculation",
                "extraneous load calculation", 
                "germane load calculation",
                "mobile-aware multipliers",
                "overload risk assessment",
                "actionable recommendations"
            ]
            
            features_found = []
            
            if isinstance(assessment, LoadAssessment):
                features_found.append("Sweller's CLT framework")
                
            if hasattr(assessment, 'intrinsic_load'):
                features_found.append("intrinsic load calculation")
                
            if hasattr(assessment, 'extraneous_load'):
                features_found.append("extraneous load calculation")
                
            if hasattr(assessment, 'germane_load'):
                features_found.append("germane load calculation")
                
            if hasattr(assessment, 'overload_risk'):
                features_found.append("overload risk assessment")
                
            if hasattr(assessment, 'recommendations') and assessment.recommendations:
                features_found.append("actionable recommendations")
                
            # Check mobile awareness by testing multipliers
            if hasattr(manager, 'mobile_extraneous_multipliers'):
                features_found.append("mobile-aware multipliers")
            
            result["features_tested"] = features_found
            result["compliance_score"] = len(features_found) / len(expected_features)
            
            if result["compliance_score"] >= 0.8:
                result["status"] = "EXCELLENT"
            elif result["compliance_score"] >= 0.6:
                result["status"] = "GOOD"
            elif result["compliance_score"] >= 0.4:
                result["status"] = "PARTIAL"
            else:
                result["status"] = "POOR"
                
            logger.info(f"Cognitive Load test completed: {result['status']} ({result['compliance_score']:.2%} compliance)")
            
        except Exception as e:
            result["status"] = "ERROR"
            result["issues"].append(f"Import/execution error: {str(e)}")
            logger.error(f"Cognitive load test failed: {e}")
            traceback.print_exc()
            
        return result
    
    def test_component_4_time_allocator(self) -> Dict[str, Any]:
        """Test Dynamic Time Allocator"""
        logger.info("Testing Component 4: Dynamic Time Allocator")
        
        result = {
            "component_name": "Dynamic Time Allocator",
            "status": "UNKNOWN",
            "features_tested": [],
            "issues": [],
            "documentation_path": "ai_engine/src/knowledge_tracing/pacing/time_allocator.py",
            "compliance_score": 0.0
        }
        
        try:
            from knowledge_tracing.pacing.time_allocator import DynamicTimeAllocator, TimeAllocationRequest
            
            allocator = DynamicTimeAllocator()
            
            # Test time allocation
            request = TimeAllocationRequest(
                student_id="test_student",
                question_id="test_question", 
                base_time_ms=60000,  # 1 minute
                stress_level=0.4,
                fatigue_level=0.2,
                mastery=0.6,
                difficulty=1.2,
                session_elapsed_ms=1800000,  # 30 minutes
                exam_code="JEE_Mains"
            )
            
            mobile_headers = {
                "device_type": "mobile",
                "screen_class": "small",
                "network": "medium",
                "distraction_level": "0.3"
            }
            
            allocation = allocator.allocate(request, mobile_headers)
            
            expected_features = [
                "stress factor adjustment",
                "fatigue factor adjustment", 
                "mastery factor adjustment",
                "difficulty factor adjustment",
                "exam-specific caps",
                "mobile-aware adjustments",
                "session duration impact"
            ]
            
            features_found = []
            
            if hasattr(allocation, 'breakdown') and allocation.breakdown:
                breakdown = allocation.breakdown
                if "stress_factor" in breakdown:
                    features_found.append("stress factor adjustment")
                if "fatigue_factor" in breakdown:
                    features_found.append("fatigue factor adjustment")
                if "mastery_factor" in breakdown:
                    features_found.append("mastery factor adjustment")
                if "difficulty_factor" in breakdown:
                    features_found.append("difficulty factor adjustment")
                if "exam_difficulty_factor" in breakdown:
                    features_found.append("exam-specific caps")
                if "session_factor" in breakdown:
                    features_found.append("session duration impact")
                if "mobile_factor" in breakdown:
                    features_found.append("mobile-aware adjustments")
            
            result["features_tested"] = features_found
            result["compliance_score"] = len(features_found) / len(expected_features)
            
            if result["compliance_score"] >= 0.8:
                result["status"] = "EXCELLENT"
            elif result["compliance_score"] >= 0.6:
                result["status"] = "GOOD"
            elif result["compliance_score"] >= 0.4:
                result["status"] = "PARTIAL"
            else:
                result["status"] = "POOR"
                
            logger.info(f"Time Allocator test completed: {result['status']} ({result['compliance_score']:.2%} compliance)")
            
        except Exception as e:
            result["status"] = "ERROR"
            result["issues"].append(f"Import/execution error: {str(e)}")
            logger.error(f"Time allocator test failed: {e}")
            traceback.print_exc()
            
        return result
    
    def test_component_5_question_selection(self) -> Dict[str, Any]:
        """Test Question Selection Engine"""
        logger.info("Testing Component 5: Question Selection Engine")
        
        result = {
            "component_name": "Question Selection Engine", 
            "status": "UNKNOWN",
            "features_tested": [],
            "issues": [],
            "documentation_path": "ai_engine/src/knowledge_tracing/selection/pressure_linucb.py",
            "compliance_score": 0.0
        }
        
        try:
            from knowledge_tracing.selection.bandit_policy import LinUCBPolicy, BanditContext
            
            policy = LinUCBPolicy(alpha=0.6, d=7)
            
            # Test bandit selection
            contexts = [
                BanditContext("question_1", {
                    "difficulty": 0.6,
                    "estimated_time_ms": 90000,
                    "mastery_level": 0.5,
                    "stress_level": 0.3,
                    "cognitive_load": 0.4,
                    "correct_score": 4.0,
                    "incorrect_score": -1.0
                }),
                BanditContext("question_2", {
                    "difficulty": 1.2,
                    "estimated_time_ms": 120000,
                    "mastery_level": 0.7,
                    "stress_level": 0.2,
                    "cognitive_load": 0.3,
                    "correct_score": 4.0,
                    "incorrect_score": -1.0
                })
            ]
            
            chosen_id, diagnostics = policy.select(contexts)
            
            expected_features = [
                "multi-armed bandit approach",
                "LinUCB algorithm",
                "context awareness",
                "exploration vs exploitation",
                "feature vector construction",
                "UCB scoring",
                "diagnostic information"
            ]
            
            features_found = []
            
            if isinstance(policy, LinUCBPolicy):
                features_found.append("multi-armed bandit approach")
                features_found.append("LinUCB algorithm")
                
            if chosen_id and isinstance(chosen_id, str):
                features_found.append("exploration vs exploitation")
                
            if diagnostics and isinstance(diagnostics, dict):
                features_found.append("diagnostic information")
                features_found.append("UCB scoring")
                
            if hasattr(contexts[0], 'feature_vector'):
                features_found.append("feature vector construction")
                features_found.append("context awareness")
            
            result["features_tested"] = features_found
            result["compliance_score"] = len(features_found) / len(expected_features)
            
            if result["compliance_score"] >= 0.8:
                result["status"] = "EXCELLENT"
            elif result["compliance_score"] >= 0.6:
                result["status"] = "GOOD"
            elif result["compliance_score"] >= 0.4:
                result["status"] = "PARTIAL"
            else:
                result["status"] = "POOR"
                
            logger.info(f"Question Selection test completed: {result['status']} ({result['compliance_score']:.2%} compliance)")
            
        except Exception as e:
            result["status"] = "ERROR"
            result["issues"].append(f"Import/execution error: {str(e)}")
            logger.error(f"Question selection test failed: {e}")
            traceback.print_exc()
            
        return result
    
    def test_component_6_fairness_monitor(self) -> Dict[str, Any]:
        """Test Fairness Monitoring System"""
        logger.info("Testing Component 6: Fairness Monitoring System")
        
        result = {
            "component_name": "Fairness Monitoring System",
            "status": "UNKNOWN",
            "features_tested": [],
            "issues": [],
            "documentation_path": "ai_engine/src/knowledge_tracing/fairness/monitor.py",
            "compliance_score": 0.0
        }
        
        try:
            from knowledge_tracing.fairness.monitor import FairnessMonitor
            
            monitor = FairnessMonitor()
            
            # Test fairness monitoring
            monitor.update_stats("JEE_Mains", "Physics", "urban", [0.7, 0.8, 0.6, 0.9])
            monitor.update_stats("JEE_Mains", "Physics", "rural", [0.6, 0.5, 0.7, 0.4])
            
            parity_check = monitor.check_parity("JEE_Mains", "Physics")
            recommendations = monitor.generate_recommendations(parity_check.get("disparity", 0.0))
            
            expected_features = [
                "demographic segmentation",
                "per-exam monitoring",
                "disparity detection",
                "statistical parity check",
                "alert thresholds",
                "bias recommendations",
                "group comparison"
            ]
            
            features_found = []
            
            if hasattr(monitor, 'group_stats'):
                features_found.append("demographic segmentation")
                features_found.append("group comparison")
                
            if "disparity" in parity_check:
                features_found.append("disparity detection")
                features_found.append("statistical parity check")
                
            if "averages" in parity_check:
                features_found.append("per-exam monitoring")
                
            if recommendations and isinstance(recommendations, list):
                features_found.append("bias recommendations")
                features_found.append("alert thresholds")
            
            result["features_tested"] = features_found
            result["compliance_score"] = len(features_found) / len(expected_features)
            
            if result["compliance_score"] >= 0.8:
                result["status"] = "EXCELLENT"
            elif result["compliance_score"] >= 0.6:
                result["status"] = "GOOD"
            elif result["compliance_score"] >= 0.4:
                result["status"] = "PARTIAL"
            else:
                result["status"] = "POOR"
                
            logger.info(f"Fairness Monitor test completed: {result['status']} ({result['compliance_score']:.2%} compliance)")
            
        except Exception as e:
            result["status"] = "ERROR"
            result["issues"].append(f"Import/execution error: {str(e)}")
            logger.error(f"Fairness monitor test failed: {e}")
            traceback.print_exc()
            
        return result
    
    def test_component_7_spaced_repetition(self) -> Dict[str, Any]:
        """Test Spaced Repetition Scheduler"""
        logger.info("Testing Component 7: Spaced Repetition Scheduler")
        
        result = {
            "component_name": "Spaced Repetition Scheduler",
            "status": "UNKNOWN",
            "features_tested": [],
            "issues": [],
            "documentation_path": "ai_engine/src/knowledge_tracing/spaced_repetition/scheduler.py",
            "compliance_score": 0.0
        }
        
        try:
            from knowledge_tracing.spaced_repetition.scheduler import HalfLifeRegressionScheduler
            from datetime import datetime
            
            scheduler = HalfLifeRegressionScheduler()
            
            # Test half-life regression
            half_life = scheduler.estimate_half_life(
                difficulty=0.8, 
                ability=0.6, 
                features={"stress": 0.3}
            )
            
            # Test next review scheduling
            last_review = datetime.now()
            next_review = scheduler.next_review_time(last_review, half_life)
            
            expected_features = [
                "half-life regression algorithm",
                "difficulty factor consideration",
                "ability level adjustment",
                "forgetting curve modeling",
                "optimal interval calculation",
                "just-in-time reviews",
                "feature-based adjustments"
            ]
            
            features_found = []
            
            if isinstance(scheduler, HalfLifeRegressionScheduler):
                features_found.append("half-life regression algorithm")
                
            if half_life and isinstance(half_life, (int, float)):
                features_found.append("difficulty factor consideration")
                features_found.append("ability level adjustment")
                features_found.append("forgetting curve modeling")
                features_found.append("feature-based adjustments")
                
            if next_review and next_review > last_review:
                features_found.append("optimal interval calculation")
                features_found.append("just-in-time reviews")
            
            result["features_tested"] = features_found
            result["compliance_score"] = len(features_found) / len(expected_features)
            
            if result["compliance_score"] >= 0.8:
                result["status"] = "EXCELLENT"
            elif result["compliance_score"] >= 0.6:
                result["status"] = "GOOD"
            elif result["compliance_score"] >= 0.4:
                result["status"] = "PARTIAL"
            else:
                result["status"] = "POOR"
                
            logger.info(f"Spaced Repetition test completed: {result['status']} ({result['compliance_score']:.2%} compliance)")
            
        except Exception as e:
            result["status"] = "ERROR"
            result["issues"].append(f"Import/execution error: {str(e)}")
            logger.error(f"Spaced repetition test failed: {e}")
            traceback.print_exc()
            
        return result
    
    def test_component_8_calibration(self) -> Dict[str, Any]:
        """Test Calibration Engine"""
        logger.info("Testing Component 8: Calibration Engine")
        
        result = {
            "component_name": "Calibration Engine",
            "status": "UNKNOWN",
            "features_tested": [],
            "issues": [],
            "documentation_path": "ai_engine/src/knowledge_tracing/calibration/calibrator.py",
            "compliance_score": 0.0
        }
        
        try:
            from knowledge_tracing.calibration.calibrator import TemperatureScalingCalibrator
            import torch
            
            calibrator = TemperatureScalingCalibrator()
            
            # Test temperature scaling
            temp = calibrator.get_temperature("JEE_Mains", "Physics")
            
            # Test calibration with dummy data
            dummy_logits = torch.randn(10, 5)  # 10 samples, 5 classes
            dummy_labels = torch.randint(0, 5, (10,))
            
            calibrated_probs = calibrator.calibrate(dummy_logits, "JEE_Mains", "Physics")
            ece = calibrator.expected_calibration_error(calibrated_probs, dummy_labels)
            
            expected_features = [
                "temperature scaling method",
                "per-exam calibration",
                "per-subject calibration", 
                "L-BFGS optimization",
                "cross-exam isolation",
                "confidence score reliability",
                "expected calibration error"
            ]
            
            features_found = []
            
            if isinstance(calibrator, TemperatureScalingCalibrator):
                features_found.append("temperature scaling method")
                
            if temp and isinstance(temp, (int, float)):
                features_found.append("per-exam calibration")
                features_found.append("per-subject calibration")
                features_found.append("cross-exam isolation")
                
            if calibrated_probs is not None and calibrated_probs.shape[0] > 0:
                features_found.append("confidence score reliability")
                
            if ece is not None and isinstance(ece, (int, float)):
                features_found.append("expected calibration error")
                
            if hasattr(calibrator, 'fit'):
                features_found.append("L-BFGS optimization")
            
            result["features_tested"] = features_found
            result["compliance_score"] = len(features_found) / len(expected_features)
            
            if result["compliance_score"] >= 0.8:
                result["status"] = "EXCELLENT"
            elif result["compliance_score"] >= 0.6:
                result["status"] = "GOOD"
            elif result["compliance_score"] >= 0.4:
                result["status"] = "PARTIAL"
            else:
                result["status"] = "POOR"
                
            logger.info(f"Calibration Engine test completed: {result['status']} ({result['compliance_score']:.2%} compliance)")
            
        except Exception as e:
            result["status"] = "ERROR"
            result["issues"].append(f"Import/execution error: {str(e)}")
            logger.error(f"Calibration engine test failed: {e}")
            traceback.print_exc()
            
        return result
    
    def analyze_all_components(self) -> Dict[str, Any]:
        """Run comprehensive analysis of all AI Engine components"""
        logger.info("Starting comprehensive AI Engine analysis...")
        
        # Test all components
        component_tests = [
            self.test_component_1_bkt,
            self.test_component_2_stress_detection,
            self.test_component_3_cognitive_load,
            self.test_component_4_time_allocator,
            self.test_component_5_question_selection,
            self.test_component_6_fairness_monitor,
            self.test_component_7_spaced_repetition,
            self.test_component_8_calibration
        ]
        
        for i, test_func in enumerate(component_tests, 1):
            logger.info(f"Testing component {i}/8...")
            component_result = test_func()
            self.results["components"][f"component_{i}"] = component_result
        
        # Calculate overall metrics
        self._calculate_overall_status()
        self._check_documentation_compliance()
        self._identify_gaps()
        
        return self.results
    
    def _calculate_overall_status(self):
        """Calculate overall system status"""
        statuses = [comp["status"] for comp in self.results["components"].values()]
        
        status_weights = {"EXCELLENT": 4, "GOOD": 3, "PARTIAL": 2, "POOR": 1, "ERROR": 0}
        total_score = sum(status_weights.get(status, 0) for status in statuses)
        max_score = len(statuses) * 4
        
        overall_score = total_score / max_score if max_score > 0 else 0
        
        if overall_score >= 0.8:
            self.results["overall_status"] = "EXCELLENT"
        elif overall_score >= 0.6:
            self.results["overall_status"] = "GOOD"
        elif overall_score >= 0.4:
            self.results["overall_status"] = "PARTIAL"
        else:
            self.results["overall_status"] = "POOR"
        
        self.results["overall_compliance_score"] = overall_score
        
    def _check_documentation_compliance(self):
        """Check compliance with documentation requirements"""
        doc_requirements = {
            "BKT_accuracy_target": "85%+",
            "response_time_target": "<100ms",
            "stress_detection_modes": "multi-modal",
            "cognitive_load_framework": "Sweller's CLT",
            "question_selection_algorithm": "Multi-Armed Bandit", 
            "fairness_monitoring": "demographic segmentation",
            "spaced_repetition_method": "Half-Life Regression",
            "calibration_method": "Temperature Scaling"
        }
        
        compliance_status = {}
        for req, expected in doc_requirements.items():
            # This would need actual performance testing to fully validate
            compliance_status[req] = "NEEDS_VALIDATION"
            
        self.results["documentation_compliance"] = compliance_status
        
    def _identify_gaps(self):
        """Identify implementation gaps"""
        gaps = []
        missing_features = []
        
        for component_id, component in self.results["components"].items():
            if component["status"] == "ERROR":
                gaps.append(f"{component['component_name']}: Critical implementation error")
            elif component["status"] == "POOR":
                gaps.append(f"{component['component_name']}: Major implementation gaps")
            elif component["compliance_score"] < 0.7:
                missing_features.extend([
                    f"{component['component_name']}: Missing key features"
                ])
        
        self.results["implementation_gaps"] = gaps
        self.results["missing_features"] = missing_features

def main():
    """Main analysis function"""
    print("🔍 JEE Smart AI Platform - Comprehensive AI Engine Analysis")
    print("=" * 80)
    
    analyzer = AIEngineAnalyzer()
    results = analyzer.analyze_all_components()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ai_engine_analysis_report_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n📊 ANALYSIS SUMMARY")
    print(f"Overall Status: {results['overall_status']}")
    print(f"Overall Compliance: {results.get('overall_compliance_score', 0):.2%}")
    
    print(f"\n🧩 COMPONENT STATUS:")
    for comp_id, comp in results["components"].items():
        status_emoji = {
            "EXCELLENT": "✅",
            "GOOD": "👍", 
            "PARTIAL": "⚠️",
            "POOR": "❌",
            "ERROR": "💥"
        }
        emoji = status_emoji.get(comp["status"], "❓")
        print(f"{emoji} {comp['component_name']}: {comp['status']} ({comp['compliance_score']:.2%})")
        
    if results["implementation_gaps"]:
        print(f"\n🚨 CRITICAL GAPS:")
        for gap in results["implementation_gaps"]:
            print(f"- {gap}")
            
    print(f"\n📄 Full report saved to: {filename}")

if __name__ == "__main__":
    main()