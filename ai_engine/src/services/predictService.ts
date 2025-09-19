import { supabase } from '../supabaseClient';
import { logger } from '../utils/logger';
import { DatabaseError, validateUUID, validateRequired } from '../utils/errorHandler';

export async function predictScore(
  studentId: string,
  predictionType: string = 'exam_score',
  horizonDays: number = 90,
  features: object = {}
) {
  try {
    // Validate inputs
    validateRequired({ studentId, predictionType }, ['studentId', 'predictionType']);
    validateUUID(studentId, 'studentId');

    logger.info('Generating score prediction via RPC', {
      studentId,
      predictionType,
      horizonDays
    });

    // Call the prediction RPC
    const { data, error } = await supabase.rpc('predict_exam_score', {
      p_student_id: studentId,
      p_features: features
    });
    
    if (error) {
      logger.error('RPC error in prediction service', { error: error.message });
      throw new DatabaseError(`Prediction RPC failed: ${error.message}`);
    }

    const predictedScore = data?.predicted_score || 0;
    const confidence = data?.confidence || 0.65;
    const masteryStats = data?.mastery_stats || {};
    
    // Calculate subject-wise breakdown
    const subjectPredictions = {
      mathematics: Math.round(predictedScore * 0.35),
      physics: Math.round(predictedScore * 0.35),
      chemistry: Math.round(predictedScore * 0.30)
    };

    // Calculate risk scores based on mastery stats
    const avgMastery = masteryStats.avg_mastery || 0.1;
    const masteryRatio = masteryStats.mastery_ratio || 0;
    const dropoutRisk = Math.max(0, Math.min(1, 1 - avgMastery - masteryRatio * 0.3));
    const burnoutRisk = masteryStats.total_concepts > 100 ? 0.2 : 0.1;
    
    // Prepare audit log payload
    const payload = {
      type: predictionType,
      horizon_days: horizonDays,
      confidence: confidence.toString(),
      predicted_score: predictedScore.toString(),
      percentile: Math.round((predictedScore / 300) * 100).toString(),
      model_name: 'baseline_avg_mastery',
      model_version: 'v0.1',
      feature_importance: {
        mastery_weight: 0.6,
        consistency_weight: 0.4
      },
      context: {
        mastery_stats: masteryStats,
        risk_scores: {
          dropout_risk: dropoutRisk,
          burnout_risk: burnoutRisk
        }
      }
    };

    // Write audit log
    const { data: logId, error: logError } = await supabase.rpc('write_prediction_log', {
      p_student_id: studentId,
      p_payload: payload
    });

    if (logError) {
      logger.warn('Failed to write prediction log', { error: logError.message });
      // Continue without failing the request
    } else {
      logger.info('Prediction logged successfully', {
        studentId,
        logId,
        predictedScore,
        confidence
      });
    }

    return {
      success: true,
      prediction_id: logId,
      predicted_score: predictedScore,
      confidence: confidence,
      prediction_type: predictionType,
      horizon_days: horizonDays,
      subject_predictions: subjectPredictions,
      risk_assessment: {
        dropout_risk: dropoutRisk,
        burnout_risk: burnoutRisk
      },
      mastery_analysis: masteryStats,
      model_info: {
        name: 'baseline_avg_mastery',
        version: 'v0.1',
        algorithm: 'mastery_weighted_scoring'
      },
      percentile_estimate: Math.round((predictedScore / 300) * 100)
    };

  } catch (error) {
    logger.error('Error in prediction service', {
      studentId,
      error: error.message,
      stack: error.stack
    });
    throw new DatabaseError(`Failed to generate prediction: ${error.message}`);
  }
}
