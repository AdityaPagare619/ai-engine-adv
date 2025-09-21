# Phase 4B AI Engine Testing Manual
**Version:** Phase 4B - Universal Exam Engine  
**Date:** September 21, 2025  
**Target:** QA/Testing Team  

## Executive Summary

This manual guides the testing team through validation of the Phase 4B AI Engine upgrade, which transforms the previous JEE-only system into a universal platform supporting JEE Mains, NEET, and JEE Advanced exams with enhanced mobile support and integrated AI components.

**Key Changes:**
- Universal exam support (JEE, NEET, Advanced) 
- Integrated AI pipeline (Stress → Load → Pacing → BKT → Selection)
- Mobile-first design with device-aware algorithms
- Admin-configurable marking schemes and time constraints
- Per-exam calibration and fairness monitoring

## Prerequisites

### System Requirements
- Python 3.8+ with pip installed
- Git for version control
- PostMan or curl for API testing
- Web browser for admin interface testing

### Environment Setup
1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd smart-ai-platform
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables**
   ```bash
   export KT_MIN_TIME_FACTOR=0.5
   export KT_MAX_TIME_FACTOR=2.0
   export PYTHONIOENCODING=utf-8
   ```

4. **Start the Application**
   ```bash
   uvicorn ai_engine.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Verify Startup**
   - Open browser: http://localhost:8000/docs
   - Should see Swagger UI with endpoints listed
   - Status should show "Smart AI Engine - Phase 4B"

## Testing Framework Overview

### Test Categories
1. **Functional Tests** - Core AI engine functionality
2. **Integration Tests** - Cross-component workflow 
3. **Performance Tests** - Response time and accuracy
4. **Mobile Tests** - Device-specific behavior
5. **Multi-Exam Tests** - JEE/NEET/Advanced parity

### Test Data Sets
The engine processes the following exam configurations:

**JEE Mains:**
- Scoring: +4 correct, -1 incorrect
- Time Limit: 180 seconds per question
- Question Types: MCQ, Integer
- Subjects: Physics (35%), Chemistry (35%), Math (30%)

**NEET:**
- Scoring: +4 correct, -1 incorrect  
- Time Limit: 90 seconds per question
- Question Types: MCQ only
- Subjects: Physics (25%), Chemistry (25%), Biology (50%)

**JEE Advanced:**
- Scoring: +4 correct, -2 incorrect
- Time Limit: 240 seconds per question
- Question Types: MCQ, Integer, Matrix
- Subjects: Physics (33%), Chemistry (33%), Math (34%)

## Test Execution Guide

### Phase 1: Basic Functionality Tests

#### Test 1.1: Exam Configuration Validation
**Objective:** Verify each exam type loads correct parameters

**Steps:**
1. Open Swagger UI: http://localhost:8000/docs
2. Test Admin Config endpoint: `/admin/exam-config/update-marking-scheme`
3. Send request for each exam:

```json
{
  "exam_code": "NEET",
  "correct_score": 4,
  "incorrect_score": -1,
  "time_constraints_sec": 90
}
```

**Expected Results:**
- Status: 200 OK
- Response: `{"status": "success", "exam_code": "NEET"}`
- Verify all three exam codes (JEE_Mains, NEET, JEE_Advanced)

#### Test 1.2: Time Allocation by Exam
**Objective:** Confirm time limits enforce per-exam caps

**Steps:**
1. Use endpoint: `/ai/trace/pacing/allocate-time`
2. Test with extreme base time (600,000ms = 10 minutes)
3. Send for each exam type:

```json
{
  "student_id": "test_student_001",
  "question_id": "q_001",
  "base_time_ms": 600000,
  "stress_level": 0.3,
  "fatigue_level": 0.2,
  "mastery": 0.7,
  "difficulty": 0.8,
  "session_elapsed_ms": 1800000,
  "exam_code": "NEET"
}
```

**Expected Results:**
- JEE_Mains: final_time_ms ≤ 180,000
- NEET: final_time_ms ≤ 90,000  
- JEE_Advanced: final_time_ms ≤ 240,000
- Response includes `breakdown.max_allowed_time_ms`

### Phase 2: Mobile Device Testing

#### Test 2.1: Mobile Context Headers
**Objective:** Verify mobile-specific processing

**Setup:**
Add these headers to all requests:
```
X-Device-Type: mobile
X-Screen-Class: small
X-Network: low
X-Interface-Score: 0.8
X-Distraction-Level: 0.6
```

**Steps:**
1. Send time allocation request with mobile headers
2. Compare response to desktop equivalent
3. Verify recommendations include mobile-specific advice

**Expected Results:**
- Higher extraneous_load for mobile vs desktop
- Recommendations mention "touch targets" or "do-not-disturb"
- Time allocation accounts for mobile constraints

#### Test 2.2: Network Quality Impact
**Objective:** Test low bandwidth scenarios

**Test Matrix:**
| Network | Expected Behavior |
|---------|------------------|
| high    | Standard processing |
| medium  | Slight load increase |  
| low     | Higher latency penalties |

### Phase 3: Multi-Exam Integration Tests

#### Test 3.1: Cross-Exam Calibration
**Objective:** Ensure each exam maintains separate probability calibration

**Steps:**
1. Fit temperature for JEE Advanced Physics:
```json
{
  "logits": [[1.2, 0.8], [0.5, 1.5], [2.0, 0.3]],
  "labels": [0, 1, 0],
  "exam_code": "JEE_Advanced", 
  "subject": "physics"
}
```

2. Fit temperature for NEET Biology:
```json
{
  "logits": [[0.8, 1.2], [1.5, 0.5], [0.3, 2.0]],
  "labels": [1, 0, 1],
  "exam_code": "NEET",
  "subject": "biology" 
}
```

3. Apply calibration for each exam/subject combination

**Expected Results:**
- Different temperature values for each (exam, subject) pair
- Calibrated probabilities sum to 1.0
- No cross-contamination between exam types

#### Test 3.2: Fairness Monitoring by Exam
**Objective:** Verify bias detection works per exam

**Steps:**
1. Update fairness stats for NEET Biology:
```json
{
  "exam_code": "NEET",
  "subject": "biology", 
  "group": "rural",
  "mastery_scores": [0.65, 0.62, 0.68, 0.61]
}
```

2. Update for urban group:
```json
{
  "exam_code": "NEET",
  "subject": "biology",
  "group": "urban", 
  "mastery_scores": [0.78, 0.82, 0.75, 0.79]
}
```

3. Generate fairness report for NEET Biology

**Expected Results:**
- Report shows disparity between rural and urban groups
- Recommendations provided if disparity > 0.08
- Results isolated to NEET Biology (no JEE contamination)

### Phase 4: Stress and Cognitive Load Tests

#### Test 4.1: Stress Detection Pipeline
**Objective:** Validate stress detection feeds into downstream components

**Setup Headers:**
```
X-Response-Time: 45000
X-Is-Correct: false
X-Hesitation: 8000
X-Keystroke-Dev: 1200
```

**Steps:**
1. Send request to any AI endpoint with stress headers
2. Check middleware processes stress signals
3. Verify stress level appears in downstream calculations

**Expected Results:**
- Middleware calculates stress_level > 0
- Time allocator increases allocation for high stress
- Load manager shows stress impact on capacity

#### Test 4.2: Cognitive Load Assessment
**Objective:** Test load calculation with device awareness

**Complex Problem Headers:**
```
X-Item-Steps: 8
X-Concepts-Required: thermodynamics,entropy,statistical_mechanics
X-Prerequisites: physics_basics,calculus
X-Learning-Value: 0.8
X-Schema-Complexity: 0.7
X-Session-Minutes: 90
X-Time-Pressure: 0.6
X-Interface-Score: 0.9
X-Distraction-Level: 0.4
```

**Steps:**
1. Send request with complex problem headers
2. Test with both desktop and mobile device types
3. Compare cognitive load assessments

**Expected Results:**
- Higher intrinsic_load for complex problems
- Mobile shows higher extraneous_load
- Overload_risk calculated accurately
- Actionable recommendations provided

### Phase 5: End-to-End Workflow Tests

#### Test 5.1: Complete Learning Session
**Objective:** Simulate realistic student interaction across multiple questions

**Session Sequence:**
1. **Question 1:** Easy warmup (difficulty: 0.3)
2. **Question 2:** Medium challenge (difficulty: 0.6)  
3. **Question 3:** Hard problem (difficulty: 0.9)
4. **Question 4:** Review question (difficulty: 0.4)

For each question:
1. Get time allocation
2. Submit answer with response time
3. Check mastery update
4. Get next question recommendation

**Tracking Metrics:**
- Time allocations adapt to performance
- Mastery estimates update correctly
- Selection difficulty follows student ability
- Exam-specific scoring reflected in decisions

#### Test 5.2: Multi-Exam Student Profile
**Objective:** Test student switching between exam preparations

**Steps:**
1. Start JEE Mains session (Physics)
2. Complete 3 questions, track mastery
3. Switch to NEET (Biology) 
4. Complete 3 questions in new exam
5. Return to JEE Mains (Math)

**Expected Results:**
- Mastery tracking separate by exam/subject
- Time constraints switch correctly
- Scoring schemes update automatically
- No data contamination between exams

### Phase 6: Performance and Load Tests

#### Test 6.1: Response Time Benchmarks
**Objective:** Ensure acceptable response times

**Benchmarks:**
- Time allocation: < 100ms
- Calibration fit: < 500ms
- Fairness report: < 200ms
- Admin config update: < 50ms

**Load Test:**
- 50 concurrent time allocation requests
- Mix of exam types and device profiles
- Monitor response time distribution

#### Test 6.2: Memory and Resource Usage
**Objective:** Validate resource efficiency

**Monitor:**
- CPU usage during peak load
- Memory consumption over extended sessions
- Database connection pooling (if applicable)
- Log file sizes and rotation

## Error Handling and Edge Cases

### Test 7.1: Invalid Input Handling
**Common Error Scenarios:**
1. Invalid exam_code values
2. Out-of-range stress/mastery levels  
3. Negative time values
4. Missing required headers
5. Malformed JSON payloads

**Expected Behavior:**
- Graceful error messages (not stack traces)
- Appropriate HTTP status codes
- Fallback to safe defaults where possible
- Comprehensive error logging

### Test 7.2: System Recovery Tests
**Failure Scenarios:**
1. Database connection loss
2. High memory pressure
3. Concurrent request storms
4. Malformed model data

**Recovery Verification:**
- Service remains responsive
- Requests queue properly
- Circuit breakers activate
- Health checks return accurate status

## Reporting and Documentation

### Test Result Format
For each test, record:

**Test ID:** [Phase].[Test].[Subtest]  
**Status:** PASS/FAIL/BLOCKED  
**Execution Time:** [duration]  
**Environment:** [desktop/mobile/mixed]  
**Exam Type:** [JEE_Mains/NEET/JEE_Advanced/Multi]  
**Issues Found:** [description]  
**Screenshots:** [if UI involved]  

### Critical Success Criteria
**Must Pass:**
- All exam-specific time caps enforced
- Mobile vs desktop load calculations differ appropriately  
- No cross-exam data contamination
- Admin config changes take effect immediately
- Response times under benchmark limits

**Should Pass:**  
- Fairness disparities detected correctly
- Stress detection correlates with performance
- Memory usage remains stable over time
- Error messages are user-friendly

### Bug Report Template
```
**Bug ID:** BUG-PHASE4B-001
**Priority:** High/Medium/Low
**Component:** [Pacing/Calibration/Fairness/etc.]
**Exam Type:** [JEE_Mains/NEET/JEE_Advanced]
**Device Type:** [Desktop/Mobile] 
**Steps to Reproduce:**
1. 
2.
3.

**Expected Result:**
**Actual Result:** 
**Screenshots:** [attach if applicable]
**Logs:** [relevant log excerpts]
**Workaround:** [if known]
```

## Troubleshooting Guide

### Common Issues

**Issue:** Import errors on startup  
**Solution:** Check Python path and requirements.txt installation

**Issue:** Exam config not loading  
**Solution:** Verify exam_config.py file placement and syntax

**Issue:** Mobile tests showing same results as desktop  
**Solution:** Confirm X-Device-Type header is being sent correctly

**Issue:** Time limits not enforcing  
**Solution:** Check time_allocator.py integration and exam_code propagation

**Issue:** Cross-exam contamination  
**Solution:** Verify calibration and fairness use separate keys per exam

### Debug Commands
```bash
# Check application logs
tail -f logs/ai-engine.log

# Verify configuration loading
curl -X GET "http://localhost:8000/health" 

# Test specific endpoint
curl -X POST "http://localhost:8000/ai/trace/pacing/allocate-time" \
  -H "Content-Type: application/json" \
  -H "X-Exam-Code: NEET" \
  -d '{"student_id":"test","question_id":"q1","base_time_ms":30000,"stress_level":0.5,"fatigue_level":0.3,"mastery":0.6,"difficulty":0.7,"session_elapsed_ms":60000}'
```

## Contact Information

**Development Team:** [Contact details]  
**Issue Tracker:** [URL]  
**Documentation:** [Wiki/Confluence URL]  
**Emergency Contact:** [Phone/Email for critical issues]

---

**Note:** This testing phase is critical for validating the transition from single-exam (JEE-only) to universal multi-exam platform. Pay special attention to exam-specific behaviors and mobile device compatibility.

**Testing Duration Estimate:** 3-5 days for comprehensive validation  
**Test Environment:** Local development initially, staging environment for final validation