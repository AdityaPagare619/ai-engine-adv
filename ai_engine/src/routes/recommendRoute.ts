import { Router } from 'express';
import { getRecommendations } from '../services/recommendService';
import { asyncHandler } from '../utils/errorHandler';
import { APIResponse } from '../utils/types';
const router = Router();

router.post('/ai/recommend', asyncHandler(async (req, res) => {
  const { 
    studentId, 
    contextState = {}, 
    sessionId, 
    recommendationType = 'next_questions', 
    maxRecommendations = 5 
  } = req.body;
  
  const recommendations = await getRecommendations(studentId, contextState, {
    sessionId,
    recommendationType,
    maxRecommendations
  });
  
  const response: APIResponse = {
    success: true,
    data: recommendations,
    timestamp: new Date()
  };
  
  res.json(response);
}));

// Health check endpoint
router.get('/ai/recommend/health', (req, res) => {
  const response: APIResponse = {
    success: true,
    data: { 
      service: 'recommendation-service',
      status: 'healthy',
      version: '1.0'
    },
    timestamp: new Date()
  };
  res.json(response);
});

export default router;
