package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gorilla/mux"
	"github.com/rs/cors"

	"question-generator-service/internal/config"
	"question-generator-service/internal/db"
	"question-generator-service/internal/service"
	"question-generator-service/api"
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

	// Set up HTTP handlers and middleware
	router := mux.NewRouter()
	
	// Add service discovery and health check endpoints
	router.HandleFunc("/health", healthCheckHandler).Methods("GET")
	router.HandleFunc("/ready", readinessCheckHandler(dbClient)).Methods("GET")
	router.HandleFunc("/metrics", metricsHandler).Methods("GET")
	
	// Mount API routes with versioning
	apiRouter := router.PathPrefix("/v1").Subrouter()
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

// metricsHandler provides Prometheus-compatible metrics endpoint
func metricsHandler(w http.ResponseWriter, r *http.Request) {
	// In production, this would integrate with Prometheus metrics
	// For now, provide basic service metrics
	w.Header().Set("Content-Type", "text/plain")
	w.WriteHeader(http.StatusOK)
	
	metrics := fmt.Sprintf(`# HELP question_generator_info Service information
# TYPE question_generator_info gauge
question_generator_info{version="%s",service="%s"} 1
# HELP question_generator_uptime_seconds Service uptime in seconds
# TYPE question_generator_uptime_seconds counter
question_generator_uptime_seconds %d
`, serviceVersion, serviceName, int64(time.Since(time.Now()).Seconds()))
	
	w.Write([]byte(metrics))
}