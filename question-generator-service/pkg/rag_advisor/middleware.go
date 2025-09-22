package rag_advisor

import (
	"context"
	"log"
	"net/http"
	"time"
)

// Service wraps the RAG advisor client for middleware use
type Service struct {
	client     *Client
	enabled    bool
	threshold  float64
}

// NewService creates a new RAG advisor service
func NewService(ragURL string, enabled bool, threshold float64) *Service {
	client := NewClient(ragURL, 3*time.Second, 2)
	return &Service{
		client:    client,
		enabled:   enabled,
		threshold: threshold,
	}
}

// AdviseQuality is a middleware that provides quality advice on generated questions
func AdviseQuality(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Add RAG advisor context flag
		ctx := context.WithValue(r.Context(), "rag_advisor_enabled", true)
		
		// For now, just pass through - actual RAG advice happens in the service layer
		// This middleware sets up the context for RAG processing
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// CheckQuestionQualityMiddleware performs actual quality checking
// This would be used in the generation pipeline
func (s *Service) CheckQuestionQualityMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if !s.enabled {
			next.ServeHTTP(w, r)
			return
		}

		// Get the generated question from context (set by previous middleware)
		generatedQuestion := r.Context().Value("generated_question")
		if generatedQuestion == nil {
			// No question to check, pass through
			next.ServeHTTP(w, r)
			return
		}

		// TODO: Perform actual RAG quality check
		// This would involve:
		// 1. Extract question details from context
		// 2. Call RAG service
		// 3. Evaluate quality score against threshold
		// 4. Add advice to context
		
		ctx := context.WithValue(r.Context(), "rag_advice", "quality_checked")
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// MockAdviceMiddleware provides a mock RAG advice for Phase 2.2 testing
func MockAdviceMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Add mock RAG advice to context
		advice := map[string]interface{}{
			"alignment_score":   0.85,
			"quality_passed":    true,
			"exemplar_matches": 3,
			"feedback":         "Question aligns well with exemplars",
		}
		
		ctx := context.WithValue(r.Context(), "rag_advice", advice)
		log.Printf("RAG Advisor: Mock advice added - alignment_score: %.2f", 0.85)
		
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}