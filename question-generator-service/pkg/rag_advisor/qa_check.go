package rag_advisor

import (
	"context"
	"fmt"
)

// Service encapsulates QA logic using Client
type Service struct {
	client *Client
}

// NewService creates new QA service instance
func NewService(client *Client) *Service {
	return &Service{client: client}
}

// QualityCheck performs alignment check for a question
func (s *Service) QualityCheck(ctx context.Context, req *QualityCheckRequest) (*QualityCheckResponse, error) {
	resp, err := s.client.CheckQuestionQuality(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("rag quality check failed: %w", err)
	}
	if resp.AlignmentScore < 0.7 {
		return resp, fmt.Errorf("alignment score %.2f below threshold", resp.AlignmentScore)
	}
	return resp, nil
}
