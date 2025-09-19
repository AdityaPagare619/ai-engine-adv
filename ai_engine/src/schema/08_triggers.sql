-- Trigger to update student profile last_active_at
CREATE OR REPLACE FUNCTION update_student_last_active()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE student_profiles
    SET last_active_at = NOW()
    WHERE id = NEW.student_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_last_active_on_interaction
    AFTER INSERT ON question_interactions
    FOR EACH ROW
    EXECUTE FUNCTION update_student_last_active();

-- Trigger for real-time notifications
CREATE OR REPLACE FUNCTION notify_knowledge_update()
RETURNS TRIGGER AS $$
BEGIN
    -- Publish real-time updates via Supabase Realtime
    PERFORM pg_notify(
        'knowledge_state_update',
        json_build_object(
            'student_id', NEW.student_id,
            'concept_id', NEW.concept_id,
            'mastery_probability', NEW.mastery_probability,
            'updated_at', NEW.updated_at
        )::text
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER knowledge_state_realtime_trigger
    AFTER UPDATE ON student_knowledge_states
    FOR EACH ROW
    EXECUTE FUNCTION notify_knowledge_update();
