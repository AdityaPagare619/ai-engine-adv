import { Router } from 'express';
import { predictScore } from '../services/predictService';
import { asyncHandler } from '../utils/errorHandler';
import { APIResponse } from '../utils/types';
const router = Router();

router.post('/ai/predict', asyncHandler(async (req, res) => {
  const { 
    studentId, 
    predictionType = 'exam_score', 
    horizonDays = 90,
    features = {}
  } = req.body;
  
  const prediction = await predictScore(studentId, predictionType, horizonDays, features);
  
  const response: APIResponse = {
    success: true,
    data: prediction,
    timestamp: new Date()
  };
  
  res.json(response);
}));

// Health check endpoint
router.get('/ai/predict/health', (req, res) => {
  const response: APIResponse = {
    success: true,
    data: { 
      service: 'prediction-service',
      status: 'healthy',
      version: '1.0'
    },
    timestamp: new Date()
  };
  res.json(response);
});

export default router;
