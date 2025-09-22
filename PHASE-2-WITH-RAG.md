<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Phase 2: Autonomous Adaptive Test Platform (Revised with RAG Advisor)

This detailed Phase 2 plan incorporates the RAG “advisor” component only at high-impact points—ensuring the core AI engine remains fast, deterministic, and reliable while RAG boosts quality and transparency where it matters most.

***

## 2.1 AI-Powered Question Generation Engine

Sprint 2.1.x builds the template-based generator, difficulty calibrator, and lightweight validator.

- **New Tables/Schema Updates**:
– `question_templates`, `question_generation_logs`, extended `question_metadata_cache`
- **Microservice Structure** (Go/Python):
– Templates loader → Calibrator (BKT) → Validator (grammar/clarity) → Logger → API
- **Kubernetes Deployment** with HPA, rate-limits, health checks
- **RAG Advisor Integration** (Phase 2.2 entrypoint):
– **Post-Generation QA Check**: After validator, call RAG QA agent to retrieve exemplar questions and rubric snippets. If alignment < 0.8, trigger a regeneration.
– Ensures no off-syllabus or ambiguous items slip through.

***

## 2.2 Time-Aware Adaptive Testing

Builds EnhancedMultiConceptBKT integration, stress detection, pacing engine, and UI components.

- **Adaptive-Test Service**: BKT inference → Pacing recommendations → Stress interventions
- **UI**: “Confidence Ribbon,” live performance metrics
- **RAG Advisor Use**:
– **On-Demand Explanations**: “Explain Solution” button invokes RAG to fetch multi-source worked steps, common pitfalls, and concept notes.
– Fully offline from scoring loop; no live latency impact.

***

## 2.3 Intelligent Proctoring \& Integrity

Implements camera/audio monitoring, multi-factor auth, and browser lockdown.

- **Proctoring Service**: Computer vision + anomaly alerts → Human review dashboard
- **RAG Advisor Role**: None—keep proctoring logic static, low-latency, and deterministic.

***

## 2.4 Student \& Educator Experiences

Develops student portal, educator dashboard, scheduler, and reporting engine.

- **Student Portal**: Practice/test flows, progress dashboard, “Ask AI Tutor”
- **Educator Dashboard**: Performance heatmaps, at-risk alerts, custom test preview
- **Automated Scheduler**: Policy-driven test assignments
- **Reporting Engine**: PDF/Excel exports
- **RAG Advisor Integration**:
– **Study-Plan Rationale Sidebar**: In “Next Topic” recommendations, show “Why this?” powered by RAG retrieval of dependency evidence and past performance snippets.
– **Admin Copilot (Batch)**: Weekly class summaries assembled via RAG retrieval of key metrics, flagged question issues, and student notes—no effect on live user sessions.

***

## Cross-Workstream Enablers

- **Data \& Analytics**: Kafka event bus → AWS S3/Athena → Metabase dashboards
- **DevOps \& Infra**: Docker + Helm → Kubernetes on EKS → GitHub Actions CI/CD → Autoscaling
- **Quality \& Compliance**: Automated tests (unit/integration/load), Snyk scanning, Lighthouse/Axe audits

***

### Timeline \& Milestones

| Month | Q-Gen | Adaptive Testing | Proctoring | UX \& Dashboards | RAG Advisor |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 1 | Templates \& API | BKT integration | Auth + basic CV | Wireframes \& APIs | – |
| 2 | Calibrator \& BKT | Stress detection | Behavior analytics | Dashboard core | Plan RAG QA agent |
| 3 | Validator \& Logs | UI widgets | Browser lockdown | Scheduler \& reports | Implement RAG QA checks |
| 4–6 | Scale \& optimize | Scale scenarios | Dashboard refine | Beta launch | On-demand \& “Why” sidebar |


***

## RAG Advisor Summary

**Where Used**

1. **Post-Generation QA**: Validate every generated question before delivery
2. **On-Demand Explanations**: Fetch multi-source solution steps upon student request
3. **Study-Plan Rationale**: Provide “Why this next?” evidence in recommendations
4. **Admin Copilot (Batch)**: Generate weekly educator reports

**Benefits**

- Removes ambiguity and syllabus drift from questions
- Enriches student explanations \& trust without live-path latency
- Strengthens adaptive recommendations with transparent evidence
- Empowers educators with synthesized insights

**Risks \& Mitigations**

- **Latency**: Advisor calls capped at 1-2 hops; on-demand only
- **Cost**: Small open-source models \& managed vector DB keep infra lean
- **Complexity**: Agent code isolated in separate service; core engine unaffected

***

**Conclusion**
This repolished Phase 2 plan preserves your high-performance core AI engine while strategically integrating RAG as a “senior faculty advisor.” It maximizes question quality, user trust, and explainability—without jeopardizing speed, reliability, or operational cost. Proceed with advisor-only RAG in Phase 2.2 and measure impact before broader expansion.

