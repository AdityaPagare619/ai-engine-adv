import { supabase } from '../supabaseClient';
import { logger } from '../utils/logger';
import { DatabaseError, validateUUID, validateRequired } from '../utils/errorHandler';

export async function getRecommendations(
  studentId: string,
  contextState: object,
  options: {
    sessionId?: string;
    recommendationType?: string;
    maxRecommendations?: number;
  } = {}
) {
  try {
    // Validate inputs
    validateRequired({ studentId }, ['studentId']);
    validateUUID(studentId, 'studentId');

    const {
      sessionId,
      recommendationType = 'next_questions',
      maxRecommendations = 10
    } = options;

    logger.info('Generating recommendations via RPC', {
      studentId,
      recommendationType,
      maxRecommendations
    });

    // Call the recommendation RPC
    const { data, error } = await supabase.rpc('recommend_questions_linucb', {
      p_student_id: studentId,
      p_context: contextState,
      p_limit: maxRecommendations
    });
    
    if (error) {
      logger.error('RPC error in recommendation service', { error: error.message });
      throw new DatabaseError(`Recommendation RPC failed: ${error.message}`);
    }

    const questions: string[] = data?.questions || [];
    const rationale = data?.rationale || [];
    
    // Prepare audit log payload
    const payload = {
      context_state: contextState,
      questions: questions,
      algorithm: 'contextual_bandit_v0',
      version: 'v0.1',
      confidence: '0.75',
      type: recommendationType,
      model_params: {
        mastery_threshold: 0.8,
        novelty_weight: 0.4,
        recency_weight: 0.2
      },
      expected_gain: '0.15'
    };

    // Write audit log
    const { data: logId, error: logError } = await supabase.rpc('write_recommendation_log', {
      p_student_id: studentId,
      p_payload: payload
    });

    if (logError) {
      logger.warn('Failed to write recommendation log', { error: logError.message });
      // Continue without failing the request
    } else {
      logger.info('Recommendation logged successfully', {
        studentId,
        logId,
        questionCount: questions.length
      });
    }

    return {
      success: true,
      questions: questions,
      rationale: rationale,
      algorithm_used: 'contextual_bandit_v0',
      confidence: 0.75,
      recommendation_id: logId,
      session_id: sessionId,
      total_recommendations: questions.length
    };

  } catch (error) {
    logger.error('Error in recommendation service', {
      studentId,
      error: error.message,
      stack: error.stack
    });
    throw new DatabaseError(`Failed to generate recommendations: ${error.message}`);
  }
}
