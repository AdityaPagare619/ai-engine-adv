package config

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"
)

// AppConfig holds all configuration for the question generator service
type AppConfig struct {
	Database DatabaseConfig
	Server   ServerConfig
	BKT      BKTConfig
	RAG      RAGConfig
	Logging  LoggingConfig
}

// DatabaseConfig contains database connection settings
type DatabaseConfig struct {
	Host            string
	Port            int
	Database        string
	Username        string
	Password        string
	SSLMode         string
	MaxOpenConns    int
	MaxIdleConns    int
	ConnMaxLifetime time.Duration
	MigrationsPath  string
}

// ServerConfig contains HTTP server settings  
type ServerConfig struct {
	Port           int
	ReadTimeout    time.Duration
	WriteTimeout   time.Duration
	IdleTimeout    time.Duration
	AllowedOrigins []string
}

// BKTConfig contains BKT inference service settings
type BKTConfig struct {
	ServiceURL    string
	Timeout       time.Duration
	RetryCount    int
	RetryDelay    time.Duration
	CircuitBreaker CircuitBreakerConfig
}

// RAGConfig contains RAG advisor service settings
type RAGConfig struct {
	Enabled           bool
	ServiceURL        string
	VectorStoreURL    string
	Timeout           time.Duration
	AlignmentThreshold float64
	MaxRetries        int
	EmbeddingModel    string
}

// CircuitBreakerConfig for resilient service calls
type CircuitBreakerConfig struct {
	MaxRequests    uint32
	Interval       time.Duration
	Timeout        time.Duration
	FailureRatio   float64
}

// LoggingConfig for structured logging
type LoggingConfig struct {
	Level  string
	Format string // json or console
	Output string // stdout, stderr, or file path
}

// LoadConfig loads configuration from environment variables with sensible defaults
func LoadConfig() (*AppConfig, error) {
	cfg := &AppConfig{
		Database: DatabaseConfig{
			Host:            getEnv("DB_HOST", "localhost"),
			Port:            getEnvAsInt("DB_PORT", 5432),
			Database:        getEnv("DB_NAME", "jee_neet_platform"),
			Username:        getEnv("DB_USER", "postgres"),
			Password:        getEnv("DB_PASSWORD", ""),
			SSLMode:         getEnv("DB_SSL_MODE", "prefer"),
			MaxOpenConns:    getEnvAsInt("DB_MAX_OPEN_CONNS", 25),
			MaxIdleConns:    getEnvAsInt("DB_MAX_IDLE_CONNS", 5),
			ConnMaxLifetime: getEnvAsDuration("DB_CONN_MAX_LIFETIME", time.Hour),
			MigrationsPath:  getEnv("DB_MIGRATIONS_PATH", "internal/db/migrations"),
		},
		Server: ServerConfig{
			Port:           getEnvAsInt("SERVER_PORT", 8080),
			ReadTimeout:    getEnvAsDuration("SERVER_READ_TIMEOUT", 10*time.Second),
			WriteTimeout:   getEnvAsDuration("SERVER_WRITE_TIMEOUT", 30*time.Second),
			IdleTimeout:    getEnvAsDuration("SERVER_IDLE_TIMEOUT", 60*time.Second),
			AllowedOrigins: getEnvAsSlice("ALLOWED_ORIGINS", []string{"*"}),
		},
		BKT: BKTConfig{
			ServiceURL: getEnv("BKT_SERVICE_URL", "http://bkt-inference:8081"),
			Timeout:    getEnvAsDuration("BKT_TIMEOUT", 5*time.Second),
			RetryCount: getEnvAsInt("BKT_RETRY_COUNT", 3),
			RetryDelay: getEnvAsDuration("BKT_RETRY_DELAY", 100*time.Millisecond),
			CircuitBreaker: CircuitBreakerConfig{
				MaxRequests:  uint32(getEnvAsInt("BKT_CB_MAX_REQUESTS", 10)),
				Interval:     getEnvAsDuration("BKT_CB_INTERVAL", 60*time.Second),
				Timeout:      getEnvAsDuration("BKT_CB_TIMEOUT", 10*time.Second),
				FailureRatio: getEnvAsFloat("BKT_CB_FAILURE_RATIO", 0.6),
			},
		},
		RAG: RAGConfig{
			Enabled:            getEnvAsBool("RAG_ENABLED", true),
			ServiceURL:         getEnv("RAG_SERVICE_URL", "http://rag-advisor:8082"),
			VectorStoreURL:     getEnv("VECTOR_STORE_URL", "http://weaviate:8080"),
			Timeout:            getEnvAsDuration("RAG_TIMEOUT", 3*time.Second),
			AlignmentThreshold: getEnvAsFloat("RAG_ALIGNMENT_THRESHOLD", 0.8),
			MaxRetries:         getEnvAsInt("RAG_MAX_RETRIES", 2),
			EmbeddingModel:     getEnv("RAG_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
		},
		Logging: LoggingConfig{
			Level:  getEnv("LOG_LEVEL", "info"),
			Format: getEnv("LOG_FORMAT", "json"),
			Output: getEnv("LOG_OUTPUT", "stdout"),
		},
	}

	// Validate required configuration
	if err := cfg.validate(); err != nil {
		return nil, fmt.Errorf("configuration validation failed: %w", err)
	}

	return cfg, nil
}

// validate ensures all required configuration is present and valid
func (c *AppConfig) validate() error {
	if c.Database.Host == "" {
		return fmt.Errorf("database host is required")
	}
	
	if c.Database.Database == "" {
		return fmt.Errorf("database name is required")
	}
	
	if c.Database.Username == "" {
		return fmt.Errorf("database username is required")
	}

	if c.BKT.ServiceURL == "" {
		return fmt.Errorf("BKT service URL is required")
	}

	if c.RAG.Enabled && c.RAG.ServiceURL == "" {
		return fmt.Errorf("RAG service URL is required when RAG is enabled")
	}

	if c.RAG.AlignmentThreshold < 0.0 || c.RAG.AlignmentThreshold > 1.0 {
		return fmt.Errorf("RAG alignment threshold must be between 0.0 and 1.0")
	}

	return nil
}

// GetDatabaseDSN returns the database connection string
func (c *DatabaseConfig) GetDatabaseDSN() string {
	return fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
		c.Host, c.Port, c.Username, c.Password, c.Database, c.SSLMode)
}

// Environment variable helper functions

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvAsInt(key string, defaultValue int) int {
	valueStr := getEnv(key, "")
	if value, err := strconv.Atoi(valueStr); err == nil {
		return value
	}
	return defaultValue
}

func getEnvAsBool(key string, defaultValue bool) bool {
	valueStr := getEnv(key, "")
	if value, err := strconv.ParseBool(valueStr); err == nil {
		return value
	}
	return defaultValue
}

func getEnvAsFloat(key string, defaultValue float64) float64 {
	valueStr := getEnv(key, "")
	if value, err := strconv.ParseFloat(valueStr, 64); err == nil {
		return value
	}
	return defaultValue
}

func getEnvAsDuration(key string, defaultValue time.Duration) time.Duration {
	valueStr := getEnv(key, "")
	if value, err := time.ParseDuration(valueStr); err == nil {
		return value
	}
	return defaultValue
}

func getEnvAsSlice(key string, defaultValue []string) []string {
	valueStr := getEnv(key, "")
	if valueStr == "" {
		return defaultValue
	}
	return strings.Split(valueStr, ",")
}