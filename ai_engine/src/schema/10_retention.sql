-- Data retention policy table
CREATE TABLE public.data_retention_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    retention_period_days INTEGER NOT NULL,
    auto_delete_enabled BOOLEAN DEFAULT FALSE,
    deletion_conditions JSONB DEFAULT '{}'::jsonb,
    last_cleanup_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default retention policies
INSERT INTO data_retention_policies (table_name, retention_period_days, auto_delete_enabled) VALUES
('question_interactions', 730, true), -- 2 years
('learning_sessions', 1095, true),     -- 3 years
('system_events', 90, true),           -- 3 months
('ai_recommendations', 365, true),     -- 1 year
('student_features', 365, true);       -- 1 year

-- Cleanup function
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS INTEGER AS $$
DECLARE
    policy RECORD;
    deleted_count INTEGER := 0;
    total_deleted INTEGER := 0;
BEGIN
    FOR policy IN SELECT * FROM data_retention_policies WHERE auto_delete_enabled = true LOOP
        EXECUTE format(
            'DELETE FROM %I WHERE created_at < NOW() - INTERVAL ''%s days''',
            policy.table_name,
            policy.retention_period_days
        );

        GET DIAGNOSTICS deleted_count = ROW_COUNT;
        total_deleted := total_deleted + deleted_count;

        -- Update last cleanup timestamp
        UPDATE data_retention_policies
        SET last_cleanup_at = NOW()
        WHERE id = policy.id;

        -- Log cleanup activity
        INSERT INTO system_events (event_type, event_source, event_payload)
        VALUES (
            'data_cleanup',
            'retention_policy',
            jsonb_build_object(
                'table_name', policy.table_name,
                'deleted_count', deleted_count,
                'retention_days', policy.retention_period_days
            )
        );
    END LOOP;

    RETURN total_deleted;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
