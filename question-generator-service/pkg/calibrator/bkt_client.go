package calibrator

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"net/http"
	"time"

	"question-generator-service/internal/config"
)

// Service handles difficulty calibration using BKT inference
type Service struct {
	client     *http.Client
	serviceURL string
	config     config.BKTConfig
}

// NewService creates a new BKT calibrator service
func NewService(cfg config.BKTConfig) (*Service, error) {
	client := &http.Client{
		Timeout: cfg.Timeout,
		Transport: &http.Transport{
			MaxIdleConns:        10,
			IdleConnTimeout:     30 * time.Second,
			DisableCompression:  false,
		},
	}

	return &Service{
		client:     client,
		serviceURL: cfg.ServiceURL,
		config:     cfg,
	}, nil
}

// CalibrationRequest represents a difficulty calibration request
type CalibrationRequest struct {
	StudentID           string  `json:"student_id"`
	TopicID             string  `json:"topic_id"`
	RequestedDifficulty float64 `json:"requested_difficulty"`
	BaseDifficulty      float64 `json:"base_difficulty"`
	ExamType            string  `json:"exam_type,omitempty"`
	Subject             string  `json:"subject,omitempty"`
}

// CalibrationResponse represents the BKT service response
type CalibrationResponse struct {
	CalibratedDifficulty float64 `json:"calibrated_difficulty"`
	MasteryLevel         float64 `json:"mastery_level"`
	Confidence           float64 `json:"confidence"`
	Recommendation       string  `json:"recommendation"`
	BKTParameters        BKTParameters `json:"bkt_parameters"`
}

// BKTParameters contains the core BKT model parameters
type BKTParameters struct {
	InitialKnowledge float64 `json:"initial_knowledge"`    // P(L0)
	TransitionRate   float64 `json:"transition_rate"`      // P(T)
	SlipRate         float64 `json:"slip_rate"`            // P(S)
	GuessRate        float64 `json:"guess_rate"`           // P(G)
	Observations     int     `json:"observations"`         // Number of attempts
	LastUpdated      string  `json:"last_updated"`
}

// CalibrateDifficulty calibrates question difficulty based on student's mastery level
func (s *Service) CalibrateDifficulty(ctx context.Context, req CalibrationRequest) (float64, float64, error) {
	// Build request payload for BKT service
	requestBody, err := json.Marshal(map[string]interface{}{
		"student_id":           req.StudentID,
		"concept_id":           req.TopicID, // BKT service uses concept_id terminology
		"requested_difficulty": req.RequestedDifficulty,
		"base_difficulty":      req.BaseDifficulty,
		"metadata": map[string]string{
			"exam_type": req.ExamType,
			"subject":   req.Subject,
		},
	})
	if err != nil {
		return 0, 0, fmt.Errorf("failed to marshal calibration request: %w", err)
	}

	// Make HTTP request to BKT inference service with retry logic
	var response CalibrationResponse
	err = s.makeRequestWithRetry(ctx, "POST", "/v1/calibrate", requestBody, &response)
	if err != nil {
		// Fallback to rule-based calibration if BKT service fails
		return s.fallbackCalibration(req)
	}

	// Validate response
	if err := s.validateCalibrationResponse(&response); err != nil {
		return s.fallbackCalibration(req)
	}

	return response.CalibratedDifficulty, response.MasteryLevel, nil
}

// GetStudentMastery retrieves current mastery level for a student-topic combination
func (s *Service) GetStudentMastery(ctx context.Context, studentID, topicID string) (float64, error) {
	endpoint := fmt.Sprintf("/v1/mastery/%s/%s", studentID, topicID)
	
	var response struct {
		MasteryLevel  float64       `json:"mastery_level"`
		Confidence    float64       `json:"confidence"`
		BKTParameters BKTParameters `json:"bkt_parameters"`
		LastActivity  string        `json:"last_activity"`
	}

	err := s.makeRequestWithRetry(ctx, "GET", endpoint, nil, &response)
	if err != nil {
		return 0.5, fmt.Errorf("failed to get student mastery: %w", err) // Default to medium mastery
	}

	return response.MasteryLevel, nil
}

// UpdateMasteryLevel updates student mastery based on question performance
func (s *Service) UpdateMasteryLevel(ctx context.Context, req MasteryUpdateRequest) error {
	requestBody, err := json.Marshal(req)
	if err != nil {
		return fmt.Errorf("failed to marshal mastery update: %w", err)
	}

	var response struct {
		Success      bool    `json:"success"`
		NewMastery   float64 `json:"new_mastery_level"`
		UpdatedAt    string  `json:"updated_at"`
	}

	err = s.makeRequestWithRetry(ctx, "POST", "/v1/update", requestBody, &response)
	if err != nil {
		return fmt.Errorf("failed to update mastery level: %w", err)
	}

	if !response.Success {
		return fmt.Errorf("mastery update was not successful")
	}

	return nil
}

// MasteryUpdateRequest represents a mastery level update request
type MasteryUpdateRequest struct {
	StudentID      string  `json:"student_id"`
	TopicID        string  `json:"topic_id"`
	QuestionID     string  `json:"question_id"`
	IsCorrect      bool    `json:"is_correct"`
	ResponseTime   int64   `json:"response_time_ms"`
	Difficulty     float64 `json:"difficulty"`
	HintUsed       bool    `json:"hint_used,omitempty"`
	PartialCredit  float64 `json:"partial_credit,omitempty"` // For numerical questions
}

// makeRequestWithRetry implements exponential backoff retry logic
func (s *Service) makeRequestWithRetry(ctx context.Context, method, endpoint string, body []byte, response interface{}) error {
	url := s.serviceURL + endpoint
	
	for attempt := 0; attempt <= s.config.RetryCount; attempt++ {
		if attempt > 0 {
			// Exponential backoff with jitter
			delay := time.Duration(math.Pow(2, float64(attempt))) * s.config.RetryDelay
			select {
			case <-time.After(delay):
			case <-ctx.Done():
				return ctx.Err()
			}
		}

		err := s.makeRequest(ctx, method, url, body, response)
		if err == nil {
			return nil
		}

		// Don't retry on context cancellation or client errors (4xx)
		if ctx.Err() != nil || isClientError(err) {
			return err
		}
	}

	return fmt.Errorf("request failed after %d retries", s.config.RetryCount)
}

// makeRequest makes a single HTTP request to the BKT service
func (s *Service) makeRequest(ctx context.Context, method, url string, body []byte, response interface{}) error {
	var reqBody io.Reader
	if body != nil {
		reqBody = bytes.NewBuffer(body)
	}

	req, err := http.NewRequestWithContext(ctx, method, url, reqBody)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	req.Header.Set("User-Agent", "question-generator/v1.0.0")

	resp, err := s.client.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("HTTP %d: %s", resp.StatusCode, string(bodyBytes))
	}

	if response != nil {
		if err := json.NewDecoder(resp.Body).Decode(response); err != nil {
			return fmt.Errorf("failed to decode response: %w", err)
		}
	}

	return nil
}

// validateCalibrationResponse validates the BKT service response
func (s *Service) validateCalibrationResponse(resp *CalibrationResponse) error {
	if resp.CalibratedDifficulty < 0.0 || resp.CalibratedDifficulty > 1.0 {
		return fmt.Errorf("invalid calibrated difficulty: %f", resp.CalibratedDifficulty)
	}

	if resp.MasteryLevel < 0.0 || resp.MasteryLevel > 1.0 {
		return fmt.Errorf("invalid mastery level: %f", resp.MasteryLevel)
	}

	// Validate BKT parameters are within expected ranges
	params := resp.BKTParameters
	if params.InitialKnowledge < 0.0 || params.InitialKnowledge > 1.0 {
		return fmt.Errorf("invalid initial knowledge parameter: %f", params.InitialKnowledge)
	}

	if params.TransitionRate < 0.0 || params.TransitionRate > 1.0 {
		return fmt.Errorf("invalid transition rate parameter: %f", params.TransitionRate)
	}

	if params.SlipRate < 0.0 || params.SlipRate > 1.0 {
		return fmt.Errorf("invalid slip rate parameter: %f", params.SlipRate)
	}

	if params.GuessRate < 0.0 || params.GuessRate > 1.0 {
		return fmt.Errorf("invalid guess rate parameter: %f", params.GuessRate)
	}

	return nil
}

// fallbackCalibration provides rule-based difficulty calibration when BKT service fails
func (s *Service) fallbackCalibration(req CalibrationRequest) (float64, float64, error) {
	// Simple rule-based fallback algorithm
	// In production, this would be more sophisticated based on historical data

	baseDifficulty := req.BaseDifficulty
	requestedDifficulty := req.RequestedDifficulty

	// Apply conservative adjustment toward base difficulty
	calibratedDifficulty := (baseDifficulty + requestedDifficulty) / 2.0

	// Ensure within bounds
	if calibratedDifficulty < 0.1 {
		calibratedDifficulty = 0.1
	}
	if calibratedDifficulty > 1.0 {
		calibratedDifficulty = 1.0
	}

	// Assume medium mastery level for fallback
	masteryLevel := 0.5

	return calibratedDifficulty, masteryLevel, nil
}

// isClientError checks if an error represents a client error (4xx HTTP status)
func isClientError(err error) bool {
	if err == nil {
		return false
	}
	
	// Simple check for common client error patterns
	errorStr := err.Error()
	return bytes.Contains([]byte(errorStr), []byte("HTTP 4")) ||
		   bytes.Contains([]byte(errorStr), []byte("400")) ||
		   bytes.Contains([]byte(errorStr), []byte("401")) ||
		   bytes.Contains([]byte(errorStr), []byte("403")) ||
		   bytes.Contains([]byte(errorStr), []byte("404"))
}

// GetDifficultyMapping maps BKT mastery levels to question difficulties
func (s *Service) GetDifficultyMapping(masteryLevel float64, targetDifficulty float64) float64 {
	// Advanced difficulty mapping algorithm based on educational research
	
	// Zone of Proximal Development (ZPD) principle
	// Optimal difficulty should be slightly above current mastery level
	
	var optimalDifficulty float64
	
	if masteryLevel < 0.3 {
		// Beginner: Stay within comfort zone with slight challenge
		optimalDifficulty = masteryLevel + 0.1
	} else if masteryLevel < 0.7 {
		// Intermediate: Moderate challenge to promote growth
		optimalDifficulty = masteryLevel + 0.15
	} else {
		// Advanced: Maintain high standards with appropriate challenge
		optimalDifficulty = masteryLevel + 0.1
	}

	// Blend with target difficulty (weighted toward optimal)
	calibratedDifficulty := 0.7*optimalDifficulty + 0.3*targetDifficulty

	// Ensure bounds
	if calibratedDifficulty < 0.1 {
		calibratedDifficulty = 0.1
	}
	if calibratedDifficulty > 1.0 {
		calibratedDifficulty = 1.0
	}

	return calibratedDifficulty
}