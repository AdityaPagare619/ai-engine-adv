package templates

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"math"
	"math/rand"
	"strconv"
	"strings"
	"time"

	"question-generator-service/internal/db"
)

// Service handles question template operations
type Service struct {
	dbClient *db.Client
	rand     *rand.Rand
}

// NewService creates a new template service
func NewService(dbClient *db.Client) (*Service, error) {
	return &Service{
		dbClient: dbClient,
		rand:     rand.New(rand.NewSource(time.Now().UnixNano())),
	}, nil
}

// TemplateSelection criteria for finding suitable templates
type TemplateSelection struct {
	TopicID       string
	ExamType      string
	Subject       string
	Format        string
	MinDifficulty float64
	MaxDifficulty float64
	BloomLevel    int    // Optional filter by Bloom's taxonomy level
	ConceptDepth  int    // Optional filter by concept depth
	Limit         int    // Maximum templates to consider (default: 10)
}

// TemplateFillRequest contains parameters for filling template variables
type TemplateFillRequest struct {
	Template           *db.QuestionTemplate
	CalibratedDifficulty float64
	StudentContext     string
	RandomSeed         int64 // Optional: for reproducible generation
}

// GeneratedQuestion represents a filled template with complete question data
type GeneratedQuestion struct {
	QuestionText   string            `json:"question_text"`
	Options        map[string]string `json:"options,omitempty"`
	CorrectAnswer  string            `json:"correct_answer"`
	SolutionSteps  []string          `json:"solution_steps,omitempty"`
	VariableValues map[string]interface{} `json:"variable_values"`
	Difficulty     float64           `json:"difficulty"`
	Metadata       map[string]interface{} `json:"metadata"`
}

// VariableSpec defines the structure of template variables
type VariableSpec struct {
	Name    string                 `json:"name"`
	Type    string                 `json:"type"` // integer, float, string, array, object
	Range   *RangeSpec            `json:"range,omitempty"`
	Options []string              `json:"options,omitempty"`
	Formula string                 `json:"formula,omitempty"` // For computed variables
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// RangeSpec defines numeric ranges for variable generation
type RangeSpec struct {
	Min  float64 `json:"min"`
	Max  float64 `json:"max"`
	Step float64 `json:"step,omitempty"` // For discrete steps
}

// SelectTemplate finds the most suitable template based on selection criteria
func (s *Service) SelectTemplate(ctx context.Context, selection TemplateSelection) (*db.QuestionTemplate, error) {
	// Set defaults
	if selection.Limit <= 0 {
		selection.Limit = 10
	}

	// Build filter criteria for database query
	filters := db.TemplateFilters{
		TopicID:       selection.TopicID,
		ExamType:      selection.ExamType,
		Subject:       selection.Subject,
		Format:        selection.Format,
		MinDifficulty: selection.MinDifficulty,
		MaxDifficulty: selection.MaxDifficulty,
		Limit:         selection.Limit,
	}

	// Query database for matching templates
	templates, err := s.dbClient.GetTemplatesByFilters(ctx, filters)
	if err != nil {
		return nil, fmt.Errorf("failed to query templates: %w", err)
	}

	if len(templates) == 0 {
		return nil, fmt.Errorf("no templates found matching criteria: topic=%s, exam=%s, subject=%s, format=%s", 
			selection.TopicID, selection.ExamType, selection.Subject, selection.Format)
	}

	// Apply intelligent template selection algorithm
	selectedTemplate := s.selectBestTemplate(templates, selection)
	
	log.Printf("Selected template %s (usage: %d, score: %.3f) from %d candidates", 
		selectedTemplate.TemplateID, selectedTemplate.UsageCount, 
		s.calculateTemplateScore(selectedTemplate, selection), len(templates))

	return selectedTemplate, nil
}

// FillTemplate generates a complete question by filling template variables
func (s *Service) FillTemplate(ctx context.Context, req TemplateFillRequest) (*GeneratedQuestion, error) {
	// Parse variable specifications from template
	var variableSpecs []VariableSpec
	if err := json.Unmarshal([]byte(req.Template.VariableSlots), &variableSpecs); err != nil {
		return nil, fmt.Errorf("failed to parse variable slots: %w", err)
	}

	// Set random seed for reproducible generation if provided
	if req.RandomSeed != 0 {
		s.rand = rand.New(rand.NewSource(req.RandomSeed))
	}

	// Generate values for all variables
	variableValues := make(map[string]interface{})
	for _, spec := range variableSpecs {
		value, err := s.generateVariableValue(spec, req.CalibratedDifficulty, variableValues)
		if err != nil {
			return nil, fmt.Errorf("failed to generate value for variable %s: %w", spec.Name, err)
		}
		variableValues[spec.Name] = value
	}

	// Fill template text with generated values
	questionText, err := s.fillTemplateText(req.Template.TemplateText, variableValues)
	if err != nil {
		return nil, fmt.Errorf("failed to fill template text: %w", err)
	}

	// Generate options for MCQ questions
	var options map[string]string
	if req.Template.Format == "MCQ" && req.Template.OptionsTemplate != nil {
		options, err = s.generateMCQOptions(ctx, *req.Template.OptionsTemplate, variableValues, req.CalibratedDifficulty)
		if err != nil {
			return nil, fmt.Errorf("failed to generate MCQ options: %w", err)
		}
	}

	// Calculate correct answer based on template logic
	correctAnswer, err := s.calculateCorrectAnswer(req.Template, variableValues)
	if err != nil {
		return nil, fmt.Errorf("failed to calculate correct answer: %w", err)
	}

	// Generate solution steps
	solutionSteps, err := s.generateSolutionSteps(req.Template, variableValues)
	if err != nil {
		log.Printf("Warning: failed to generate solution steps: %v", err)
		// Solution steps are optional, continue without them
	}

	return &GeneratedQuestion{
		QuestionText:   questionText,
		Options:        options,
		CorrectAnswer:  correctAnswer,
		SolutionSteps:  solutionSteps,
		VariableValues: variableValues,
		Difficulty:     req.CalibratedDifficulty,
		Metadata: map[string]interface{}{
			"template_id":    req.Template.TemplateID,
			"bloom_level":    req.Template.BloomLevel,
			"concept_depth":  req.Template.ConceptDepth,
			"chapter":        req.Template.Chapter,
			"sub_chapter":    req.Template.SubChapter,
			"ncert_reference": req.Template.NCERTReference,
			"generation_time": time.Now().UTC(),
		},
	}, nil
}

// selectBestTemplate implements intelligent template selection algorithm
func (s *Service) selectBestTemplate(templates []*db.QuestionTemplate, selection TemplateSelection) *db.QuestionTemplate {
	var bestTemplate *db.QuestionTemplate
	var bestScore float64 = -1

	for _, template := range templates {
		score := s.calculateTemplateScore(template, selection)
		if score > bestScore {
			bestScore = score
			bestTemplate = template
		}
	}

	return bestTemplate
}

// calculateTemplateScore computes a quality score for template selection
func (s *Service) calculateTemplateScore(template *db.QuestionTemplate, selection TemplateSelection) float64 {
	var score float64

	// Factor 1: Difficulty alignment (40% weight)
	targetDifficulty := (selection.MinDifficulty + selection.MaxDifficulty) / 2
	difficultyAlignment := 1.0 - math.Abs(template.BaseDifficulty-targetDifficulty)
	score += 0.4 * difficultyAlignment

	// Factor 2: Template quality metrics (30% weight)
	qualityScore := 0.0
	if template.ValidationScore != nil {
		qualityScore += *template.ValidationScore
	}
	if template.ClarityScore != nil {
		qualityScore += *template.ClarityScore
	}
	if !template.AmbiguityFlag {
		qualityScore += 0.2 // Bonus for non-ambiguous questions
	}
	score += 0.3 * (qualityScore / 2.0) // Normalize to 0-1 range

	// Factor 3: Success rate (20% weight)
	if template.SuccessRate != nil {
		score += 0.2 * (*template.SuccessRate)
	}

	// Factor 4: Usage freshness (10% weight) - Avoid overused templates
	usageFreshness := 1.0 / (1.0 + float64(template.UsageCount)/100.0)
	score += 0.1 * usageFreshness

	return score
}

// generateVariableValue creates a value for a template variable based on its specification
func (s *Service) generateVariableValue(spec VariableSpec, difficulty float64, existingVars map[string]interface{}) (interface{}, error) {
	switch spec.Type {
	case "integer":
		return s.generateIntegerValue(spec, difficulty)
	case "float":
		return s.generateFloatValue(spec, difficulty)
	case "string":
		return s.generateStringValue(spec, difficulty)
	case "array":
		return s.generateArrayValue(spec, difficulty)
	case "computed":
		return s.generateComputedValue(spec, existingVars)
	default:
		return nil, fmt.Errorf("unsupported variable type: %s", spec.Type)
	}
}

// generateIntegerValue generates integer values with difficulty-based scaling
func (s *Service) generateIntegerValue(spec VariableSpec, difficulty float64) (int, error) {
	if spec.Range == nil {
		return 0, fmt.Errorf("integer variable %s requires range specification", spec.Name)
	}

	min := int(spec.Range.Min)
	max := int(spec.Range.Max)

	// Scale range based on difficulty for mathematical complexity
	if strings.Contains(strings.ToLower(spec.Name), "velocity") ||
		strings.Contains(strings.ToLower(spec.Name), "acceleration") {
		// Physics variables: higher difficulty = larger numbers
		scaleFactor := 1.0 + difficulty*2.0
		max = int(float64(max) * scaleFactor)
	}

	// Generate value within range
	if spec.Range.Step > 0 {
		// Discrete steps
		steps := int((float64(max-min) / spec.Range.Step) + 1)
		stepIndex := s.rand.Intn(steps)
		return min + int(float64(stepIndex)*spec.Range.Step), nil
	}

	// Continuous range
	return min + s.rand.Intn(max-min+1), nil
}

// generateFloatValue generates float values with precision control
func (s *Service) generateFloatValue(spec VariableSpec, difficulty float64) (float64, error) {
	if spec.Range == nil {
		return 0, fmt.Errorf("float variable %s requires range specification", spec.Name)
	}

	min := spec.Range.Min
	max := spec.Range.Max

	// Generate base value
	value := min + s.rand.Float64()*(max-min)

	// Apply difficulty-based precision
	precision := 2 // Default 2 decimal places
	if difficulty > 0.7 {
		precision = 3 // Higher precision for difficult questions
	}

	multiplier := math.Pow(10, float64(precision))
	return math.Round(value*multiplier) / multiplier, nil
}

// generateStringValue selects from predefined options or generates content
func (s *Service) generateStringValue(spec VariableSpec, difficulty float64) (string, error) {
	if len(spec.Options) == 0 {
		return "", fmt.Errorf("string variable %s requires options", spec.Name)
	}

	// Simple random selection from options
	index := s.rand.Intn(len(spec.Options))
	return spec.Options[index], nil
}

// generateArrayValue creates array values for complex question types
func (s *Service) generateArrayValue(spec VariableSpec, difficulty float64) ([]interface{}, error) {
	// Implementation depends on specific array requirements
	// For Phase 2.1, return simple placeholder
	return []interface{}{}, nil
}

// generateComputedValue evaluates formula-based variables
func (s *Service) generateComputedValue(spec VariableSpec, existingVars map[string]interface{}) (interface{}, error) {
	if spec.Formula == "" {
		return nil, fmt.Errorf("computed variable %s requires formula", spec.Name)
	}

	// Simple formula evaluation for Phase 2.1
	// In production, would use proper expression evaluator
	formula := spec.Formula
	for varName, value := range existingVars {
		placeholder := fmt.Sprintf("{{%s}}", varName)
		formula = strings.ReplaceAll(formula, placeholder, fmt.Sprintf("%v", value))
	}

	// Basic arithmetic evaluation (simplified)
	if strings.Contains(formula, "+") {
		parts := strings.Split(formula, "+")
		if len(parts) == 2 {
			a, _ := strconv.ParseFloat(strings.TrimSpace(parts[0]), 64)
			b, _ := strconv.ParseFloat(strings.TrimSpace(parts[1]), 64)
			return a + b, nil
		}
	}

	return formula, nil
}

// fillTemplateText replaces variable placeholders with generated values
func (s *Service) fillTemplateText(templateText string, variables map[string]interface{}) (string, error) {
	result := templateText

	for varName, value := range variables {
		placeholder := fmt.Sprintf("{{%s}}", varName)
		replacement := fmt.Sprintf("%v", value)
		result = strings.ReplaceAll(result, placeholder, replacement)
	}

	// Check for unfilled placeholders
	if strings.Contains(result, "{{") && strings.Contains(result, "}}") {
		return result, fmt.Errorf("unfilled placeholders remain in template")
	}

	return result, nil
}

// generateMCQOptions creates multiple choice options for questions
func (s *Service) generateMCQOptions(ctx context.Context, optionsTemplate string, variables map[string]interface{}, difficulty float64) (map[string]string, error) {
	// Parse options template (simplified for Phase 2.1)
	options := make(map[string]string)
	
	// Generate 4 options (A, B, C, D) with one correct answer
	options["A"] = "Option A placeholder"
	options["B"] = "Option B placeholder"
	options["C"] = "Option C placeholder"
	options["D"] = "Option D placeholder"

	return options, nil
}

// calculateCorrectAnswer computes the correct answer based on template logic
func (s *Service) calculateCorrectAnswer(template *db.QuestionTemplate, variables map[string]interface{}) (string, error) {
	// For Phase 2.1, implement basic answer calculation
	// In production, this would include comprehensive answer logic

	switch template.Subject {
	case "PHYSICS":
		return s.calculatePhysicsAnswer(template, variables)
	case "CHEMISTRY":
		return s.calculateChemistryAnswer(template, variables)
	case "MATHEMATICS":
		return s.calculateMathematicsAnswer(template, variables)
	case "BIOLOGY":
		return s.calculateBiologyAnswer(template, variables)
	default:
		return "Answer placeholder", nil
	}
}

// Subject-specific answer calculation methods
func (s *Service) calculatePhysicsAnswer(template *db.QuestionTemplate, variables map[string]interface{}) (string, error) {
	// Example: Kinematics calculation v = u + at
	if u, ok := variables["v0"].(int); ok {
		if a, ok := variables["a"].(int); ok {
			if t, ok := variables["t"].(int); ok {
				result := u + a*t
				return fmt.Sprintf("%d m/s", result), nil
			}
		}
	}
	return "Physics answer", nil
}

func (s *Service) calculateChemistryAnswer(template *db.QuestionTemplate, variables map[string]interface{}) (string, error) {
	return "Chemistry answer", nil
}

func (s *Service) calculateMathematicsAnswer(template *db.QuestionTemplate, variables map[string]interface{}) (string, error) {
	return "Mathematics answer", nil
}

func (s *Service) calculateBiologyAnswer(template *db.QuestionTemplate, variables map[string]interface{}) (string, error) {
	return "Biology answer", nil
}

// generateSolutionSteps creates step-by-step solution explanations
func (s *Service) generateSolutionSteps(template *db.QuestionTemplate, variables map[string]interface{}) ([]string, error) {
	// Generate solution steps based on template and subject
	steps := []string{
		"Step 1: Identify given values",
		"Step 2: Apply relevant formula/concept",
		"Step 3: Substitute values and calculate",
		"Step 4: Express final answer with units",
	}

	return steps, nil
}