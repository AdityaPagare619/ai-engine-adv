// simulate_students.go
// Large-Scale Student Simulation Framework - Go Implementation
// Phase 2.2 Load Testing with configurable concurrency

package main

import (
	"bytes"
	"context"
	"encoding/csv"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"math/rand"
	"net/http"
	"os"
	"sync"
	"time"
)

// Configuration for simulation
type SimulationConfig struct {
	APIBaseURL      string
	StudentCount    int
	ConcurrentUsers int
	TestDuration    time.Duration
	RequestsPerUser int
	OutputFile      string
	Verbose         bool
}

// Student simulation profile
type VirtualStudent struct {
	ID          string
	ExamType    string
	Subject     string
	Format      string
	Difficulty  float64
	Performance float64 // Simulated ability level
}

// Request/Response structures
type QuestionRequest struct {
	StudentID           string  `json:"student_id"`
	TopicID            string  `json:"topic_id"`
	ExamType           string  `json:"exam_type"`
	Subject            string  `json:"subject"`
	Format             string  `json:"format"`
	RequestedDifficulty float64 `json:"requested_difficulty"`
	SessionID          string  `json:"session_id"`
	RequestID          string  `json:"request_id"`
}

type QuestionResponse struct {
	QuestionID     string                 `json:"question_id"`
	QuestionText   string                 `json:"question_text"`
	Options        map[string]string      `json:"options"`
	CorrectAnswer  string                 `json:"correct_answer"`
	Difficulty     float64               `json:"difficulty"`
	GenerationTime int64                 `json:"generation_time"`
	QualityScore   float64               `json:"quality_score"`
	Status         string                `json:"status"`
	Metadata       map[string]interface{} `json:"metadata"`
}

// Performance metrics
type StudentMetrics struct {
	StudentID          string
	TotalRequests      int
	SuccessfulRequests int
	FailedRequests     int
	AvgResponseTime    time.Duration
	MinResponseTime    time.Duration
	MaxResponseTime    time.Duration
	TotalResponseTime  time.Duration
	ErrorMessages      []string
	QuestionsAnswered  int
	CorrectAnswers     int
	Accuracy           float64
}

// Global metrics collector
type MetricsCollector struct {
	mutex           sync.RWMutex
	StudentMetrics  map[string]*StudentMetrics
	StartTime       time.Time
	EndTime         time.Time
	TotalRequests   int64
	SuccessRequests int64
	ErrorRequests   int64
	ResponseTimes   []time.Duration
}

func NewMetricsCollector() *MetricsCollector {
	return &MetricsCollector{
		StudentMetrics: make(map[string]*StudentMetrics),
		StartTime:      time.Now(),
		ResponseTimes:  make([]time.Duration, 0),
	}
}

func (mc *MetricsCollector) RecordRequest(studentID string, responseTime time.Duration, success bool, errorMsg string) {
	mc.mutex.Lock()
	defer mc.mutex.Unlock()

	mc.TotalRequests++
	mc.ResponseTimes = append(mc.ResponseTimes, responseTime)

	if success {
		mc.SuccessRequests++
	} else {
		mc.ErrorRequests++
	}

	// Update student-specific metrics
	if _, exists := mc.StudentMetrics[studentID]; !exists {
		mc.StudentMetrics[studentID] = &StudentMetrics{
			StudentID:       studentID,
			MinResponseTime: responseTime,
			MaxResponseTime: responseTime,
			ErrorMessages:   make([]string, 0),
		}
	}

	student := mc.StudentMetrics[studentID]
	student.TotalRequests++
	student.TotalResponseTime += responseTime

	if success {
		student.SuccessfulRequests++
	} else {
		student.FailedRequests++
		if errorMsg != "" {
			student.ErrorMessages = append(student.ErrorMessages, errorMsg)
		}
	}

	if responseTime < student.MinResponseTime {
		student.MinResponseTime = responseTime
	}
	if responseTime > student.MaxResponseTime {
		student.MaxResponseTime = responseTime
	}

	student.AvgResponseTime = student.TotalResponseTime / time.Duration(student.TotalRequests)
}

func (mc *MetricsCollector) RecordAnswer(studentID string, correct bool) {
	mc.mutex.Lock()
	defer mc.mutex.Unlock()

	if student, exists := mc.StudentMetrics[studentID]; exists {
		student.QuestionsAnswered++
		if correct {
			student.CorrectAnswers++
		}
		student.Accuracy = float64(student.CorrectAnswers) / float64(student.QuestionsAnswered)
	}
}

func (mc *MetricsCollector) GetSummary() map[string]interface{} {
	mc.mutex.RLock()
	defer mc.mutex.RUnlock()

	mc.EndTime = time.Now()
	duration := mc.EndTime.Sub(mc.StartTime)

	// Calculate percentiles
	var p50, p95, p99 time.Duration
	if len(mc.ResponseTimes) > 0 {
		// Simple percentile calculation (for production use proper sorting)
		total := len(mc.ResponseTimes)
		p50 = mc.ResponseTimes[total*50/100]
		p95 = mc.ResponseTimes[total*95/100]
		p99 = mc.ResponseTimes[total*99/100]
	}

	var avgResponseTime time.Duration
	if len(mc.ResponseTimes) > 0 {
		var total time.Duration
		for _, rt := range mc.ResponseTimes {
			total += rt
		}
		avgResponseTime = total / time.Duration(len(mc.ResponseTimes))
	}

	return map[string]interface{}{
		"simulation_duration":    duration.Seconds(),
		"total_requests":        mc.TotalRequests,
		"successful_requests":   mc.SuccessRequests,
		"failed_requests":       mc.ErrorRequests,
		"success_rate":          float64(mc.SuccessRequests) / float64(mc.TotalRequests) * 100,
		"requests_per_second":   float64(mc.TotalRequests) / duration.Seconds(),
		"avg_response_time_ms":  avgResponseTime.Milliseconds(),
		"p50_response_time_ms":  p50.Milliseconds(),
		"p95_response_time_ms":  p95.Milliseconds(),
		"p99_response_time_ms":  p99.Milliseconds(),
		"concurrent_users":      len(mc.StudentMetrics),
		"start_time":           mc.StartTime.Format(time.RFC3339),
		"end_time":             mc.EndTime.Format(time.RFC3339),
	}
}

// Generate realistic virtual student profiles
func GenerateVirtualStudents(count int) []VirtualStudent {
	rand.Seed(time.Now().UnixNano())
	
	examTypes := []string{"JEE_MAIN", "JEE_ADVANCED", "NEET", "FOUNDATION"}
	subjects := []string{"PHYSICS", "CHEMISTRY", "MATHEMATICS", "BIOLOGY"}
	formats := []string{"MCQ", "NUMERICAL", "ASSERTION_REASON", "PASSAGE"}
	
	students := make([]VirtualStudent, count)
	
	for i := 0; i < count; i++ {
		examType := examTypes[rand.Intn(len(examTypes))]
		
		// Subject selection based on exam type
		var availableSubjects []string
		if examType == "NEET" {
			availableSubjects = []string{"PHYSICS", "CHEMISTRY", "BIOLOGY"}
		} else if examType == "JEE_MAIN" || examType == "JEE_ADVANCED" {
			availableSubjects = []string{"PHYSICS", "CHEMISTRY", "MATHEMATICS"}
		} else {
			availableSubjects = subjects
		}
		
		subject := availableSubjects[rand.Intn(len(availableSubjects))]
		format := formats[rand.Intn(len(formats))]
		
		// Normal distribution for difficulty preference and performance
		difficulty := 0.3 + rand.Float64()*0.4 // Between 0.3 and 0.7
		performance := 0.2 + rand.Float64()*0.6 // Between 0.2 and 0.8
		
		students[i] = VirtualStudent{
			ID:          fmt.Sprintf("sim_student_%05d", i+1),
			ExamType:    examType,
			Subject:     subject,
			Format:      format,
			Difficulty:  difficulty,
			Performance: performance,
		}
	}
	
	return students
}

// Simulate a single student's behavior
func SimulateStudent(ctx context.Context, config SimulationConfig, student VirtualStudent, 
	metrics *MetricsCollector, wg *sync.WaitGroup) {
	defer wg.Done()

	client := &http.Client{
		Timeout: 30 * time.Second,
	}

	for i := 0; i < config.RequestsPerUser; i++ {
		select {
		case <-ctx.Done():
			return
		default:
			// Generate realistic question request
			request := QuestionRequest{
				StudentID:           student.ID,
				TopicID:            generateTopicID(student.Subject),
				ExamType:           student.ExamType,
				Subject:            student.Subject,
				Format:             student.Format,
				RequestedDifficulty: student.Difficulty + (rand.Float64()-0.5)*0.2, // ±0.1 variation
				SessionID:          fmt.Sprintf("session_%s_%d", student.ID, i),
				RequestID:          fmt.Sprintf("req_%s_%d_%d", student.ID, i, time.Now().UnixNano()),
			}

			// Measure response time
			startTime := time.Now()
			success, errorMsg := makeQuestionRequest(client, config.APIBaseURL, request)
			responseTime := time.Since(startTime)

			// Record metrics
			metrics.RecordRequest(student.ID, responseTime, success, errorMsg)

			if config.Verbose {
				status := "SUCCESS"
				if !success {
					status = "FAILED: " + errorMsg
				}
				log.Printf("Student %s: Request %d/%d - %s (%s)", 
					student.ID, i+1, config.RequestsPerUser, status, responseTime)
			}

			// Simulate answer submission based on student performance
			if success && rand.Float64() < 0.8 { // 80% answer questions
				correct := rand.Float64() < student.Performance
				metrics.RecordAnswer(student.ID, correct)
			}

			// Realistic interval between requests (1-5 seconds)
			time.Sleep(time.Duration(1000+rand.Intn(4000)) * time.Millisecond)
		}
	}
}

// Make HTTP request to question generation API
func makeQuestionRequest(client *http.Client, baseURL string, request QuestionRequest) (bool, string) {
	requestBody, err := json.Marshal(request)
	if err != nil {
		return false, fmt.Sprintf("JSON marshal error: %v", err)
	}

	url := fmt.Sprintf("%s/v1/questions/generate", baseURL)
	
	httpReq, err := http.NewRequest("POST", url, bytes.NewBuffer(requestBody))
	if err != nil {
		return false, fmt.Sprintf("Request creation error: %v", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Accept", "application/json")
	httpReq.Header.Set("X-Request-ID", request.RequestID)

	resp, err := client.Do(httpReq)
	if err != nil {
		return false, fmt.Sprintf("HTTP request error: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return false, fmt.Sprintf("HTTP %d: %s", resp.StatusCode, resp.Status)
	}

	// Parse response to validate
	var response QuestionResponse
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		return false, fmt.Sprintf("Response parsing error: %v", err)
	}

	return true, ""
}

// Generate realistic topic IDs based on subject
func generateTopicID(subject string) string {
	topics := map[string][]string{
		"PHYSICS": {
			"PHY_MECHANICS_KINEMATICS", "PHY_MECHANICS_DYNAMICS", "PHY_THERMODYNAMICS",
			"PHY_ELECTROMAGNETISM", "PHY_OPTICS", "PHY_MODERN_PHYSICS",
		},
		"CHEMISTRY": {
			"CHEM_PHYSICAL_CHEMISTRY", "CHEM_ORGANIC_CHEMISTRY", "CHEM_INORGANIC_CHEMISTRY",
			"CHEM_CHEMICAL_BONDING", "CHEM_THERMODYNAMICS", "CHEM_ATOMIC_STRUCTURE",
		},
		"MATHEMATICS": {
			"MATH_ALGEBRA", "MATH_CALCULUS", "MATH_TRIGONOMETRY",
			"MATH_COORDINATE_GEOMETRY", "MATH_PROBABILITY", "MATH_VECTORS",
		},
		"BIOLOGY": {
			"BIO_CELL_BIOLOGY", "BIO_GENETICS", "BIO_ECOLOGY",
			"BIO_HUMAN_PHYSIOLOGY", "BIO_PLANT_PHYSIOLOGY", "BIO_EVOLUTION",
		},
	}

	subjectTopics := topics[subject]
	return subjectTopics[rand.Intn(len(subjectTopics))]
}

// Export metrics to CSV
func ExportMetricsToCSV(metrics *MetricsCollector, filename string) error {
	file, err := os.Create(filename)
	if err != nil {
		return fmt.Errorf("create file error: %w", err)
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	// Write header
	header := []string{
		"student_id", "total_requests", "successful_requests", "failed_requests",
		"success_rate", "avg_response_time_ms", "min_response_time_ms", "max_response_time_ms",
		"questions_answered", "correct_answers", "accuracy", "error_count",
	}
	writer.Write(header)

	// Write student data
	metrics.mutex.RLock()
	defer metrics.mutex.RUnlock()

	for _, student := range metrics.StudentMetrics {
		successRate := float64(student.SuccessfulRequests) / float64(student.TotalRequests) * 100
		
		record := []string{
			student.StudentID,
			fmt.Sprintf("%d", student.TotalRequests),
			fmt.Sprintf("%d", student.SuccessfulRequests),
			fmt.Sprintf("%d", student.FailedRequests),
			fmt.Sprintf("%.2f", successRate),
			fmt.Sprintf("%d", student.AvgResponseTime.Milliseconds()),
			fmt.Sprintf("%d", student.MinResponseTime.Milliseconds()),
			fmt.Sprintf("%d", student.MaxResponseTime.Milliseconds()),
			fmt.Sprintf("%d", student.QuestionsAnswered),
			fmt.Sprintf("%d", student.CorrectAnswers),
			fmt.Sprintf("%.2f", student.Accuracy*100),
			fmt.Sprintf("%d", len(student.ErrorMessages)),
		}
		writer.Write(record)
	}

	return nil
}

func main() {
	// Command-line flags
	var config SimulationConfig
	flag.StringVar(&config.APIBaseURL, "url", "http://localhost:8080", "API base URL")
	flag.IntVar(&config.StudentCount, "students", 100, "Number of virtual students")
	flag.IntVar(&config.ConcurrentUsers, "concurrent", 10, "Concurrent users")
	flag.DurationVar(&config.TestDuration, "duration", 5*time.Minute, "Test duration")
	flag.IntVar(&config.RequestsPerUser, "requests", 10, "Requests per user")
	flag.StringVar(&config.OutputFile, "output", "simulation_results.csv", "Output CSV file")
	flag.BoolVar(&config.Verbose, "verbose", false, "Verbose logging")
	flag.Parse()

	log.Printf("Starting Student Simulation with %d students, %d concurrent users", 
		config.StudentCount, config.ConcurrentUsers)
	
	// Generate virtual students
	students := GenerateVirtualStudents(config.StudentCount)
	
	// Initialize metrics collector
	metrics := NewMetricsCollector()
	
	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), config.TestDuration)
	defer cancel()
	
	// Start simulation
	var wg sync.WaitGroup
	semaphore := make(chan struct{}, config.ConcurrentUsers)
	
	for _, student := range students {
		wg.Add(1)
		semaphore <- struct{}{} // Acquire semaphore
		
		go func(s VirtualStudent) {
			defer func() { <-semaphore }() // Release semaphore
			SimulateStudent(ctx, config, s, metrics, &wg)
		}(student)
	}
	
	// Wait for completion or timeout
	wg.Wait()
	
	// Generate summary
	summary := metrics.GetSummary()
	log.Println("\n=== SIMULATION SUMMARY ===")
	for key, value := range summary {
		log.Printf("%s: %v", key, value)
	}
	
	// Export detailed metrics
	if err := ExportMetricsToCSV(metrics, config.OutputFile); err != nil {
		log.Printf("Error exporting metrics: %v", err)
	} else {
		log.Printf("Detailed metrics exported to: %s", config.OutputFile)
	}
	
	log.Println("Simulation completed successfully!")
}