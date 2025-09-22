package validator

import (
	"context"
	"strings"
)

// AmbiguityResult holds ambiguity score and feedback
type AmbiguityResult struct {
	AmbiguityScore float64
	Feedback       string
}

// Service for ambiguity detection
type Service struct {
	ambiguousTerms []string
}

// NewService returns a new ambiguity detection service
func NewService() (*Service, error) {
	// Example ambiguous terms, expand as needed
	terms := []string{"some", "many", "few", "better", "worse", "often", "usually", "maybe", "several"}
	return &Service{ambiguousTerms: terms}, nil
}

// DetectAmbiguity checks string for ambiguous phrases and scores
func (s *Service) DetectAmbiguity(ctx context.Context, text string) (*AmbiguityResult, error) {
	lower := strings.ToLower(text)
	count := 0
	for _, term := range s.ambiguousTerms {
		if strings.Contains(lower, term) {
			count++
		}
	}
	score := float64(count) / float64(len(s.ambiguousTerms))
	feedback := ""
	if count > 0 {
		feedback = "Detected ambiguous terms in question: " + strings.Join(s.ambiguousTerms, ", ")
	} else {
		feedback = "No ambiguous terms detected."
	}
	return &AmbiguityResult{AmbiguityScore: score, Feedback: feedback}, nil
}
