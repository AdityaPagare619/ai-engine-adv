package api

import (
	"context"
	"net"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/google/uuid"
	"log"
	"sync/atomic"
	"errors"
)

var (
	ErrTooManyRequests = errors.New("too many requests")
)

// MiddlewareConfig holds configurable params
type MiddlewareConfig struct {
	RateLimitPerMinute int64
	AuthEnabled        bool
	AuthHeader         string
	TokenPrefix        string
}

// RateLimiter tracks counts per key (e.g., IP or token)
// Uses atomic counters for concurrency safety
type RateLimiter struct {
	sync.RWMutex
	visitors map[string]*visitor
	limit    int64
}

type visitor struct {
	lastSeen time.Time
	count    int64
}

func NewRateLimiter(limit int64) *RateLimiter {
	rl := &RateLimiter{
		visitors: make(map[string]*visitor),
		limit:    limit,
	}
	go rl.cleanupVisitors()
	return rl
}

func (rl *RateLimiter) cleanupVisitors() {
	for {
		time.Sleep(time.Minute)
		rl.Lock()
		for key, v := range rl.visitors {
			if time.Since(v.lastSeen) > time.Minute {
				delete(rl.visitors, key)
			}
		}
		rl.Unlock()
	}
}

func (rl *RateLimiter) Allow(key string) bool {
	rl.Lock()
	defer rl.Unlock()
	v, exists := rl.visitors[key]
	if !exists {
		rl.visitors[key] = &visitor{lastSeen: time.Now(), count: 1}
		return true
	}
	if time.Since(v.lastSeen) > time.Minute {
		v.count = 0
	}
	v.lastSeen = time.Now()
	if atomic.LoadInt64(&v.count) >= rl.limit {
		return false
	}
	atomic.AddInt64(&v.count, 1)
	return true
}

// Extract IP from request taking X-Forwarded-For header into account
func extractClientIP(r *http.Request) string {
	xff := r.Header.Get("X-Forwarded-For")
	if xff != "" {
		ips := strings.Split(xff, ",")
		return strings.TrimSpace(ips[0])
	}
	ip, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		// fallback to raw addr
		return r.RemoteAddr
	}
	return ip
}

// Extract Auth Token from Authorization header
func extractAuthToken(r *http.Request, prefix string) string {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return ""
	}
	if !strings.HasPrefix(authHeader, prefix+" ") {
		return ""
	}
	return strings.TrimSpace(strings.TrimPrefix(authHeader, prefix))
}

// Middleware is the API middleware container
type Middleware struct {
	cfg                MiddlewareConfig
	ipRateLimiter      *RateLimiter
	authTokenRateLimiter *RateLimiter
}

// NewMiddleware creates middleware instance
func NewMiddleware(cfg MiddlewareConfig) *Middleware {
	m := &Middleware{
		cfg:                cfg,
		ipRateLimiter:      NewRateLimiter(cfg.RateLimitPerMinute),
		authTokenRateLimiter: NewRateLimiter(cfg.RateLimitPerMinute),
	}
	return m
}

// RateLimitByIP limits request rate per IP address
func (m *Middleware) RateLimitByIP(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ip := extractClientIP(r)
		if !m.ipRateLimiter.Allow(ip) {
			http.Error(w, ErrTooManyRequests.Error(), http.StatusTooManyRequests)
			return
		}
		next.ServeHTTP(w, r)
	})
}

// AuthMiddleware stub for Bearer token validation
func (m *Middleware) AuthMiddleware(next http.Handler) http.Handler {
	if !m.cfg.AuthEnabled {
		// No auth applied
		return next
	}
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		token := extractAuthToken(r, m.cfg.TokenPrefix)
		if token == "" {
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}
		// Here put your token validation logic (JWT or OAuth)
		// For stub: accept any token with length > 5 for demo
		if len(token) < 6 {
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		}

		// Rate limit by token also to prevent abuse
		if !m.authTokenRateLimiter.Allow(token) {
			http.Error(w, ErrTooManyRequests.Error(), http.StatusTooManyRequests)
			return
		}

		// Add token/user info to context for use downstream
		ctx := context.WithValue(r.Context(), "auth_token", token)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// RequestLogger middleware logs request details with correlation ID
func (m *Middleware) RequestLogger(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requestID := r.Header.Get("X-Request-ID")
		if requestID == "" {
			requestID = uuid.NewString()
		}
		start := time.Now()
		log.Printf("Start Request: Method=%s Path=%s RemoteIP=%s RequestID=%s", r.Method, r.URL.Path, extractClientIP(r), requestID)

		// Add RequestID to context and response header
		ctx := context.WithValue(r.Context(), "request_id", requestID)
		w.Header().Set("X-Request-ID", requestID)

		next.ServeHTTP(w, r.WithContext(ctx))

		log.Printf("End Request: Method=%s Path=%s RequestID=%s Duration=%s", r.Method, r.URL.Path, requestID, time.Since(start))
	})
}

// RecoverMiddleware handles panic and internal errors gracefully
func (m *Middleware) RecoverMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if rec := recover(); rec != nil {
				log.Printf("Recovered from panic: %v", rec)
				http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			}
		}()
		next.ServeHTTP(w, r)
	})
}
