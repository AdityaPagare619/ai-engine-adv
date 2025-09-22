package rag_advisor

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// Client connects to RAG external service
type Client struct {
	baseURL    string
	httpClient *http.Client
	timeout    time.Duration
	maxRetries int
}

// NewClient creates a RAG client instance
func NewClient(baseURL string, timeout time.Duration, maxRetries int) *Client {
	return &Client{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: timeout,
		},
		maxRetries: maxRetries,
	}
}

// QualityCheckRequest to be sent to RAG server
type QualityCheckRequest struct {
	QuestionText string            `json:"question_text"`
	Options      map[string]string `json:"options,omitempty"`
	Subject      string            `json:"subject"`
	ExamType     string            `json:"exam_type"`
	TopicID      string            `json:"topic_id"`
	BaseDiff     float64           `json:"base_difficulty"`
}

// QualityCheckResponse from RAG server
type QualityCheckResponse struct {
	AlignmentScore float64  `json:"alignment_score"`
	ExemplarIDs    []string `json:"exemplar_ids"`
	Feedback       string   `json:"feedback"`
}

// CheckQuestionQuality sends question for RAG quality validation
func (c *Client) CheckQuestionQuality(ctx context.Context, req *QualityCheckRequest) (*QualityCheckResponse, error) {
	url := fmt.Sprintf("%s/v1/quality_check", c.baseURL)
	requestBody, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("marshal request: %w", err)
	}

	var resp QualityCheckResponse
	for attempt := 0; attempt <= c.maxRetries; attempt++ {
		err = c.doRequest(ctx, url, requestBody, &resp)
		if err == nil {
			return &resp, nil
		}
		if ctx.Err() != nil {
			return nil, ctx.Err()
		}
		time.Sleep(time.Duration(100*(attempt+1)) * time.Millisecond)
	}
	return nil, fmt.Errorf("rag advisor request failed after retries: %w", err)
}

func (c *Client) doRequest(ctx context.Context, url string, body []byte, respObj interface{}) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		b, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("http error %d: %s", resp.StatusCode, string(b))
	}

	return json.NewDecoder(resp.Body).Decode(respObj)
}
