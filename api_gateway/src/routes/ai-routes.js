// Enhanced API Gateway Routes for AI Engine Integration
// Adds routing for BKT and Time Context services

const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const rateLimit = require('express-rate-limit');
const router = express.Router();

// Rate limiting for AI endpoints
const aiRateLimit = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many AI requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});

// BKT Engine routes
router.use('/api/v1/bkt', aiRateLimit);
router.use('/api/v1/bkt', createProxyMiddleware({
  target: process.env.AI_ENGINE_URL || 'http://ai-engine:8005',
  changeOrigin: true,
  pathRewrite: {
    '^/api/v1/bkt': '/bkt'
  },
  onError: (err, req, res) => {
    console.error('BKT proxy error:', err);
    res.status(503).json({ error: 'BKT service unavailable' });
  }
}));

// Time Context routes
router.use('/api/v1/time-context', aiRateLimit);
router.use('/api/v1/time-context', createProxyMiddleware({
  target: process.env.TIME_CONTEXT_URL || 'http://time-context:8006',
  changeOrigin: true,
  pathRewrite: {
    '^/api/v1/time-context': ''
  },
  onError: (err, req, res) => {
    console.error('Time Context proxy error:', err);
    res.status(503).json({ error: 'Time Context service unavailable' });
  }
}));

// Integrated AI Intelligence endpoint
router.use('/api/v1/ai-intelligence', aiRateLimit);
router.use('/api/v1/ai-intelligence', createProxyMiddleware({
  target: process.env.AI_ENGINE_URL || 'http://ai-engine:8005',
  changeOrigin: true,
  pathRewrite: {
    '^/api/v1/ai-intelligence': '/integrated'
  },
  onError: (err, req, res) => {
    console.error('AI Intelligence proxy error:', err);
    res.status(503).json({ error: 'AI Intelligence service unavailable' });
  }
}));

// Health check aggregation
router.get('/api/v1/ai-health', async (req, res) => {
  try {
    const axios = require('axios');
    
    const [bktHealth, timeHealth] = await Promise.allSettled([
      axios.get(`${process.env.AI_ENGINE_URL || 'http://ai-engine:8005'}/health`),
      axios.get(`${process.env.TIME_CONTEXT_URL || 'http://time-context:8006'}/health`)
    ]);
    
    res.json({
      timestamp: new Date().toISOString(),
      services: {
        bkt_engine: bktHealth.status === 'fulfilled' ? 'healthy' : 'unhealthy',
        time_context: timeHealth.status === 'fulfilled' ? 'healthy' : 'unhealthy'
      },
      overall_status: (bktHealth.status === 'fulfilled' && timeHealth.status === 'fulfilled') ? 'healthy' : 'degraded'
    });
  } catch (error) {
    res.status(503).json({
      timestamp: new Date().toISOString(),
      error: 'Health check failed',
      services: {
        bkt_engine: 'unknown',
        time_context: 'unknown'
      },
      overall_status: 'unhealthy'
    });
  }
});

module.exports = router;