package api

import (
    "context"
    "encoding/json"
    "net/http"
    "time"

    "github.com/yourproject/internal/service"
    "github.com/yourproject/pkg/logger"
)

type Handler struct {
    GeneratorService *service.GeneratorService
    Logger           *logger.Logger
    RagClient        *service.RagClient
}

type GenerateRequest struct {
    StudentID string `json:"student_id"`
    Topic     string `json:"topic"`
    Difficulty string `json:"difficulty"`
}

type GenerateResponse struct {
    QuestionID string `json:"question_id"`
    Question   string `json:"question"`
    Options    []string `json:"options"`
    QualityScore float64 `json:"quality_score"`
}

func (h *Handler) GenerateQuestion(w http.ResponseWriter, r *http.Request) {
    var req GenerateRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid request", http.StatusBadRequest)
        return
    }

    ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
    defer cancel()

    question, err := h.GeneratorService.Generate(ctx, req.StudentID, req.Topic, req.Difficulty)
    if err != nil {
        http.Error(w, "Failed to generate question", http.StatusInternalServerError)
        return
    }

    ragResp, err := h.RagClient.AssessQuestionQuality(ctx, question.Text)
    if err != nil {
        // Log error but continue
        ragResp = &service.RagResponse{Score: 0.0}
    }

    logEntry := logger.GenerationLog{
        StudentID:      req.StudentID,
        QuestionID:     question.ID,
        GenerationTime: time.Now(),
        Parameters: map[string]interface{}{
            "topic":     req.Topic,
            "difficulty": req.Difficulty,
        },
        Result: question.Text,
    }
    h.Logger.Save(logEntry)

    resp := GenerateResponse{
        QuestionID:   question.ID,
        Question:     question.Text,
        Options:      question.Options,
        QualityScore: ragResp.Score,
    }
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(resp)
}
