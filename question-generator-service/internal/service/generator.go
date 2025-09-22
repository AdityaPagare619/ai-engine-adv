package service

import (
	"context"
	"fmt"
	"log"
	"time"

	"question-generator-service/internal/config"
	"question-generator-service/internal/db"
	"question-generator-service/pkg/templates"
	"question-generator-service/pkg/calibrator"
	"question-generator-service/pkg/validator"
	"question-generator-service/pkg/rag_advisor"
	"question-generator-service/pkg/logger"
)

// GeneratorService orchestrates the complete question generation pipeline
type GeneratorService struct {
	dbClient     *db.Client
	templateSvc  *templates.Service
	calibrator   *calibrator.Service
	validator    *validator.Service
	ragAdvisor   *rag_advisor.Service
	logger       *logger.Service
	cfg          *config.AppConfig
}

// NewGeneratorService creates a new generator service with all dependencies
func NewGeneratorService(cfg *config.AppConfig, dbClient *db.Client) (*GeneratorService, error) {
	// Initialize template service
	templateSvc, err := templates.NewService(dbClient)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize template service: %w", err)
	}

	// Initialize BKT calibrator
	calibratorSvc, err := calibrator.NewService(cfg.BKT)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize calibrator: %w", err)
	}

	// Initialize validator service
	validatorSvc, err := validator.NewService()
	if err != nil {
		return nil, fmt.Errorf("failed to initialize validator: %w", err)
	}

	// Initialize RAG advisor (optional)
	var ragAdvisorSvc *rag_advisor.Service
	if cfg.RAG.Enabled {
		ragAdvisorSvc, err = rag_advisor.NewService(cfg.RAG)
		if err != nil {
			return nil, fmt.Errorf("failed to initialize RAG advisor: %w", err)
		}
	}

	// Initialize logger service
	loggerSvc, err := logger.NewService(dbClient)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize logger: %w", err)
	}

	return &GeneratorService{
		dbClient:    dbClient,
		templateSvc: templateSvc,
		calibrator:  calibratorSvc,
		validator:   validatorSvc,
		ragAdvisor:  ragAdvisorSvc,
		logger:      loggerSvc,
		cfg:         cfg,
	}, nil
}

// GenerateQuestionRequest represents a question generation request
type GenerateQuestionRequest struct {
	StudentID          string  `json:"student_id" validate:"required"`
	TopicID           string  `json:"topic_id" validate:"required"`
	ExamType          string  `json:"exam_type" validate:"required,oneof=JEE_MAIN JEE_ADVANCED NEET FOUNDATION"`
	Subject           string  `json:"subject" validate:"required,oneof=PHYSICS CHEMISTRY MATHEMATICS BIOLOGY"`
	Format            string  `json:"format" validate:"required,oneof=MCQ NUMERICAL ASSERTION_REASON PASSAGE MATRIX_MATCH"`
	RequestedDifficulty float64 `json:"requested_difficulty" validate:"required,min=0.1,max=1.0"`
	SessionID         string  `json:"session_id"`
	RequestID         string  `json:"request_id"`
}

// GenerateQuestionResponse represents the generated question response
type GenerateQuestionResponse struct {
	QuestionID       string                 `json:"question_id"`
	QuestionText     string                 `json:"question_text"`
	Options          map[string]string      `json:"options,omitempty"`
	CorrectAnswer    string                 `json:"correct_answer"`
	SolutionSteps    []string              `json:"solution_steps,omitempty"`
	Difficulty       float64               `json:"difficulty"`
	GenerationTime   int64                 `json:"generation_time_ms"`
	QualityScore     float64               `json:"quality_score"`
	Metadata         map[string]interface{} `json:"metadata"`
}

// GenerateQuestion executes the complete question generation pipeline
func (gs *GeneratorService) GenerateQuestion(ctx context.Context, req *GenerateQuestionRequest) (*GenerateQuestionResponse, error) {
	startTime := time.Now()
	
	// Initialize generation log for tracking
	genLog := &db.GenerationLog{
		StudentID:           req.StudentID,
		SessionID:           req.SessionID,
		RequestID:           req.RequestID,
		TopicID:             req.TopicID,
		ExamType:            req.ExamType,
		Subject:             req.Subject,
		Format:              req.Format,
		RequestedDifficulty: req.RequestedDifficulty,
		Status:              "PENDING",
		GeneratorVersion:    "v1.0.0",
		ModelVersion:        "template-v1",
	}

	// Create generation log entry
	if err := gs.logger.CreateGenerationLog(ctx, genLog); err != nil {
		log.Printf("Failed to create generation log: %v", err)
		// Continue execution even if logging fails
	}

	// Step 1: Load and select appropriate template
	templateStart := time.Now()
	template, err := gs.templateSvc.SelectTemplate(ctx, templates.TemplateSelection{
		TopicID:       req.TopicID,
		ExamType:      req.ExamType,
		Subject:       req.Subject,
		Format:        req.Format,
		MinDifficulty: req.RequestedDifficulty - 0.1,
		MaxDifficulty: req.RequestedDifficulty + 0.1,
	})
	if err != nil {
		return gs.handleGenerationError(ctx, genLog, "TEMPLATE_SELECTION_FAILED", err)
	}
	templateTime := time.Since(templateStart)

	genLog.TemplateID = &template.TemplateID
	genLog.Status = "TEMPLATE_SELECTED"

	// Step 2: Calibrate difficulty using BKT
	calibrationStart := time.Now()
	calibratedDifficulty, masteryLevel, err := gs.calibrator.CalibrateDifficulty(ctx, calibrator.CalibrationRequest{
		StudentID:           req.StudentID,
		TopicID:             req.TopicID,
		RequestedDifficulty: req.RequestedDifficulty,
		BaseDifficulty:      template.BaseDifficulty,
	})
	if err != nil {
		return gs.handleGenerationError(ctx, genLog, "CALIBRATION_FAILED", err)
	}
	calibrationTime := time.Since(calibrationStart)

	genLog.CalibratedDifficulty = &calibratedDifficulty
	genLog.BKTMasteryLevel = &masteryLevel
	genLog.CalibrationTimeMs = int(calibrationTime.Milliseconds())
	genLog.Status = "CALIBRATED"

	// Step 3: Generate question from template
	generationStart := time.Now()
	generatedQuestion, err := gs.templateSvc.FillTemplate(ctx, templates.TemplateFillRequest{
		Template:           template,
		CalibratedDifficulty: calibratedDifficulty,
		StudentContext:     req.StudentID,
	})
	if err != nil {
		return gs.handleGenerationError(ctx, genLog, "GENERATION_FAILED", err)
	}
	generationTime := time.Since(generationStart)

	genLog.GeneratedQuestionText = generatedQuestion.QuestionText
	genLog.GeneratedOptions = generatedQuestion.Options
	genLog.CorrectAnswer = generatedQuestion.CorrectAnswer
	genLog.SolutionSteps = generatedQuestion.SolutionSteps
	genLog.TemplateVariables = generatedQuestion.VariableValues
	genLog.GenerationTimeMs = int(generationTime.Milliseconds())
	genLog.Status = "GENERATED"

	// Step 4: Validate generated question
	validationStart := time.Now()
	validationResult, err := gs.validator.ValidateQuestion(ctx, validator.ValidationRequest{
		QuestionText:  generatedQuestion.QuestionText,
		Options:       generatedQuestion.Options,
		CorrectAnswer: generatedQuestion.CorrectAnswer,
		Subject:       req.Subject,
		ExamType:      req.ExamType,
	})
	if err != nil {
		return gs.handleGenerationError(ctx, genLog, "VALIDATION_FAILED", err)
	}
	validationTime := time.Since(validationStart)

	genLog.GrammarScore = &validationResult.GrammarScore
	genLog.ClarityScore = &validationResult.ClarityScore
	genLog.AmbiguityScore = &validationResult.AmbiguityScore
	genLog.ValidatorFeedback = validationResult.Feedback
	genLog.ValidationPassed = validationResult.Passed
	genLog.ValidationTimeMs = int(validationTime.Milliseconds())
	genLog.Status = "VALIDATED"

	// Step 5: RAG advisor quality check (if enabled)
	var ragTime time.Duration
	var finalQualityScore float64 = validationResult.OverallScore

	if gs.ragAdvisor != nil {
		ragStart := time.Now()
		ragResult, err := gs.ragAdvisor.CheckQuestionQuality(ctx, rag_advisor.QualityCheckRequest{
			QuestionText:    generatedQuestion.QuestionText,
			Options:         generatedQuestion.Options,
			Subject:         req.Subject,
			ExamType:        req.ExamType,
			TopicID:         req.TopicID,
			BaseDifficulty:  template.BaseDifficulty,
		})
		if err != nil {
			log.Printf("RAG advisor check failed (non-critical): %v", err)
			// RAG failure is non-critical, continue with generation
		} else {
			ragTime = time.Since(ragStart)
			
			genLog.RAGAlignmentScore = &ragResult.AlignmentScore
			genLog.RAGExemplarIDs = ragResult.ExemplarIDs
			genLog.RAGFeedback = ragResult.Feedback
			genLog.RAGTimeMs = int(ragTime.Milliseconds())

			// Check if regeneration is needed
			if ragResult.AlignmentScore < gs.cfg.RAG.AlignmentThreshold {
				genLog.RegenerationTriggered = true
				genLog.RegenerationReason = fmt.Sprintf("RAG alignment score %.3f below threshold %.3f", 
					ragResult.AlignmentScore, gs.cfg.RAG.AlignmentThreshold)
				
				// Trigger regeneration (simplified for Phase 2.1)
				log.Printf("Question regeneration triggered for request %s: %s", 
					req.RequestID, genLog.RegenerationReason)
			}

			// Combine RAG and validation scores for final quality
			finalQualityScore = (validationResult.OverallScore + ragResult.AlignmentScore) / 2.0
		}
		
		genLog.Status = "RAG_CHECKED"
	}

	// Calculate total pipeline time
	totalTime := time.Since(startTime)
	genLog.FinalQualityScore = &finalQualityScore
	genLog.TotalPipelineTimeMs = int(totalTime.Milliseconds())
	genLog.Status = "COMPLETED"

	// Update generation log with final results
	if err := gs.logger.UpdateGenerationLog(ctx, genLog); err != nil {
		log.Printf("Failed to update generation log: %v", err)
		// Continue execution even if logging fails
	}

	// Increment template usage counter
	if err := gs.dbClient.IncrementTemplateUsage(ctx, template.TemplateID); err != nil {
		log.Printf("Failed to increment template usage: %v", err)
		// Non-critical error, continue
	}

	// Build response
	response := &GenerateQuestionResponse{
		QuestionID:     fmt.Sprintf("q_%s_%d", req.RequestID, time.Now().UnixNano()),
		QuestionText:   generatedQuestion.QuestionText,
		Options:        generatedQuestion.Options,
		CorrectAnswer:  generatedQuestion.CorrectAnswer,
		SolutionSteps:  generatedQuestion.SolutionSteps,
		Difficulty:     calibratedDifficulty,
		GenerationTime: totalTime.Milliseconds(),
		QualityScore:   finalQualityScore,
		Metadata: map[string]interface{}{
			"template_id":         template.TemplateID,
			"mastery_level":       masteryLevel,
			"validation_passed":   validationResult.Passed,
			"generation_log_id":   genLog.ID,
			"pipeline_breakdown": map[string]int64{
				"template_ms":    templateTime.Milliseconds(),
				"calibration_ms": calibrationTime.Milliseconds(),
				"generation_ms":  generationTime.Milliseconds(),
				"validation_ms":  validationTime.Milliseconds(),
				"rag_ms":         ragTime.Milliseconds(),
			},
		},
	}

	if gs.ragAdvisor != nil && genLog.RAGAlignmentScore != nil {
		response.Metadata["rag_alignment_score"] = *genLog.RAGAlignmentScore
	}

	return response, nil
}

// handleGenerationError handles pipeline errors and updates logs
func (gs *GeneratorService) handleGenerationError(ctx context.Context, genLog *db.GenerationLog, status string, err error) (*GenerateQuestionResponse, error) {
	genLog.Status = "FAILED"
	genLog.ErrorMessage = err.Error()
	
	// Update log with error details
	if updateErr := gs.logger.UpdateGenerationLog(ctx, genLog); updateErr != nil {
		log.Printf("Failed to update generation log with error: %v", updateErr)
	}
	
	return nil, fmt.Errorf("question generation failed at %s: %w", status, err)
}

// GetGenerationMetrics returns performance metrics for monitoring
func (gs *GeneratorService) GetGenerationMetrics(ctx context.Context, timeRange time.Duration) (map[string]interface{}, error) {
	// Implementation would query generation_performance_summary materialized view
	// This is a simplified version for Phase 2.1
	metrics := map[string]interface{}{
		"service_version": "v1.0.0",
		"rag_enabled":     gs.cfg.RAG.Enabled,
		"uptime_seconds":  time.Since(time.Now()).Seconds(),
	}

	return metrics, nil
}