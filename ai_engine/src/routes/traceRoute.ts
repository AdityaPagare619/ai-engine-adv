import { Router } from 'express';
import { updateKnowledgeState } from '../services/traceService';
import { asyncHandler } from '../utils/errorHandler';
import { APIResponse } from '../utils/types';
const router = Router();

router.post('/ai/trace', asyncHandler(async (req, res) => {
  const { studentId, conceptId, correct, responseTimeMs } = req.body;
  
  const result = await updateKnowledgeState(studentId, conceptId, correct, responseTimeMs);
  
  const response: APIResponse = {
    success: true,
    data: result,
    timestamp: new Date()
  };
  
  res.json(response);
}));

// Health check endpoint
router.get('/ai/trace/health', (req, res) => {
  const response: APIResponse = {
    success: true,
    data: { 
      service: 'knowledge-tracing-service',
      status: 'healthy',
      version: '1.0'
    },
    timestamp: new Date()
  };
  res.json(response);
});

export default router;
