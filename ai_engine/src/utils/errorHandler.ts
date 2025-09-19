import { Request, Response, NextFunction } from 'express';
import { logger } from './logger';
import { APIResponse } from './types';

// Custom error classes
export class ValidationError extends Error {
  public statusCode = 400;
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

export class DatabaseError extends Error {
  public statusCode = 500;
  constructor(message: string) {
    super(message);
    this.name = 'DatabaseError';
  }
}

// Error handling middleware
export function errorHandler(error: Error, req: Request, res: Response, next: NextFunction) {
  logger.error('Error occurred', {
    error: error.message,
    stack: error.stack,
    url: req.url,
    method: req.method
  });

  let statusCode = 500;
  let message = 'Internal server error';

  if (error instanceof ValidationError) {
    statusCode = 400;
    message = error.message;
  } else if (error instanceof DatabaseError) {
    statusCode = 500;
    message = 'Database operation failed';
  }

  const response: APIResponse = {
    success: false,
    error: message,
    timestamp: new Date()
  };

  res.status(statusCode).json(response);
}

// Async error wrapper
export function asyncHandler(fn: Function) {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

// Validation helpers
export function validateRequired(data: any, requiredFields: string[]): void {
  const missingFields = requiredFields.filter(field => {
    const value = data[field];
    return value === undefined || value === null || value === '';
  });

  if (missingFields.length > 0) {
    throw new ValidationError(`Missing required fields: ${missingFields.join(', ')}`);
  }
}

export function validateUUID(value: string, fieldName: string): void {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!uuidRegex.test(value)) {
    throw new ValidationError(`${fieldName} must be a valid UUID`);
  }
}