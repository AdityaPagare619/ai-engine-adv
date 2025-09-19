import { supabase } from '../supabaseClient';
import { logger } from '../utils/logger';
import { DatabaseError } from '../utils/errorHandler';

// Performance monitoring interface
interface PerformanceMetrics {
  serviceLatency: number;
  databaseLatency: number;
  memoryUsage: number;
  cpuUsage: number;
  activeConnections: number;
}

// System event logging
export async function logSystemEvent(
  eventType: string,
  eventSource: string,
  eventPayload: object,
  studentContext?: string,
  sessionContext?: string
) {
  try {
    const { data, error } = await supabase.from('system_events').insert({
      event_type: eventType,
      event_source: eventSource,
      event_payload: eventPayload,
      student_context: studentContext,
      session_context: sessionContext,
      event_timestamp: new Date().toISOString(),
      processing_status: 'completed'
    });

    if (error) {
      logger.error('Failed to log system event', {
        eventType,
        eventSource,
        error: error.message
      });
      return null;
    }

    return data;
  } catch (error) {
    logger.error('Error in telemetry service', {
      eventType,
      error: error.message
    });
    return null;
  }
}

// Model performance tracking
export async function trackModelPerformance(
  modelName: string,
  modelVersion: string,
  metricName: string,
  metricValue: number,
  evaluationContext?: object
) {
  try {
    const { data, error } = await supabase.from('ai_model_performance').insert({
      model_name: modelName,
      model_version: modelVersion,
      metric_name: metricName,
      metric_value: metricValue,
      evaluation_period_start: new Date().toISOString(),
      evaluation_period_end: new Date().toISOString(),
      evaluation_metadata: evaluationContext || {}
    });

    if (error) {
      logger.error('Failed to track model performance', {
        modelName,
        metricName,
        error: error.message
      });
      return null;
    }

    logger.debug('Model performance tracked', {
      modelName,
      modelVersion,
      metricName,
      metricValue
    });

    return data;
  } catch (error) {
    logger.error('Error tracking model performance', {
      modelName,
      error: error.message
    });
    return null;
  }
}

// Service health monitoring
export async function getServiceHealth() {
  try {
    const startTime = Date.now();
    
    // Test database connection
    const { data: dbTest, error: dbError } = await supabase
      .from('student_profiles')
      .select('id')
      .limit(1);
    
    const dbLatency = Date.now() - startTime;
    
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      database: {
        connected: !dbError,
        latency: dbLatency,
        error: dbError?.message || null
      },
      memory: {
        used: process.memoryUsage().heapUsed / 1024 / 1024, // MB
        total: process.memoryUsage().heapTotal / 1024 / 1024, // MB
        external: process.memoryUsage().external / 1024 / 1024 // MB
      },
      process: {
        uptime: process.uptime(),
        pid: process.pid,
        version: process.version,
        platform: process.platform
      }
    };

    // Log health check event
    await logSystemEvent(
      'health_check',
      'telemetry_service',
      health
    );

    return health;
  } catch (error) {
    logger.error('Error checking service health', {
      error: error.message
    });
    
    return {
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error.message
    };
  }
}

// Usage analytics
export async function trackUsage(
  endpoint: string,
  method: string,
  statusCode: number,
  responseTime: number,
  studentId?: string
) {
  try {
    const usageData = {
      endpoint,
      method,
      status_code: statusCode,
      response_time_ms: responseTime,
      student_id: studentId,
      timestamp: new Date().toISOString(),
      user_agent: 'ai-engine-service',
      ip_address: '127.0.0.1' // Internal service
    };

    await logSystemEvent(
      'api_usage',
      'ai_engine',
      usageData,
      studentId
    );

    logger.debug('Usage tracked', {
      endpoint,
      method,
      statusCode,
      responseTime
    });

  } catch (error) {
    logger.error('Error tracking usage', {
      endpoint,
      error: error.message
    });
  }
}

// Algorithm performance monitoring
export async function trackAlgorithmPerformance(
  algorithmName: string,
  operation: string,
  executionTime: number,
  accuracy?: number,
  studentId?: string
) {
  try {
    const performanceData = {
      algorithm: algorithmName,
      operation,
      execution_time_ms: executionTime,
      accuracy: accuracy || null,
      student_context: studentId,
      timestamp: new Date().toISOString()
    };

    await logSystemEvent(
      'algorithm_performance',
      'ai_engine',
      performanceData,
      studentId
    );

    // Track specific metrics for model performance table
    if (accuracy !== undefined) {
      await trackModelPerformance(
        algorithmName,
        'v1.0',
        'accuracy',
        accuracy,
        { operation, execution_time: executionTime }
      );
    }

    await trackModelPerformance(
      algorithmName,
      'v1.0',
      'execution_time',
      executionTime,
      { operation }
    );

  } catch (error) {
    logger.error('Error tracking algorithm performance', {
      algorithmName,
      operation,
      error: error.message
    });
  }
}

// Error tracking and analysis
export async function trackError(
  errorType: string,
  errorMessage: string,
  errorStack?: string,
  context?: object,
  studentId?: string
) {
  try {
    const errorData = {
      error_type: errorType,
      error_message: errorMessage,
      error_stack: errorStack,
      context: context || {},
      timestamp: new Date().toISOString(),
      service: 'ai-engine',
      student_id: studentId
    };

    await logSystemEvent(
      'error_occurred',
      'ai_engine',
      errorData,
      studentId
    );

    logger.error('Error tracked in telemetry', {
      errorType,
      errorMessage,
      context
    });

  } catch (error) {
    logger.error('Failed to track error in telemetry', {
      originalError: errorMessage,
      telemetryError: error.message
    });
  }
}

// Get system metrics for monitoring dashboard
export async function getSystemMetrics(timeRangeHours: number = 24) {
  try {
    const startTime = new Date(Date.now() - timeRangeHours * 60 * 60 * 1000).toISOString();
    
    // Get recent system events
    const { data: events, error } = await supabase
      .from('system_events')
      .select('event_type, event_source, created_at')
      .gte('event_timestamp', startTime)
      .order('event_timestamp', { ascending: false })
      .limit(1000);

    if (error) {
      throw new DatabaseError(`Failed to fetch system metrics: ${error.message}`);
    }

    // Aggregate metrics
    const eventTypes = events?.reduce((acc, event) => {
      acc[event.event_type] = (acc[event.event_type] || 0) + 1;
      return acc;
    }, {}) || {};

    const eventSources = events?.reduce((acc, event) => {
      acc[event.event_source] = (acc[event.event_source] || 0) + 1;
      return acc;
    }, {}) || {};

    return {
      total_events: events?.length || 0,
      event_types: eventTypes,
      event_sources: eventSources,
      time_range_hours: timeRangeHours,
      generated_at: new Date().toISOString()
    };

  } catch (error) {
    logger.error('Error getting system metrics', {
      error: error.message
    });
    throw new DatabaseError(`Failed to get system metrics: ${error.message}`);
  }
}
