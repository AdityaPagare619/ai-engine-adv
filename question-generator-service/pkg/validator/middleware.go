package validator

import (
	"context"
	"encoding/json"
	"net/http"
	"strings"
)

// GenerateQuestionRequest represents the request structure for question generation
type GenerateQuestionRequest struct {
	StudentID           string  `json:"student_id" validate:"required"`
	TopicID            string  `json:"topic_id" validate:"required"`
	ExamType           string  `json:"exam_type" validate:"required,oneof=JEE_MAIN JEE_ADVANCED NEET FOUNDATION"`
	Subject            string  `json:"subject" validate:"required,oneof=PHYSICS CHEMISTRY MATHEMATICS BIOLOGY"`
	Format             string  `json:"format" validate:"required,oneof=MCQ NUMERICAL ASSERTION_REASON PASSAGE MATRIX_MATCH"`
	RequestedDifficulty float64 `json:"requested_difficulty" validate:"required,min=0.1,max=1.0"`
	SessionID          string  `json:"session_id"`
	RequestID          string  `json:"request_id"`
}

// ValidationError represents a validation error
type ValidationError struct {
	Field   string `json:"field"`
	Message string `json:"message"`
	Value   interface{} `json:"value,omitempty"`
}

// ValidationResponse represents validation error response
type ValidationResponse struct {
	Status string            `json:"status"`
	Message string           `json:"message"`
	Errors []ValidationError `json:"errors"`
}

// ValidateGenerateQuestionRequest validates the incoming question generation request
func ValidateGenerateQuestionRequest(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Only validate POST requests to question generation endpoint
		if r.Method != http.MethodPost {
			next.ServeHTTP(w, r)
			return
		}

		// Parse request body
		var req GenerateQuestionRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			writeValidationError(w, "invalid_json", "Request body contains invalid JSON", []ValidationError{
				{Field: "body", Message: "Invalid JSON format", Value: err.Error()},
			})
			return
		}

		// Validate required fields and business rules
		errors := validateRequest(&req)
		if len(errors) > 0 {
			writeValidationError(w, "validation_failed", "Request validation failed", errors)
			return
		}

		// Add validated request to context
		ctx := context.WithValue(r.Context(), "validated_request", &req)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

// validateRequest performs business rule validation
func validateRequest(req *GenerateQuestionRequest) []ValidationError {
	var errors []ValidationError

	// Required field validation
	if strings.TrimSpace(req.StudentID) == "" {
		errors = append(errors, ValidationError{
			Field:   "student_id",
			Message: "Student ID is required",
			Value:   req.StudentID,
		})
	}

	if strings.TrimSpace(req.TopicID) == "" {
		errors = append(errors, ValidationError{
			Field:   "topic_id",
			Message: "Topic ID is required",
			Value:   req.TopicID,
		})
	}

	// Exam type validation
	validExamTypes := []string{"JEE_MAIN", "JEE_ADVANCED", "NEET", "FOUNDATION"}
	if !contains(validExamTypes, req.ExamType) {
		errors = append(errors, ValidationError{
			Field:   "exam_type",
			Message: "Invalid exam type. Must be one of: JEE_MAIN, JEE_ADVANCED, NEET, FOUNDATION",
			Value:   req.ExamType,
		})
	}

	// Subject validation
	validSubjects := []string{"PHYSICS", "CHEMISTRY", "MATHEMATICS", "BIOLOGY"}
	if !contains(validSubjects, req.Subject) {
		errors = append(errors, ValidationError{
			Field:   "subject",
			Message: "Invalid subject. Must be one of: PHYSICS, CHEMISTRY, MATHEMATICS, BIOLOGY",
			Value:   req.Subject,
		})
	}

	// Format validation
	validFormats := []string{"MCQ", "NUMERICAL", "ASSERTION_REASON", "PASSAGE", "MATRIX_MATCH"}
	if !contains(validFormats, req.Format) {
		errors = append(errors, ValidationError{
			Field:   "format",
			Message: "Invalid format. Must be one of: MCQ, NUMERICAL, ASSERTION_REASON, PASSAGE, MATRIX_MATCH",
			Value:   req.Format,
		})
	}

	// Difficulty validation
	if req.RequestedDifficulty < 0.1 || req.RequestedDifficulty > 1.0 {
		errors = append(errors, ValidationError{
			Field:   "requested_difficulty",
			Message: "Requested difficulty must be between 0.1 and 1.0",
			Value:   req.RequestedDifficulty,
		})
	}

	// Business rule validation
	if req.ExamType == "NEET" && req.Subject == "MATHEMATICS" {
		errors = append(errors, ValidationError{
			Field:   "subject",
			Message: "NEET exam does not include MATHEMATICS subject",
			Value:   req.Subject,
		})
	}

	if req.ExamType == "JEE_MAIN" && req.Subject == "BIOLOGY" {
		errors = append(errors, ValidationError{
			Field:   "subject",
			Message: "JEE_MAIN exam does not typically include BIOLOGY subject",
			Value:   req.Subject,
		})
	}

	return errors
}

// writeValidationError writes validation error response
func writeValidationError(w http.ResponseWriter, status, message string, errors []ValidationError) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusBadRequest)
	
	response := ValidationResponse{
		Status:  status,
		Message: message,
		Errors:  errors,
	}
	
	json.NewEncoder(w).Encode(response)
}

// contains checks if slice contains item
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}