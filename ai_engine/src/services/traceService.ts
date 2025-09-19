import { supabase } from '../supabaseClient';
import { logger } from '../utils/logger';
import { DatabaseError, validateUUID, validateRequired } from '../utils/errorHandler';

export async function updateKnowledgeState(
  studentId: string,
  conceptId: string,
  isCorrect: boolean,
  responseTimeMs?: number
) {
  try {
    // Validate inputs
    validateRequired({ studentId, conceptId, isCorrect }, ['studentId', 'conceptId', 'isCorrect']);
    validateUUID(studentId, 'studentId');
    validateUUID(conceptId, 'conceptId');
    
    if (typeof isCorrect !== 'boolean') {
      throw new DatabaseError('isCorrect must be a boolean value');
    }

    logger.info('Updating knowledge state via BKT RPC', {
      studentId,
      conceptId,
      isCorrect,
      responseTimeMs
    });

    // Call the BKT update RPC
    const { data, error } = await supabase.rpc('update_knowledge_state_bkt', {
      p_student_id: studentId,
      p_concept_id: conceptId,
      p_is_correct: isCorrect,
      p_response_time_ms: responseTimeMs || null
    });
    
    if (error) {
      logger.error('BKT RPC error', { 
        error: error.message, 
        studentId, 
        conceptId 
      });
      throw new DatabaseError(`BKT update failed: ${error.message}`);
    }

    if (!data) {
      throw new DatabaseError('BKT update function returned no result');
    }

    logger.info('Knowledge state updated successfully via RPC', {
      studentId,
      conceptId,
      previousMastery: data.previous_mastery,
      newMastery: data.new_mastery,
      learningOccurred: data.learning_occurred,
      confidenceChange: data.confidence_change
    });

    return {
      success: true,
      student_id: studentId,
      concept_id: conceptId,
      previous_mastery: data.previous_mastery,
      new_mastery: data.new_mastery,
      learning_occurred: data.learning_occurred,
      confidence_change: data.confidence_change,
      mastery_improvement: data.new_mastery - data.previous_mastery,
      updated_at: new Date(),
      response_time_ms: responseTimeMs,
      algorithm_version: 'BKT_v1.0'
    };

  } catch (error) {
    logger.error('Error in knowledge tracing service', {
      studentId,
      conceptId,
      error: error.message,
      stack: error.stack
    });
    throw new DatabaseError(`Failed to update knowledge state: ${error.message}`);
  }
}
