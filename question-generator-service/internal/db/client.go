package db

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"path/filepath"
	"time"

	"github.com/golang-migrate/migrate/v4"
	"github.com/golang-migrate/migrate/v4/database/postgres"
	_ "github.com/golang-migrate/migrate/v4/source/file"
	_ "github.com/lib/pq"

	"question-generator-service/internal/config"
)

// Client wraps database connection with helper methods
type Client struct {
	db  *sql.DB
	cfg config.DatabaseConfig
}

// NewClient creates a new database client with connection pooling
func NewClient(cfg config.DatabaseConfig) (*Client, error) {
	db, err := sql.Open("postgres", cfg.GetDatabaseDSN())
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	// Configure connection pool for high-performance workloads
	db.SetMaxOpenConns(cfg.MaxOpenConns)
	db.SetMaxIdleConns(cfg.MaxIdleConns)
	db.SetConnMaxLifetime(cfg.ConnMaxLifetime)

	// Test the connection
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := db.PingContext(ctx); err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	log.Printf("Successfully connected to database %s:%d/%s", 
		cfg.Host, cfg.Port, cfg.Database)

	return &Client{
		db:  db,
		cfg: cfg,
	}, nil
}

// Close closes the database connection
func (c *Client) Close() error {
	return c.db.Close()
}

// Ping checks if the database connection is alive
func (c *Client) Ping(ctx context.Context) error {
	return c.db.PingContext(ctx)
}

// DB returns the underlying sql.DB instance
func (c *Client) DB() *sql.DB {
	return c.db
}

// RunMigrations applies database migrations from the migrations directory
func (c *Client) RunMigrations() error {
	driver, err := postgres.WithInstance(c.db, &postgres.Config{})
	if err != nil {
		return fmt.Errorf("failed to create migration driver: %w", err)
	}

	// Construct migration source URL
	migrationsURL := fmt.Sprintf("file://%s", filepath.Join(c.cfg.MigrationsPath))
	
	m, err := migrate.NewWithDatabaseInstance(
		migrationsURL,
		"postgres",
		driver,
	)
	if err != nil {
		return fmt.Errorf("failed to create migrator: %w", err)
	}

	// Apply migrations
	if err := m.Up(); err != nil && err != migrate.ErrNoChange {
		return fmt.Errorf("failed to apply migrations: %w", err)
	}

	version, dirty, err := m.Version()
	if err != nil {
		log.Printf("Database migrations applied successfully")
	} else {
		log.Printf("Database at migration version %d (dirty: %v)", version, dirty)
	}

	return nil
}

// GetQuestionTemplate retrieves a question template by ID with optimized query
func (c *Client) GetQuestionTemplate(ctx context.Context, templateID string) (*QuestionTemplate, error) {
	query := `
		SELECT template_id, topic_id, exam_type, subject, format, template_text, 
			   variable_slots, options_template, base_difficulty, bloom_level, 
			   concept_depth, validation_score, ambiguity_flag, clarity_score,
			   chapter, sub_chapter, ncert_reference, usage_count, success_rate,
			   avg_solve_time, created_at, updated_at, is_active, version
		FROM question_templates 
		WHERE template_id = $1 AND is_active = true`

	var qt QuestionTemplate
	var optionsTemplate, validationScore, successRate sql.NullString
	var avgSolveTime sql.NullInt64

	err := c.db.QueryRowContext(ctx, query, templateID).Scan(
		&qt.TemplateID, &qt.TopicID, &qt.ExamType, &qt.Subject, &qt.Format,
		&qt.TemplateText, &qt.VariableSlots, &optionsTemplate, &qt.BaseDifficulty,
		&qt.BloomLevel, &qt.ConceptDepth, &validationScore, &qt.AmbiguityFlag,
		&qt.ClarityScore, &qt.Chapter, &qt.SubChapter, &qt.NCERTReference,
		&qt.UsageCount, &successRate, &avgSolveTime, &qt.CreatedAt,
		&qt.UpdatedAt, &qt.IsActive, &qt.Version,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("template %s not found", templateID)
		}
		return nil, fmt.Errorf("failed to get template: %w", err)
	}

	// Handle nullable fields
	if optionsTemplate.Valid {
		qt.OptionsTemplate = &optionsTemplate.String
	}
	if validationScore.Valid {
		if score, err := parseFloat64(validationScore.String); err == nil {
			qt.ValidationScore = &score
		}
	}
	if successRate.Valid {
		if rate, err := parseFloat64(successRate.String); err == nil {
			qt.SuccessRate = &rate
		}
	}
	if avgSolveTime.Valid {
		qt.AvgSolveTime = &avgSolveTime.Int64
	}

	return &qt, nil
}

// GetTemplatesByFilters retrieves templates matching the specified criteria
func (c *Client) GetTemplatesByFilters(ctx context.Context, filters TemplateFilters) ([]*QuestionTemplate, error) {
	query := `
		SELECT template_id, topic_id, exam_type, subject, format, template_text,
			   variable_slots, base_difficulty, bloom_level, concept_depth,
			   chapter, validation_score, usage_count, success_rate
		FROM question_templates
		WHERE is_active = true`
	
	args := []interface{}{}
	argIndex := 1

	// Build dynamic WHERE clause based on filters
	if filters.TopicID != "" {
		query += fmt.Sprintf(" AND topic_id = $%d", argIndex)
		args = append(args, filters.TopicID)
		argIndex++
	}

	if filters.ExamType != "" {
		query += fmt.Sprintf(" AND exam_type = $%d", argIndex)
		args = append(args, filters.ExamType)
		argIndex++
	}

	if filters.Subject != "" {
		query += fmt.Sprintf(" AND subject = $%d", argIndex)
		args = append(args, filters.Subject)
		argIndex++
	}

	if filters.Format != "" {
		query += fmt.Sprintf(" AND format = $%d", argIndex)
		args = append(args, filters.Format)
		argIndex++
	}

	if filters.MinDifficulty > 0 {
		query += fmt.Sprintf(" AND base_difficulty >= $%d", argIndex)
		args = append(args, filters.MinDifficulty)
		argIndex++
	}

	if filters.MaxDifficulty > 0 {
		query += fmt.Sprintf(" AND base_difficulty <= $%d", argIndex)
		args = append(args, filters.MaxDifficulty)
		argIndex++
	}

	// Add ordering and limits for performance
	query += ` ORDER BY usage_count DESC, success_rate DESC NULLS LAST, validation_score DESC NULLS LAST`
	
	if filters.Limit > 0 {
		query += fmt.Sprintf(" LIMIT $%d", argIndex)
		args = append(args, filters.Limit)
	}

	rows, err := c.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to query templates: %w", err)
	}
	defer rows.Close()

	var templates []*QuestionTemplate
	for rows.Next() {
		var qt QuestionTemplate
		var validationScore sql.NullFloat64
		var successRate sql.NullFloat64

		err := rows.Scan(
			&qt.TemplateID, &qt.TopicID, &qt.ExamType, &qt.Subject, &qt.Format,
			&qt.TemplateText, &qt.VariableSlots, &qt.BaseDifficulty, &qt.BloomLevel,
			&qt.ConceptDepth, &qt.Chapter, &validationScore, &qt.UsageCount, &successRate,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan template row: %w", err)
		}

		if validationScore.Valid {
			qt.ValidationScore = &validationScore.Float64
		}
		if successRate.Valid {
			qt.SuccessRate = &successRate.Float64
		}

		templates = append(templates, &qt)
	}

	if err = rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating template rows: %w", err)
	}

	return templates, nil
}

// CreateGenerationLog inserts a new generation log entry
func (c *Client) CreateGenerationLog(ctx context.Context, log *GenerationLog) error {
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
			generator_version, model_version
		) VALUES (
			$1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16,
			$17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30,
			$31, $32, $33, $34, $35, $36, $37
		) RETURNING id`

	err := c.db.QueryRowContext(ctx, query,
		log.StudentID, log.SessionID, log.RequestID, log.TopicID, log.ExamType,
		log.Subject, log.Format, log.RequestedDifficulty, log.CalibratedDifficulty,
		log.BKTMasteryLevel, log.TemplateID, log.TemplateVariables,
		log.GeneratedQuestionText, log.GeneratedOptions, log.CorrectAnswer,
		log.SolutionSteps, log.GrammarScore, log.ClarityScore, log.AmbiguityScore,
		log.ValidatorFeedback, log.RAGAlignmentScore, log.RAGExemplarIDs,
		log.RAGFeedback, log.RegenerationTriggered, log.RegenerationReason,
		log.GenerationTimeMs, log.CalibrationTimeMs, log.ValidationTimeMs,
		log.RAGTimeMs, log.TotalPipelineTimeMs, log.ValidationPassed,
		log.FinalQualityScore, log.Status, log.ErrorMessage, log.RetryCount,
		log.GeneratorVersion, log.ModelVersion,
	).Scan(&log.ID)

	if err != nil {
		return fmt.Errorf("failed to create generation log: %w", err)
	}

	return nil
}

// UpdateGenerationLog updates an existing generation log
func (c *Client) UpdateGenerationLog(ctx context.Context, logID int64, updates GenerationLogUpdate) error {
	// Build dynamic UPDATE query based on provided fields
	setParts := []string{}
	args := []interface{}{}
	argIndex := 1

	if updates.Status != nil {
		setParts = append(setParts, fmt.Sprintf("status = $%d", argIndex))
		args = append(args, *updates.Status)
		argIndex++
	}

	if updates.FinalQualityScore != nil {
		setParts = append(setParts, fmt.Sprintf("final_quality_score = $%d", argIndex))
		args = append(args, *updates.FinalQualityScore)
		argIndex++
	}

	if updates.RAGAlignmentScore != nil {
		setParts = append(setParts, fmt.Sprintf("rag_alignment_score = $%d", argIndex))
		args = append(args, *updates.RAGAlignmentScore)
		argIndex++
	}

	if updates.ValidationPassed != nil {
		setParts = append(setParts, fmt.Sprintf("validation_passed = $%d", argIndex))
		args = append(args, *updates.ValidationPassed)
		argIndex++
	}

	if updates.ErrorMessage != nil {
		setParts = append(setParts, fmt.Sprintf("error_message = $%d", argIndex))
		args = append(args, *updates.ErrorMessage)
		argIndex++
	}

	if len(setParts) == 0 {
		return fmt.Errorf("no fields provided for update")
	}

	query := fmt.Sprintf("UPDATE question_generation_logs SET %s WHERE id = $%d",
		fmt.Sprintf("%s", setParts[0]), argIndex)
	
	for i := 1; i < len(setParts); i++ {
		query = fmt.Sprintf("UPDATE question_generation_logs SET %s, %s WHERE id = $%d",
			setParts[0], setParts[i], argIndex)
	}
	
	args = append(args, logID)

	result, err := c.db.ExecContext(ctx, query, args...)
	if err != nil {
		return fmt.Errorf("failed to update generation log: %w", err)
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	if rowsAffected == 0 {
		return fmt.Errorf("generation log %d not found", logID)
	}

	return nil
}

// IncrementTemplateUsage atomically increments usage count for a template
func (c *Client) IncrementTemplateUsage(ctx context.Context, templateID string) error {
	query := `
		UPDATE question_templates 
		SET usage_count = usage_count + 1, updated_at = NOW()
		WHERE template_id = $1`

	result, err := c.db.ExecContext(ctx, query, templateID)
	if err != nil {
		return fmt.Errorf("failed to increment template usage: %w", err)
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	if rowsAffected == 0 {
		return fmt.Errorf("template %s not found", templateID)
	}

	return nil
}

// Helper function to parse float64 from string
func parseFloat64(s string) (float64, error) {
	if s == "" {
		return 0, fmt.Errorf("empty string")
	}
	return sql.NullFloat64{}.Scan(s)
}