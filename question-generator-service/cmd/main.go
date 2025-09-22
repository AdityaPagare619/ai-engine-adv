package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/gorilla/mux"
	"github.com/rs/cors"

	"question-generator-service/internal/config"
	"question-generator-service/internal/db"
	"question-generator-service/internal/service"
	"question-generator-service/api"
	"question-generator-service/pkg/validator"
	"question-generator-service/pkg/rag_advisor"
	"question-generator-service/pkg/logger"
)

const (
	serviceName    = "question-generator"
	serviceVersion = "v1.0.0"
)

func main() {
	log.Printf("Starting %s service %s", serviceName, serviceVersion)

	// Load configuration from environment variables
	cfg, err := config.LoadConfig()
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Initialize database client with connection pooling
	dbClient, err := db.NewClient(cfg.Database)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer dbClient.Close()

	// Run database migrations
	if err := dbClient.RunMigrations(); err != nil {
		log.Fatalf("Failed to run database migrations: %v", err)
	}

	// Initialize question generation service with all dependencies
	generatorService, err := service.NewGeneratorService(cfg, dbClient)
	if err != nil {
		log.Fatalf("Failed to initialize generator service: %v", err)
	}

	// Initialize middleware with configuration
	middlewareConfig := api.MiddlewareConfig{
		RateLimitPerMinute: 1000, // 1000 requests per minute per IP
		AuthEnabled:        false, // Disable auth for Phase 2.2
		AuthHeader:         "Authorization",
		TokenPrefix:        "Bearer",
	}
	middleware := api.NewMiddleware(middlewareConfig)

	// Initialize logger service
	loggerService, err := logger.NewService(dbClient)
	if err != nil {
		log.Fatalf("Failed to initialize logger service: %v", err)
	}

	// Set up HTTP handlers and middleware chain
	router := mux.NewRouter()
	
	// Apply global middleware
	router.Use(middleware.RequestLogger)
	router.Use(middleware.RecoverMiddleware)
	router.Use(middleware.RateLimitByIP)
	
	// Add service discovery and health check endpoints
	router.HandleFunc("/health", healthCheckHandler).Methods("GET")
	router.HandleFunc("/ready", readinessCheckHandler(dbClient)).Methods("GET")
	router.HandleFunc("/metrics", metricsHandler).Methods("GET")
	
	// Mount API routes with versioning
	apiRouter := router.PathPrefix("/v1").Subrouter()
	
	// Add specific endpoint with middleware chain as per guide
	apiRouter.Handle("/questions/generate",
		middleware.RequestLogger(
			validator.ValidateGenerateQuestionRequest(
				rag_advisor.AdviseQuality(
					loggerService.LogRequest(
						http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
							// Call the generator service method
							handleGenerateQuestion(generatorService, w, r)
						}),
					),
				),
			),
		),
	).Methods("POST")
	
	// Register other handlers
	api.RegisterHandlers(apiRouter, generatorService)

	// Configure CORS for cross-origin requests
	corsHandler := cors.New(cors.Options{
		AllowedOrigins:   cfg.Server.AllowedOrigins,
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Content-Type", "Authorization", "X-Request-ID"},
		ExposedHeaders:   []string{"X-Request-ID", "X-Generation-Time"},
		AllowCredentials: true,
		MaxAge:           300, // 5 minutes preflight cache
	}).Handler(router)

	// Create HTTP server with production-ready timeouts
	server := &http.Server{
		Addr:         fmt.Sprintf(":%d", cfg.Server.Port),
		Handler:      corsHandler,
		ReadTimeout:  cfg.Server.ReadTimeout,
		WriteTimeout: cfg.Server.WriteTimeout,
		IdleTimeout:  cfg.Server.IdleTimeout,
	}

	// Start server in a goroutine
	go func() {
		log.Printf("Server listening on port %d", cfg.Server.Port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Server failed to start: %v", err)
		}
	}()

	// Wait for interrupt signal for graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down server gracefully...")

	// Create shutdown context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Attempt graceful shutdown
	if err := server.Shutdown(ctx); err != nil {
		log.Printf("Server forced to shutdown: %v", err)
	}

	log.Println("Server exited successfully")
}

// healthCheckHandler provides liveness probe endpoint
func healthCheckHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	
	response := map[string]interface{}{
		"status":    "healthy",
		"service":   serviceName,
		"version":   serviceVersion,
		"timestamp": time.Now().UTC().Format(time.RFC3339),
	}
	
	if err := api.WriteJSONResponse(w, response); err != nil {
		log.Printf("Failed to write health check response: %v", err)
	}
}

// readinessCheckHandler provides readiness probe endpoint with dependency checks
func readinessCheckHandler(dbClient *db.Client) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
		defer cancel()
		
		// Check database connectivity
		if err := dbClient.Ping(ctx); err != nil {
			log.Printf("Database health check failed: %v", err)
			w.WriteHeader(http.StatusServiceUnavailable)
			
			response := map[string]interface{}{
				"status": "not_ready",
				"reason": "database_unavailable",
				"error":  err.Error(),
			}
			api.WriteJSONResponse(w, response)
			return
		}

		// All checks passed
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		
		response := map[string]interface{}{
			"status":      "ready",
			"service":     serviceName,
			"version":     serviceVersion,
			"timestamp":   time.Now().UTC().Format(time.RFC3339),
			"checks": map[string]string{
				"database": "ok",
			},
		}
		
		api.WriteJSONResponse(w, response)
	}
}

// Global metrics counters
var (
	startTime = time.Now()
	totalRequests int64
	successfulRequests int64
	failedRequests int64
	totalResponseTime int64 // in milliseconds
	validationErrors int64
	ragChecks int64
	bktCalls int64
	activeConnections int64
	questionsGenerated int64
	mutex sync.RWMutex
)

// metricsHandler provides comprehensive Prometheus-compatible metrics
func metricsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/plain")
	w.WriteHeader(http.StatusOK)
	
	mutex.RLock()
	defer mutex.RUnlock()
	
	uptime := time.Since(startTime).Seconds()
	avgResponseTime := float64(0)
	if totalRequests > 0 {
		avgResponseTime = float64(totalResponseTime) / float64(totalRequests)
	}
	successRate := float64(0)
	if totalRequests > 0 {
		successRate = float64(successfulRequests) / float64(totalRequests) * 100
	}
	
	metrics := fmt.Sprintf(`# HELP question_generator_info Service information
# TYPE question_generator_info gauge
question_generator_info{version="%s",service="%s"} 1

# HELP question_generator_uptime_seconds Service uptime in seconds
# TYPE question_generator_uptime_seconds counter
question_generator_uptime_seconds %.2f

# HELP question_generator_requests_total Total number of HTTP requests
# TYPE question_generator_requests_total counter
question_generator_requests_total{status="success"} %d
question_generator_requests_total{status="failed"} %d

# HELP question_generator_request_duration_ms Average request duration in milliseconds
# TYPE question_generator_request_duration_ms gauge
question_generator_request_duration_ms %.2f

# HELP question_generator_success_rate Percentage of successful requests
# TYPE question_generator_success_rate gauge
question_generator_success_rate %.2f

# HELP question_generator_validation_errors_total Total validation errors
# TYPE question_generator_validation_errors_total counter
question_generator_validation_errors_total %d

# HELP question_generator_rag_checks_total Total RAG quality checks performed
# TYPE question_generator_rag_checks_total counter
question_generator_rag_checks_total %d

# HELP question_generator_bkt_calls_total Total BKT service calls
# TYPE question_generator_bkt_calls_total counter
question_generator_bkt_calls_total %d

# HELP question_generator_active_connections Current active connections
# TYPE question_generator_active_connections gauge
question_generator_active_connections %d

# HELP question_generator_questions_generated_total Total questions generated successfully
# TYPE question_generator_questions_generated_total counter
question_generator_questions_generated_total %d

# HELP question_generator_requests_per_second Current requests per second
# TYPE question_generator_requests_per_second gauge
question_generator_requests_per_second %.2f
`,
		serviceVersion, serviceName, uptime,
		successfulRequests, failedRequests,
		avgResponseTime, successRate,
		validationErrors, ragChecks, bktCalls,
		activeConnections, questionsGenerated,
		float64(totalRequests)/uptime,
	)
	
	w.Write([]byte(metrics))
}

// handleGenerateQuestion processes question generation requests
func handleGenerateQuestion(generatorService *service.GeneratorService, w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	
	// Extract validated request from context
	validatedReq := ctx.Value("validated_request")
	if validatedReq == nil {
		http.Error(w, "Request validation failed", http.StatusBadRequest)
		return
	}
	
	// Convert to service request format
	// This is a simplified handler for Phase 2.2
	// Full implementation would use the complete service.GenerateQuestionRequest
	
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	
	// Mock response for Phase 2.2 testing
	mockResponse := map[string]interface{}{
		"question_id":     "mock_q_12345",
		"question_text":   "What is the acceleration due to gravity on Earth?",
		"options": map[string]string{
			"A": "9.8 m/s²",
			"B": "9.6 m/s²",
			"C": "10.0 m/s²",
			"D": "8.9 m/s²",
		},
		"correct_answer":  "A",
		"difficulty":      0.3,
		"generation_time": 150,
		"quality_score":   0.85,
		"status":          "success",
		"metadata": map[string]interface{}{
			"template_id": "physics_basic_001",
			"bkt_mastery": 0.65,
			"rag_checked": true,
		},
	}
	
	if err := json.NewEncoder(w).Encode(mockResponse); err != nil {
		log.Printf("Failed to encode response: %v", err)
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
	}
}
