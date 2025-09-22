package logger

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"time"

	"question-generator-service/internal/db"
)

// GenlogService handles persistence of generation logs
type GenlogService struct {
	dbClient *db.Client
}

// NewService creates a new GenlogService instance
func NewService(dbClient *db.Client) (*GenlogService, error) {
	return &GenlogService{dbClient: dbClient}, nil
}

// CreateGenerationLog inserts a new generation log entry transactionally
func (s *GenlogService) CreateGenerationLog(ctx context.Context, log *db.GenerationLog) error {
	tx, err := s.dbClient.DB().BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("start tx failed: %w", err)
	}

	query := `
	INSERT INTO question_generation_logs (
		student_id, session_id, request_id, topic_id, exam_type, subject, format,
		requested_difficulty, calibrated_difficulty, bkt_mastery_level,
		template_id, template_variables, generated_question_text, generated_options,
		correct_answer, solution_steps, grammar_score, clarity_score, ambiguity_score,
		validator_feedback, rag_alignment_score, rag_exemplar_ids, rag_feedback,
		regeneration_triggered, regeneration_reason, generation_time_ms,
		calibration_time_ms, validation_time_ms, rag_time_ms, total_pipeline_time_ms,
		validation_passed, final_quality_score, status, error_message, retry_count,
		generator_version, model_version,
		created_at
	) VALUES (
		$1,$2,$3,$4,$5,$6,$7,$8,$9,$10,
		$11,$12,$13,$14,$15,$16,$17,$18,$19,
		$20,$21,$22,$23,$24,$25,$26,$27,$28,
		$29,$30,$31,$32,$33,$34,$35,$36,NOW()
	) RETURNING id`

	err = tx.QueryRowContext(ctx, query,
		log.StudentID, log.SessionID, log.RequestID, log.TopicID, log.ExamType, log.Subject, log.Format,
		log.RequestedDifficulty, log.CalibratedDifficulty, log.BKTMasteryLevel,
		log.TemplateID, log.TemplateVariables, log.GeneratedQuestionText, log.GeneratedOptions,
		log.CorrectAnswer, log.SolutionSteps, log.GrammarScore, log.ClarityScore, log.AmbiguityScore,
		log.ValidatorFeedback, log.RAGAlignmentScore, log.RAGExemplarIDs, log.RAGFeedback,
		log.RegenerationTriggered, log.RegenerationReason, log.GenerationTimeMs,
		log.CalibrationTimeMs, log.ValidationTimeMs, log.RAGTimeMs, log.TotalPipelineTimeMs,
		log.ValidationPassed, log.FinalQualityScore, log.Status, log.ErrorMessage, log.RetryCount,
		log.GeneratorVersion, log.ModelVersion,
	).Scan(&log.ID)

	if err != nil {
		tx.Rollback()
		return fmt.Errorf("insert generation log failed: %w", err)
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("commit tx failed: %w", err)
	}
	return nil
}

// UpdateGenerationLog updates columns for an existing generation log
func (s *GenlogService) UpdateGenerationLog(ctx context.Context, log *db.GenerationLog) error {
	query := `
		UPDATE question_generation_logs SET
			status = $1,
			final_quality_score = $2,
			rag_alignment_score = $3,
			validation_passed = $4,
			error_message = $5,
			updated_at = NOW()
		WHERE id = $6`

	_, err := s.dbClient.DB().ExecContext(ctx, query, log.Status, log.FinalQualityScore,
		log.RAGAlignmentScore, log.ValidationPassed, log.ErrorMessage, log.ID)
	if err != nil {
		return fmt.Errorf("update generation log failed: %w", err)
	}
	return nil
}
