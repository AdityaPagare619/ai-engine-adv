import fs from 'fs';
import path from 'path';
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import dotenv from 'dotenv';

import traceRoute from './routes/traceRoute';
import recommendRoute from './routes/recommendRoute';
import predictRoute from './routes/predictRoute';
import { pool } from './supabaseClient';
import { errorHandler } from './utils/errorHandler';
import { logger } from './utils/logger';
import { APIResponse } from './utils/types';

// Load environment variables
dotenv.config();

// Run SQL migrations
async function runMigrations() {
  const schemaDir = path.join(__dirname, 'schema');
  
  if (!fs.existsSync(schemaDir)) {
    logger.warn('Schema directory not found, skipping migrations');
    return;
  }

  const files = fs.readdirSync(schemaDir).filter(f => f.endsWith('.sql')).sort();
  
  if (files.length === 0) {
    logger.info('No migration files found');
    return;
  }

  const client = await pool.connect();
  
  try {
    for (const file of files) {
      const sqlPath = path.join(schemaDir, file);
      const sql = fs.readFileSync(sqlPath, 'utf8');
      
      logger.info(`Running migration: ${file}`);
      
      try {
        await client.query(sql);
        logger.info(`Migration completed: ${file}`);
      } catch (error) {
        logger.error(`Migration failed: ${file}`, { error: error.message });
        // Continue with other migrations instead of failing completely
      }
    }
    logger.info('All migrations processed');
  } finally {
    client.release();
  }
}

// Test database connection
async function testConnection() {
  try {
    const client = await pool.connect();
    const result = await client.query('SELECT NOW() as current_time');
    logger.info('Database connection successful', { 
      currentTime: result.rows[0].current_time 
    });
    client.release();
  } catch (error) {
    logger.error('Database connection failed', { error: error.message });
    throw error;
  }
}

// Start Express server
async function startServer() {
  const app = express();
  const port = process.env.PORT || 8005;
  
  // Security middleware
  app.use(helmet());
  app.use(cors({
    origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
    credentials: true
  }));
  
  // Logging middleware
  app.use(morgan('combined', {
    stream: {
      write: (message) => logger.info(message.trim())
    }
  }));
  
  // Body parsing middleware
  app.use(express.json({ limit: '10mb' }));
  app.use(express.urlencoded({ extended: true, limit: '10mb' }));
  
  // Health check endpoint
  app.get('/health', (req, res) => {
    const response: APIResponse = {
      success: true,
      data: {
        service: 'ai-engine',
        status: 'healthy',
        version: '1.0',
        timestamp: new Date(),
        uptime: process.uptime()
      },
      timestamp: new Date()
    };
    res.json(response);
  });
  
  // API routes
  app.use('/api', traceRoute);
  app.use('/api', recommendRoute);
  app.use('/api', predictRoute);
  
  // 404 handler
  app.use('*', (req, res) => {
    const response: APIResponse = {
      success: false,
      error: 'Endpoint not found',
      timestamp: new Date()
    };
    res.status(404).json(response);
  });
  
  // Global error handler
  app.use(errorHandler);
  
  // Start server
  app.listen(port, () => {
    logger.info(`AI Engine server started`, {
      port: port,
      environment: process.env.NODE_ENV || 'development',
      pid: process.pid
    });
  });
  
  // Graceful shutdown
  process.on('SIGTERM', async () => {
    logger.info('Received SIGTERM, shutting down gracefully');
    await pool.end();
    process.exit(0);
  });
  
  process.on('SIGINT', async () => {
    logger.info('Received SIGINT, shutting down gracefully');
    await pool.end();
    process.exit(0);
  });
}

// Initialize application
async function init() {
  try {
    logger.info('Starting AI Engine initialization...');
    
    // Test database connection
    await testConnection();
    
    // Run migrations
    await runMigrations();
    
    // Start server
    await startServer();
    
  } catch (error) {
    logger.error('Failed to initialize AI Engine', { error: error.message });
    process.exit(1);
  }
}

// Start the application
init();
