-- Function to calculate student mastery summary
CREATE OR REPLACE FUNCTION get_student_mastery_summary(p_student_id UUID)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'overall_mastery', AVG(mastery_probability),
        'concepts_mastered', COUNT(*) FILTER (WHERE mastery_probability >= 0.8),
        'concepts_learning', COUNT(*) FILTER (WHERE mastery_probability BETWEEN 0.3 AND 0.8),
        'concepts_struggling', COUNT(*) FILTER (WHERE mastery_probability < 0.3),
        'total_concepts', COUNT(*),
        'last_updated', MAX(updated_at)
    )
    INTO result
    FROM student_knowledge_states
    WHERE student_id = p_student_id;

  RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Recommendation RPC (LinUCB-ready placeholder)
CREATE OR REPLACE FUNCTION recommend_questions_linucb(
  p_student_id UUID,
  p_context JSONB DEFAULT '{}'::jsonb,
  p_limit INT DEFAULT 10
)
RETURNS JSONB AS $$
/*
Returns:
{
  "questions": ["EXM-...-Q-00028", ...],
  "rationale": [{"q":"...","score":0.73,"signals":{"mastery_gap":0.4,"novelty":0.2,"recency":0.13}}]
}
*/
DECLARE
  result JSONB := '[]'::jsonb;
BEGIN
  -- Get questions based on low mastery concepts and practice frequency
  RETURN jsonb_build_object(
    'questions',
    (
      SELECT COALESCE(jsonb_agg(concat('Q-', lpad((ROW_NUMBER() OVER())::text, 5, '0'))), '[]'::jsonb)
      FROM (
        SELECT 
          sks.concept_id,
          kc.concept_name,
          sks.mastery_probability,
          sks.practice_count,
          (1 - sks.mastery_probability) * 0.6 + 
          (CASE WHEN sks.practice_count = 0 THEN 0.4 ELSE 0.1 END) as priority_score
        FROM student_knowledge_states sks
        JOIN knowledge_concepts kc ON sks.concept_id = kc.id
        WHERE sks.student_id = p_student_id
          AND sks.mastery_probability < 0.8
          AND (p_context->>'subject' IS NULL OR kc.subject = p_context->>'subject')
        ORDER BY priority_score DESC, sks.last_practice_at ASC NULLS FIRST
        LIMIT p_limit
      ) t
    ),
    'rationale',
    (
      SELECT COALESCE(jsonb_agg(
        jsonb_build_object(
          'concept_id', t.concept_id,
          'concept_name', t.concept_name,
          'score', t.priority_score,
          'signals', jsonb_build_object(
            'mastery_gap', ROUND((1 - t.mastery_probability)::numeric, 3),
            'novelty', CASE WHEN t.practice_count = 0 THEN 0.4 ELSE 0.1 END,
            'recency', CASE WHEN t.last_practice_at IS NULL THEN 0.5 
                           ELSE GREATEST(0, 1 - EXTRACT(epoch FROM (NOW() - t.last_practice_at))/86400/7) 
                      END
          )
        )
      ), '[]'::jsonb)
      FROM (
        SELECT 
          sks.concept_id,
          kc.concept_name,
          sks.mastery_probability,
          sks.practice_count,
          sks.last_practice_at,
          (1 - sks.mastery_probability) * 0.6 + 
          (CASE WHEN sks.practice_count = 0 THEN 0.4 ELSE 0.1 END) as priority_score
        FROM student_knowledge_states sks
        JOIN knowledge_concepts kc ON sks.concept_id = kc.id
        WHERE sks.student_id = p_student_id
          AND sks.mastery_probability < 0.8
          AND (p_context->>'subject' IS NULL OR kc.subject = p_context->>'subject')
        ORDER BY priority_score DESC, sks.last_practice_at ASC NULLS FIRST
        LIMIT p_limit
      ) t
    )
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Prediction RPC (simple, replaceable by model server later)
CREATE OR REPLACE FUNCTION predict_exam_score(
  p_student_id UUID,
  p_features JSONB DEFAULT '{}'::jsonb
)
RETURNS JSONB AS $$
DECLARE 
  avg_mastery FLOAT;
  total_concepts INT;
  mastered_concepts INT;
  predicted_score FLOAT;
  confidence FLOAT;
BEGIN
  -- Get student mastery statistics
  SELECT 
    COALESCE(AVG(mastery_probability), 0.1),
    COUNT(*),
    COUNT(*) FILTER (WHERE mastery_probability >= 0.8)
  INTO avg_mastery, total_concepts, mastered_concepts
  FROM student_knowledge_states
  WHERE student_id = p_student_id;

  -- Calculate predicted score for JEE Main (max 300)
  -- Base score from mastery (60% weight) + consistency bonus (40% weight)
  predicted_score := avg_mastery * 180 + (mastered_concepts::float / GREATEST(total_concepts, 1)) * 120;
  
  -- Confidence based on data availability
  confidence := LEAST(0.95, total_concepts::float / 50.0 + 0.3);
  
  RETURN jsonb_build_object(
    'predicted_score', ROUND(predicted_score, 1),
    'confidence', ROUND(confidence, 3),
    'mastery_stats', jsonb_build_object(
      'avg_mastery', ROUND(avg_mastery, 3),
      'total_concepts', total_concepts,
      'mastered_concepts', mastered_concepts,
      'mastery_ratio', ROUND((mastered_concepts::float / GREATEST(total_concepts, 1)), 3)
    )
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Audit helper to store recommendations atomically
CREATE OR REPLACE FUNCTION write_recommendation_log(
  p_student_id UUID,
  p_payload JSONB
) RETURNS UUID AS $$
DECLARE 
  rec_id UUID;
  questions_array TEXT[];
BEGIN
  -- Convert JSONB array to TEXT array
  SELECT ARRAY(
    SELECT jsonb_array_elements_text(p_payload->'questions')
  ) INTO questions_array;
  
  INSERT INTO ai_recommendations (
    student_id, 
    context_state, 
    recommended_questions, 
    algorithm_name, 
    algorithm_version, 
    confidence_score,
    recommendation_type,
    model_parameters,
    expected_learning_gain,
    created_at,
    expires_at
  )
  VALUES (
    p_student_id,
    p_payload->'context_state',
    questions_array,
    COALESCE(p_payload->>'algorithm', 'contextual_bandit_v0'),
    COALESCE(p_payload->>'version', 'v0.1'),
    COALESCE((p_payload->>'confidence')::numeric, 0.6),
    COALESCE(p_payload->>'type', 'next_questions'),
    p_payload->'model_params',
    COALESCE((p_payload->>'expected_gain')::numeric, 0.1),
    NOW(),
    NOW() + INTERVAL '24 hours'
  )
  RETURNING id INTO rec_id;

  RETURN rec_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Audit helper to store predictions atomically
CREATE OR REPLACE FUNCTION write_prediction_log(
  p_student_id UUID,
  p_payload JSONB
) RETURNS UUID AS $$
DECLARE 
  pred_id UUID;
BEGIN
  INSERT INTO ai_predictions (
    student_id,
    prediction_type,
    prediction_horizon_days,
    prediction_confidence,
    predicted_score,
    predicted_percentile,
    model_name,
    model_version,
    feature_importance,
    prediction_context,
    created_at
  )
  VALUES (
    p_student_id,
    COALESCE(p_payload->>'type', 'exam_score'),
    COALESCE((p_payload->>'horizon_days')::int, 90),
    COALESCE((p_payload->>'confidence')::numeric, 0.65),
    COALESCE((p_payload->>'predicted_score')::numeric, 0),
    COALESCE((p_payload->>'percentile')::numeric, 50),
    COALESCE(p_payload->>'model_name', 'baseline_avg_mastery'),
    COALESCE(p_payload->>'model_version', 'v0.1'),
    p_payload->'feature_importance',
    p_payload->'context',
    NOW()
  )
  RETURNING id INTO pred_id;

  RETURN pred_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to update knowledge state with BKT
CREATE OR REPLACE FUNCTION update_knowledge_state_bkt(
    p_student_id UUID,
    p_concept_id UUID,
    p_is_correct BOOLEAN,
    p_response_time_ms INTEGER DEFAULT NULL
)
RETURNS JSONB AS $$
DECLARE
    current_state RECORD;
    new_mastery DECIMAL;
    learning_occurred BOOLEAN;
    result JSONB;
BEGIN
    -- Get current knowledge state
    SELECT * INTO current_state
    FROM student_knowledge_states
    WHERE student_id = p_student_id AND concept_id = p_concept_id;

    -- Initialize if doesn't exist
    IF NOT FOUND THEN
        INSERT INTO student_knowledge_states (
            student_id, concept_id, mastery_probability,
            learning_rate, forgetting_rate, slip_probability, guess_probability
        ) VALUES (
            p_student_id, p_concept_id, 0.5,
            0.3, 0.1, 0.1, 0.2
        );
        current_state.mastery_probability := 0.5;
        current_state.learning_rate := 0.3;
        current_state.slip_probability := 0.1;
        current_state.guess_probability := 0.2;
        current_state.practice_count := 0;
        current_state.correct_count := 0;
    END IF;

    -- BKT Update Logic
    IF p_is_correct THEN
        -- P(L_n|correct) = P(L_n)(1-s) / [P(L_n)(1-s) + (1-P(L_n))g]
        new_mastery := (current_state.mastery_probability * (1 - current_state.slip_probability)) /
                      (current_state.mastery_probability * (1 - current_state.slip_probability) +
                       (1 - current_state.mastery_probability) * current_state.guess_probability);
    ELSE
        -- P(L_n|incorrect) = P(L_n)s / [P(L_n)s + (1-P(L_n))(1-g)]
        new_mastery := (current_state.mastery_probability * current_state.slip_probability) /
                      (current_state.mastery_probability * current_state.slip_probability +
                       (1 - current_state.mastery_probability) * (1 - current_state.guess_probability));
    END IF;

    -- Apply learning: P(L_n+1) = P(L_n) + (1-P(L_n))t
    learning_occurred := random() < current_state.learning_rate;
    IF learning_occurred THEN
        new_mastery := new_mastery + (1 - new_mastery) * current_state.learning_rate;
    END IF;

    -- Update the record
    UPDATE student_knowledge_states
    SET
        mastery_probability = LEAST(0.99, GREATEST(0.01, new_mastery)),
        practice_count = practice_count + 1,
        correct_count = CASE WHEN p_is_correct THEN correct_count + 1 ELSE correct_count END,
        last_practice_at = NOW(),
        updated_at = NOW()
    WHERE student_id = p_student_id AND concept_id = p_concept_id;

    -- Return result
    result := jsonb_build_object(
        'previous_mastery', current_state.mastery_probability,
        'new_mastery', new_mastery,
        'learning_occurred', learning_occurred,
        'confidence_change', new_mastery - current_state.mastery_probability
    );

    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
