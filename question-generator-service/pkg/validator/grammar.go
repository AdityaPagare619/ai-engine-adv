package validator

import (
	"context"
	"fmt"
	"strings"
	"unicode"
)

// GrammarResult holds clarity and grammar scores plus feedback
type GrammarResult struct {
	GrammarScore float64
	ClarityScore float64
	Feedback     string
	Passed       bool
}

// Service for grammar validation
type Service struct {
	// Could add API client here for third-party checkers
}

// NewService returns new validator service
func NewService() (*Service, error) {
	return &Service{}, nil
}

// ValidateQuestion performs grammar and clarity checks using heuristics or API
func (s *Service) ValidateQuestion(ctx context.Context, questionText string) (*GrammarResult, error) {
	// Simple heuristic checks for demo
	length := len(questionText)
	if length < 10 {
		return &GrammarResult{GrammarScore: 0.2, ClarityScore: 0.3, Feedback: "Question too short", Passed: false}, nil
	}

	// Check for proper ending punctuation
	lastChar := rune(questionText[length-1])
	if lastChar != '.' && lastChar != '?' && lastChar != '!' {
		return &GrammarResult{GrammarScore: 0.5, ClarityScore: 0.5, Feedback: "Question missing punctuation", Passed: false}, nil
	}

	// Check capital letter start
	firstChar := rune(questionText[0])
	if !unicode.IsUpper(firstChar) {
		return &GrammarResult{GrammarScore: 0.6, ClarityScore: 0.6, Feedback: "Question should start with capital letter", Passed: false}, nil
	}

	score := 0.8 // Placeholder for better scoring logic
	feedback := "Grammar looks good."
	return &GrammarResult{
		GrammarScore: score,
		ClarityScore: score,
		Feedback:     feedback,
		Passed:       true,
	}, nil
}
