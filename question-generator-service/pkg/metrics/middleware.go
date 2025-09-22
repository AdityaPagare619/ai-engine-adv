package metrics

import (
	"net/http"
	"sync"
	"sync/atomic"
	"time"
)

// Global metrics counters
var (
	TotalRequests      int64
	SuccessfulRequests int64
	FailedRequests     int64
	TotalResponseTime  int64 // in milliseconds
	ValidationErrors   int64
	RAGChecks          int64
	BKTCalls           int64
	ActiveConnections  int64
	QuestionsGenerated int64
	StartTime          = time.Now()
	mutex              sync.RWMutex
)

// MetricsMiddleware tracks HTTP request metrics
func MetricsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		startTime := time.Now()
		
		// Track active connections
		atomic.AddInt64(&ActiveConnections, 1)
		defer atomic.AddInt64(&ActiveConnections, -1)
		
		// Track total requests
		atomic.AddInt64(&TotalRequests, 1)
		
		// Create response writer wrapper to capture status
		wrapper := &responseWriter{ResponseWriter: w, statusCode: 200}
		
		// Process request
		next.ServeHTTP(wrapper, r)
		
		// Track response time
		duration := time.Since(startTime)
		atomic.AddInt64(&TotalResponseTime, duration.Milliseconds())
		
		// Track success/failure
		if wrapper.statusCode >= 200 && wrapper.statusCode < 400 {
			atomic.AddInt64(&SuccessfulRequests, 1)
			
			// Track questions generated for generation endpoints
			if r.URL.Path == "/v1/questions/generate" && wrapper.statusCode == 200 {
				atomic.AddInt64(&QuestionsGenerated, 1)
			}
		} else {
			atomic.AddInt64(&FailedRequests, 1)
		}
	})
}

// responseWriter wrapper to capture status code
type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

// Increment validation errors counter
func IncrementValidationErrors() {
	atomic.AddInt64(&ValidationErrors, 1)
}

// Increment RAG checks counter
func IncrementRAGChecks() {
	atomic.AddInt64(&RAGChecks, 1)
}

// Increment BKT calls counter
func IncrementBKTCalls() {
	atomic.AddInt64(&BKTCalls, 1)
}

// GetMetricsSummary returns current metrics summary
func GetMetricsSummary() map[string]interface{} {
	mutex.RLock()
	defer mutex.RUnlock()
	
	uptime := time.Since(StartTime).Seconds()
	totalReqs := atomic.LoadInt64(&TotalRequests)
	successReqs := atomic.LoadInt64(&SuccessfulRequests)
	totalRespTime := atomic.LoadInt64(&TotalResponseTime)
	
	avgResponseTime := float64(0)
	if totalReqs > 0 {
		avgResponseTime = float64(totalRespTime) / float64(totalReqs)
	}
	
	successRate := float64(0)
	if totalReqs > 0 {
		successRate = float64(successReqs) / float64(totalReqs) * 100
	}
	
	return map[string]interface{}{
		"uptime_seconds":        uptime,
		"total_requests":        totalReqs,
		"successful_requests":   successReqs,
		"failed_requests":       atomic.LoadInt64(&FailedRequests),
		"avg_response_time_ms":  avgResponseTime,
		"success_rate":          successRate,
		"validation_errors":     atomic.LoadInt64(&ValidationErrors),
		"rag_checks":            atomic.LoadInt64(&RAGChecks),
		"bkt_calls":             atomic.LoadInt64(&BKTCalls),
		"active_connections":    atomic.LoadInt64(&ActiveConnections),
		"questions_generated":   atomic.LoadInt64(&QuestionsGenerated),
		"requests_per_second":   float64(totalReqs) / uptime,
	}
}