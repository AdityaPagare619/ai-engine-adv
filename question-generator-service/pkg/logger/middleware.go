package logger

import (
	"context"
	"log"
	"net/http"
	"time"
	
	"question-generator-service/internal/db"
)

// LogRequest is a middleware that sets up request logging context
func (s *GenlogService) LogRequest(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		startTime := time.Now()
		
		// Add logger service to context for use in handlers
		ctx := context.WithValue(r.Context(), "logger_service", s)
		ctx = context.WithValue(ctx, "request_start_time", startTime)
		
		log.Printf("Logger: Request started - Method=%s Path=%s", r.Method, r.URL.Path)
		
		// Call next handler
		next.ServeHTTP(w, r.WithContext(ctx))
		
		// Log completion
		duration := time.Since(startTime)
		log.Printf("Logger: Request completed - Method=%s Path=%s Duration=%s", 
			r.Method, r.URL.Path, duration)
	})
}

// CreateGenerationLogFromContext creates a generation log from request context
func (s *GenlogService) CreateGenerationLogFromContext(ctx context.Context) *db.GenerationLog {
	// Extract validated request from context
	validatedRequest := ctx.Value("validated_request")
	if validatedRequest == nil {
		return nil
	}
	
	// Extract request ID from context
	requestID := ctx.Value("request_id")
	var reqIDStr string
	if requestID != nil {
		reqIDStr = requestID.(string)
	}
	
	// Extract start time
	startTime := ctx.Value("request_start_time")
	var startTimeVal time.Time
	if startTime != nil {
		startTimeVal = startTime.(time.Time)
	}
	
	// Create basic generation log structure
	genLog := &db.GenerationLog{
		RequestID:        reqIDStr,
		Status:          "PENDING",
		GeneratorVersion: "v1.0.0",
		ModelVersion:    "template-v1",
	}
	
	// Set timing if available
	if !startTimeVal.IsZero() {
		elapsed := time.Since(startTimeVal)
		genLog.TotalPipelineTimeMs = int(elapsed.Milliseconds())
	}
	
	return genLog
}

// LogGeneration logs the generation process with all details
func (s *GenlogService) LogGeneration(ctx context.Context, log *db.GenerationLog) error {
	if log == nil {
		log.Printf("Warning: Attempted to log nil generation log")
		return nil
	}
	
	// Create or update the generation log
	if log.ID == 0 {
		return s.CreateGenerationLog(ctx, log)
	} else {
		return s.UpdateGenerationLog(ctx, log)
	}
}