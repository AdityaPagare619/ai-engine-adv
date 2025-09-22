-- Performance Optimization Indexes
-- Phase 1 Implementation - Enhanced Query Performance
-- Created: 2025-09-22

-- =====================================================
-- 1. Composite Indexes for Complex Queries
-- =====================================================

-- Student mastery queries with time filtering
CREATE INDEX IF NOT EXISTS idx_student_mastery_composite_time 
ON student_concept_mastery_enhanced(student_id, last_interaction DESC, mastery_probability DESC);

-- BKT logs for student analysis
CREATE INDEX IF NOT EXISTS idx_bkt_logs_student_time_concept 
ON bkt_interaction_logs_enhanced(student_id, interaction_timestamp DESC, concept_id);

-- Transfer learning effectiveness analysis
CREATE INDEX IF NOT EXISTS idx_transfer_events_effectiveness 
ON transfer_learning_events(transfer_type, boost_amount DESC, event_timestamp DESC);

-- Time context recommendations by urgency
CREATE INDEX IF NOT EXISTS idx_recommendations_urgency_status 
ON time_context_recommendations(urgency_level, recommendation_status, priority_level DESC);

-- Risk assessment trending
CREATE INDEX IF NOT EXISTS idx_risk_assessment_trending 
ON exam_preparation_risk_assessment(student_id, assessment_date DESC, overall_risk_level);

-- =====================================================
-- 2. Partial Indexes for Active Data
-- =====================================================

-- Active exam timelines only
CREATE INDEX IF NOT EXISTS idx_active_exam_timelines_partial 
ON student_exam_timeline(student_id, days_remaining, current_phase) 
WHERE is_active = TRUE;

-- Pending recommendations only
CREATE INDEX IF NOT EXISTS idx_pending_recommendations_partial 
ON time_context_recommendations(student_id, created_at DESC) 
WHERE recommendation_status IN ('new', 'acknowledged', 'in_progress');

-- Recent BKT interactions (last 30 days)
CREATE INDEX IF NOT EXISTS idx_recent_bkt_interactions 
ON bkt_interaction_logs_enhanced(student_id, concept_id, mastery_change)
WHERE interaction_timestamp > (CURRENT_TIMESTAMP - INTERVAL '30 days');

-- High-risk students only
CREATE INDEX IF NOT EXISTS idx_high_risk_students 
ON exam_preparation_risk_assessment(student_id, assessment_date DESC, mastery_gap_risk)
WHERE overall_risk_level IN ('high', 'critical');

-- Overdue milestones
CREATE INDEX IF NOT EXISTS idx_overdue_milestones 
ON study_milestones(student_id, target_date, priority_level)
WHERE milestone_status IN ('overdue', 'in_progress') AND target_date < CURRENT_DATE;

-- =====================================================
-- 3. Functional Indexes for Analytics
-- =====================================================

-- Mastery level buckets for analytics
CREATE INDEX IF NOT EXISTS idx_mastery_buckets 
ON student_concept_mastery_enhanced(
    student_id,
    CASE 
        WHEN mastery_probability >= 0.8 THEN 'high'
        WHEN mastery_probability >= 0.6 THEN 'medium'
        WHEN mastery_probability >= 0.4 THEN 'low'
        ELSE 'very_low'
    END
);

-- Study consistency analysis
CREATE INDEX IF NOT EXISTS idx_study_consistency 
ON daily_study_schedules(
    student_id, 
    schedule_date,
    CASE 
        WHEN adherence_percentage >= 80 THEN 'consistent'
        WHEN adherence_percentage >= 60 THEN 'moderate'
        ELSE 'inconsistent'
    END
) WHERE schedule_status = 'completed';

-- Phase transition tracking
CREATE INDEX IF NOT EXISTS idx_phase_transitions 
ON student_exam_timeline(student_id, current_phase, days_remaining)
WHERE is_active = TRUE;

-- =====================================================
-- 4. Text Search Indexes
-- =====================================================

-- Full-text search on recommendations
CREATE INDEX IF NOT EXISTS idx_recommendations_fulltext 
ON time_context_recommendations 
USING GIN(to_tsvector('english', recommendation_title || ' ' || recommendation_description));

-- Milestone search
CREATE INDEX IF NOT EXISTS idx_milestones_fulltext 
ON study_milestones 
USING GIN(to_tsvector('english', milestone_name || ' ' || COALESCE(milestone_description, '')));

-- Daily notes search
CREATE INDEX IF NOT EXISTS idx_daily_notes_fulltext 
ON daily_study_schedules 
USING GIN(to_tsvector('english', COALESCE(daily_notes, '')))
WHERE daily_notes IS NOT NULL AND LENGTH(daily_notes) > 0;

-- =====================================================
-- 5. Performance Analytics Indexes
-- =====================================================

-- BKT performance analytics by period
CREATE INDEX IF NOT EXISTS idx_bkt_analytics_period_date 
ON bkt_performance_analytics(analysis_period, analysis_date DESC, engine_health);

-- Concept performance aggregation
CREATE INDEX IF NOT EXISTS idx_concept_difficulty_performance 
ON concept_difficulty_analysis(subject_area, total_complexity DESC, success_rate DESC);

-- Learning patterns analysis
CREATE INDEX IF NOT EXISTS idx_learning_patterns_analysis 
ON student_learning_patterns(learning_velocity DESC, transfer_learning_affinity DESC, last_active DESC);

-- Transfer learning source analysis
CREATE INDEX IF NOT EXISTS idx_transfer_source_analysis 
ON transfer_learning_events(source_concept_id, transfer_type, boost_amount DESC, event_timestamp DESC);

-- =====================================================
-- 6. Time-based Partitioned Indexes
-- =====================================================

-- Monthly partitioned index for BKT logs
CREATE INDEX IF NOT EXISTS idx_bkt_logs_monthly 
ON bkt_interaction_logs_enhanced(
    DATE_TRUNC('month', interaction_timestamp),
    student_id,
    concept_id
);

-- Weekly partitioned index for daily schedules
CREATE INDEX IF NOT EXISTS idx_schedules_weekly 
ON daily_study_schedules(
    DATE_TRUNC('week', schedule_date),
    student_id,
    adherence_percentage DESC
);

-- Daily partitioned index for recommendations
CREATE INDEX IF NOT EXISTS idx_recommendations_daily 
ON time_context_recommendations(
    recommendation_date,
    student_id,
    recommendation_status
);

-- =====================================================
-- 7. JSONB Indexes for Metadata
-- =====================================================

-- Transfer sources JSON analysis
CREATE INDEX IF NOT EXISTS idx_transfer_sources_gin 
ON bkt_interaction_logs_enhanced 
USING GIN(transfer_sources) 
WHERE transfer_sources IS NOT NULL;

-- Recommendation action items
CREATE INDEX IF NOT EXISTS idx_action_items_gin 
ON time_context_recommendations 
USING GIN(action_items) 
WHERE action_items IS NOT NULL;

-- Risk factors analysis
CREATE INDEX IF NOT EXISTS idx_risk_factors_gin 
ON exam_preparation_risk_assessment 
USING GIN(factors_considered) 
WHERE factors_considered IS NOT NULL;

-- BKT analytics subject breakdown
CREATE INDEX IF NOT EXISTS idx_subject_breakdown_gin 
ON bkt_performance_analytics 
USING GIN(subject_breakdown) 
WHERE subject_breakdown IS NOT NULL;

-- =====================================================
-- 8. Covering Indexes for Common Queries
-- =====================================================

-- Student mastery summary covering index
CREATE INDEX IF NOT EXISTS idx_student_mastery_summary_covering 
ON student_concept_mastery_enhanced(student_id) 
INCLUDE (concept_id, mastery_probability, confidence_level, practice_count, last_interaction);

-- Recent interactions covering index
CREATE INDEX IF NOT EXISTS idx_recent_interactions_covering 
ON bkt_interaction_logs_enhanced(student_id, interaction_timestamp DESC) 
INCLUDE (concept_id, is_correct, mastery_change, cognitive_load)
WHERE interaction_timestamp > (CURRENT_TIMESTAMP - INTERVAL '7 days');

-- Active timeline covering index
CREATE INDEX IF NOT EXISTS idx_active_timeline_covering 
ON student_exam_timeline(student_id) 
INCLUDE (exam_type, exam_date, days_remaining, current_phase, urgency_level)
WHERE is_active = TRUE;

-- =====================================================
-- 9. Statistics and Maintenance
-- =====================================================

-- Update table statistics for query planner
ANALYZE student_concept_mastery_enhanced;
ANALYZE bkt_interaction_logs_enhanced;
ANALYZE transfer_learning_events;
ANALYZE student_exam_timeline;
ANALYZE time_context_recommendations;
ANALYZE exam_preparation_risk_assessment;
ANALYZE daily_study_schedules;
ANALYZE study_milestones;

-- =====================================================
-- 10. Query Optimization Views
-- =====================================================

-- Materialized view for student performance dashboard
CREATE MATERIALIZED VIEW IF NOT EXISTS student_performance_dashboard AS
SELECT 
    s.student_id,
    s.overall_mastery,
    s.total_concepts,
    s.mastered_concepts,
    s.weak_concepts,
    s.last_activity,
    et.exam_type,
    et.days_remaining,
    et.current_phase,
    et.urgency_level,
    COALESCE(ra.overall_risk_level, 'unknown') as risk_level,
    COALESCE(ds.avg_adherence, 0) as recent_adherence
FROM student_mastery_summary s
LEFT JOIN student_exam_timeline et ON s.student_id = et.student_id AND et.is_active = TRUE
LEFT JOIN (
    SELECT DISTINCT ON (student_id) 
        student_id, overall_risk_level 
    FROM exam_preparation_risk_assessment 
    ORDER BY student_id, assessment_date DESC
) ra ON s.student_id = ra.student_id
LEFT JOIN (
    SELECT 
        student_id, 
        AVG(adherence_percentage) as avg_adherence
    FROM daily_study_schedules 
    WHERE schedule_date > (CURRENT_DATE - INTERVAL '7 days') 
        AND schedule_status = 'completed'
    GROUP BY student_id
) ds ON s.student_id = ds.student_id;

-- Create index on materialized view
CREATE INDEX IF NOT EXISTS idx_performance_dashboard_student 
ON student_performance_dashboard(student_id);

CREATE INDEX IF NOT EXISTS idx_performance_dashboard_risk 
ON student_performance_dashboard(risk_level, urgency_level);

-- Materialized view for concept analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS concept_analytics_summary AS
SELECT 
    c.concept_id,
    c.subject_area,
    c.base_difficulty,
    c.total_complexity,
    COUNT(DISTINCT s.student_id) as students_attempted,
    AVG(s.mastery_probability) as avg_mastery,
    STDDEV(s.mastery_probability) as mastery_std_dev,
    COUNT(CASE WHEN s.mastery_probability > 0.8 THEN 1 END) as students_mastered,
    AVG(s.practice_count) as avg_practice_needed,
    COUNT(DISTINCT t.id) as transfer_events_as_target,
    AVG(t.boost_amount) as avg_transfer_boost
FROM concept_difficulty_analysis c
LEFT JOIN student_concept_mastery_enhanced s ON c.concept_id = s.concept_id
LEFT JOIN transfer_learning_events t ON c.concept_id = t.target_concept_id
GROUP BY c.concept_id, c.subject_area, c.base_difficulty, c.total_complexity;

-- Create index on concept analytics
CREATE INDEX IF NOT EXISTS idx_concept_analytics_subject 
ON concept_analytics_summary(subject_area, avg_mastery DESC);

-- =====================================================
-- 11. Performance Monitoring
-- =====================================================

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_performance_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY student_performance_dashboard;
    REFRESH MATERIALIZED VIEW CONCURRENTLY concept_analytics_summary;
END;
$$ LANGUAGE plpgsql;

-- Function to get index usage statistics
CREATE OR REPLACE FUNCTION get_index_usage_stats()
RETURNS TABLE(
    schemaname TEXT,
    tablename TEXT,
    indexname TEXT,
    idx_scan BIGINT,
    idx_tup_read BIGINT,
    idx_tup_fetch BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.schemaname::TEXT,
        s.tablename::TEXT,
        s.indexname::TEXT,
        s.idx_scan,
        s.idx_tup_read,
        s.idx_tup_fetch
    FROM pg_stat_user_indexes s
    WHERE s.schemaname = 'public'
        AND (s.tablename LIKE '%bkt%' OR s.tablename LIKE '%student%' OR s.tablename LIKE '%time%')
    ORDER BY s.idx_scan DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to identify slow queries
CREATE OR REPLACE FUNCTION get_slow_queries()
RETURNS TABLE(
    query TEXT,
    calls BIGINT,
    total_time DOUBLE PRECISION,
    mean_time DOUBLE PRECISION,
    max_time DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.query::TEXT,
        s.calls,
        s.total_time,
        s.mean_time,
        s.max_time
    FROM pg_stat_statements s
    WHERE s.query LIKE '%student%' OR s.query LIKE '%bkt%' OR s.query LIKE '%concept%'
    ORDER BY s.mean_time DESC
    LIMIT 20;
EXCEPTION
    WHEN undefined_table THEN
        RAISE NOTICE 'pg_stat_statements extension not available';
        RETURN;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 12. Comments and Documentation
-- =====================================================

COMMENT ON INDEX idx_student_mastery_composite_time IS 'Composite index for student mastery queries with time filtering';
COMMENT ON INDEX idx_bkt_logs_student_time_concept IS 'Optimizes student BKT analysis queries';
COMMENT ON INDEX idx_transfer_events_effectiveness IS 'Speeds up transfer learning effectiveness analysis';
COMMENT ON INDEX idx_recommendations_urgency_status IS 'Quick filtering of urgent recommendations';
COMMENT ON INDEX idx_active_exam_timelines_partial IS 'Partial index for active student timelines only';

COMMENT ON MATERIALIZED VIEW student_performance_dashboard IS 'Pre-computed student performance metrics for dashboards';
COMMENT ON MATERIALIZED VIEW concept_analytics_summary IS 'Pre-computed concept performance analytics';

COMMENT ON FUNCTION refresh_performance_views() IS 'Refreshes all materialized views for current data';
COMMENT ON FUNCTION get_index_usage_stats() IS 'Returns usage statistics for BKT-related indexes';
COMMENT ON FUNCTION get_slow_queries() IS 'Identifies slow queries related to BKT system';

-- =====================================================
-- 13. Maintenance Schedule
-- =====================================================

-- Note: Set up automated tasks to:
-- 1. REFRESH MATERIALIZED VIEWS every hour during peak usage
-- 2. VACUUM and ANALYZE tables daily during low usage periods
-- 3. REINDEX weekly for heavily updated tables
-- 4. Monitor index usage with get_index_usage_stats() function

-- Migration completion
INSERT INTO schema_migrations (version, applied_at) VALUES ('004_indexes_optimization', CURRENT_TIMESTAMP)
ON CONFLICT (version) DO NOTHING;