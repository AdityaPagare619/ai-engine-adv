require('dotenv').config();
const express = require('express');
const helmet = require('helmet');
const morgan = require('morgan');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const jwt = require('jsonwebtoken');
const jwksRsa = require('jwks-rsa');
const { createProxyMiddleware } = require('http-proxy-middleware');
const pino = require('pino');
const pinoHttp = require('pino-http');
const { v4: uuidv4 } = require('uuid');

const app = express();
const logger = pino({ level: process.env.LOG_LEVEL || 'info' });
app.use(pinoHttp({ logger }));

// Security headers
app.use(helmet());

// CORS policy
app.use(cors({
  origin: ['https://trusted-frontend.domain.com'],
  methods: ['GET','POST','PUT','DELETE','OPTIONS'],
  allowedHeaders: ['Authorization','Content-Type','X-Correlation-ID'],
  credentials: true
}));

// Logging request bodies (be cautious with sensitive data)
app.use(express.json({ limit: '1mb' }));

// Global correlation ID middleware
app.use((req, res, next) => {
  const corrId = req.header('X-Correlation-ID') || uuidv4();
  req.correlationId = corrId;
  res.setHeader('X-Correlation-ID', corrId);
  req.log = logger.child({ correlationId: corrId });
  next();
});

// JWT validation with JWKS & key rotation
const jwtCheck = (req, res, next) => {
  const token = req.header('Authorization')?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'Authorization token missing' });

  // Configure JWKS client (for key rotation)
  const client = jwksRsa({
    jwksUri: process.env.JWKS_URI,
    cache: true,
    rateLimit: true,
    cacheMaxEntries: 5,
    cacheMaxAge: 3600000
  });

  function getKey(header, callback) {
    client.getSigningKey(header.kid, (err, key) => {
      if (err) {
        req.log.error({ err }, 'Failed to get signing key');
        return callback(err);
      }
      const signingKey = key.getPublicKey();
      callback(null, signingKey);
    });
  }

  jwt.verify(token, getKey, { algorithms: ['RS256'] }, (err, decoded) => {
    if (err) {
      req.log.warn({ err }, 'JWT verification failed');
      return res.status(401).json({ error: 'Invalid token' });
    }
    req.user = decoded;
    next();
  });
};

app.use(jwtCheck);

// Rate limiting
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 mins
  max: 500,
  standardHeaders: true,
  legacyHeaders: false,
  message: 'Too many requests, please try again later.'
});
app.use('/api/', apiLimiter);

// Proxy mappings
const services = {
  admin: process.env.ADMIN_API_URL,
  content: process.env.CONTENT_API_URL,
  asset: process.env.ASSET_API_URL,
  database: process.env.DB_API_URL
};

Object.entries(services).forEach(([prefix, target]) => {
  app.use(`/${prefix}`, createProxyMiddleware({
    target,
    changeOrigin: true,
    secure: true,
    pathRewrite: { [`^/${prefix}`]: '' },
    onProxyReq: (proxyReq, req) => {
      // Inject correlation ID header
      proxyReq.setHeader('X-Correlation-ID', req.correlationId);
      // Optionally pass user info for RBAC downstream
      if (req.user) {
        proxyReq.setHeader('X-User-ID', req.user.sub || '');
        proxyReq.setHeader('X-User-Role', req.user.role || '');
      }
      req.log.info({ url: req.url, method: req.method }, 'Proxying request');
    }
  }));
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'api-gateway' });
});

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  logger.info(`API Gateway listening on port ${PORT}`);
});
