const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const router = express.Router();

const services = {
  admin: 'http://admin-service:8001',
  content: 'http://content-processor:8002',
  asset: 'http://asset-processor:8003',
  database: 'http://database-manager:8004'
};

// Dynamic proxy middleware
Object.entries(services).forEach(([key, target]) => {
  router.use(`/${key}`, createProxyMiddleware({
    target,
    changeOrigin: true,
    pathRewrite: {
      [`^/${key}`]: ''
    },
    onProxyReq(proxyReq, req, res) {
      proxyReq.setHeader('X-Correlation-ID', req.correlationId);
    }
  }));
});

module.exports = router;
