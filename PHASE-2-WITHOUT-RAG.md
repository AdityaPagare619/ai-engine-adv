<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# nice so now lets start working on these PHASE 2.1 expand it now step by step we will focus on every single thing.

Phase 2.1: AI-Powered Question Generation
=========================================

Phase 2.1 transforms your static question bank into a fully autonomous, syllabus-aware question‐generation engine. Over three sprints, we’ll build and deploy a microservice that produces unlimited high-quality questions—across formats and difficulty levels—tailored to each student’s mastery profile.

Sprint 2.1.1 (Weeks 1–2): Template Library \& Basic Generator
-----------------------------------------------------------
- Define question templates for all required formats:
– MCQ (single/multiple correct)
– Numerical (precision, range)
– Assertion–Reason
– Passage-based comprehension
- Curate source content for each JEE/NEET syllabus topic (Physics, Chemistry, Math)
- Implement “template filler” module:
– Named-entity extraction from syllabus text
– Variable substitution (numbers, units, chemical names)
- Expose a “generate” endpoint:
POST /questions/generate
Request: { topic_id, format, difficulty_hint }
Response: { question_text, options, answer_key, metadata }
- Unit tests: 90% coverage on template logic

Sprint 2.1.2 (Weeks 3–6): Difficulty Calibrator \& BKT Integration
----------------------------------------------------------------
- Integrate EnhancedMultiConceptBKT to fetch student’s mastery for topic_id
- Develop difficulty adjustment algorithm:
– Map mastery probability → reading complexity, distractor similarity, numerical precision
– Scale difficulty_hint by ±20% based on real-time load assessment
- Embed “difficulty calibrator” in generation pipeline:
generate() → calibrate_difficulty() → validate()
- Implement metadata logging:
– store { student_id, topic_id, difficulty_hint, calibrated_level } in “question_generation_logs”
- Load-test calibration module under 500 req/sec; optimize caching for repeated templates

Sprint 2.1.3 (Weeks 7–10): Real-Time Quality Validation \& Feedback Loop
----------------------------------------------------------------------
- Integrate a lightweight language model (e.g., distilled GPT) to validate question clarity:
– Grammaticality, ambiguity score, option overlap
- Develop “validator” micro-task pipeline:
– generate() → validate_semantics() → post_process()
- Build admin UI for sampling generated questions and flagging errors
- Implement automatic retraining data pipeline:
– Collect flagged questions → store in “qa_feedback” table
– Weekly batch job to retrain template parameters and improve distractor selection
- Achieve ≥ 95% pass rate on clarity checks, < 2% flag rate in admin sampling

Sprint 2.1.4 (Weeks 11–12): Service Hardening \& Deployment
----------------------------------------------------------
- Package as Docker microservice with health checks (`/health`) and metrics (`/metrics`) endpoints
- Configure Kubernetes Deployment + HPA (autoscale 2–10 replicas based on CPU \& request queue)
- Implement rate limiting (100 req/min per student) in API gateway
- End-to-end integration tests: generate → calibrate → validate → log → respond
- Deploy to staging and conduct pilot with 100 students for real-world feedback

Key Success Metrics (End of Phase 2.1)
--------------------------------------
- **Generation Capacity:** 1,000 questions/minute
- **Quality Pass Rate:** ≥ 95% on clarity and syllabus compliance
- **Difficulty Accuracy:** ± 0.1 mastery prediction error
- **Uptime:** 99.9% under load
- **Developer Experience:** 5-minute setup to “generate” endpoint

By the end of Phase 2.1, you’ll have a production-ready question-generation service that autonomously creates, calibrates, and validates high-quality practice and mock exam items—paving the way for truly adaptive, student-centric test experiences.

