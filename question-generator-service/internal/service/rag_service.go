package service

import (
    "context"
    "encoding/json"
    "errors"
    "fmt"
    "net/http"
    "time"
)

type RagClient struct {
    BaseURL    string
    HttpClient *http.Client
}

type RagResponse struct {
    Score float64 `json:"score"`
    Data  string  `json:"data"`
}

func NewRagClient(baseURL string) *RagClient {
    return &RagClient{
        BaseURL:    baseURL,
        HttpClient: &http.Client{Timeout: 5 * time.Second},
    }
}

func (c *RagClient) AssessQuestionQuality(ctx context.Context, question string) (*RagResponse, error) {
    req, err := http.NewRequestWithContext(ctx, http.MethodPost, fmt.Sprintf("%s/api/quality", c.BaseURL), nil)
    if err != nil {
        return nil, err
    }
    // Add question param, headers etc. as needed

    resp, err := c.HttpClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        return nil, errors.New("rag service returned error status")
    }

    var ragResp RagResponse
    if err := json.NewDecoder(resp.Body).Decode(&ragResp); err != nil {
        return nil, err
    }

    return &ragResp, nil
}
