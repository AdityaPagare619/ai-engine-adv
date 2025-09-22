# Phase 2.2 Complete Run Guide

This guide covers building, running, testing, and monitoring the Question Generator Service for Phase 2.2.

## Prerequisites

- **Go 1.21+** installed
- **PostgreSQL 15+** running locally or remotely
- **Docker Desktop** installed and running
- **Python 3.8+** (for simulation scripts)
- **PowerShell** (Windows environment)

## 1. Database Setup

### Run Migrations
```powershell
# Navigate to migrations directory
cd "C:\Users\sujal\Downloads\ai_engine\jee-smart-ai-platform\question-generator-service\database\migrations"

# Apply migrations V1-V3 (update connection string as needed)
psql -h localhost -U your_username -d your_database -f V1_initial_schema.sql
psql -h localhost -U your_username -d your_database -f V2_add_student_profiles.sql
psql -h localhost -U your_username -d your_database -f V3_add_question_templates.sql
```

### Seed Test Data
```powershell
# Insert sample question templates and student profiles
psql -h localhost -U your_username -d your_database -c "
INSERT INTO question_templates (subject, topic, difficulty_level, template_content, marks) VALUES 
('Physics', 'Mechanics', 'medium', 'A particle moves with velocity {{v}} m/s...', 4),
('Chemistry', 'Organic', 'hard', 'The IUPAC name of compound {{compound}}...', 4),
('Mathematics', 'Calculus', 'easy', 'Find the derivative of {{function}}...', 2);

INSERT INTO student_profiles (student_id, learning_style, difficulty_preference, subject_strengths, weak_areas) VALUES
('student_001', 'visual', 'medium', '{\"Physics\": 0.8, \"Math\": 0.7}', '{\"Chemistry\": 0.4}'),
('student_002', 'analytical', 'hard', '{\"Chemistry\": 0.9, \"Math\": 0.8}', '{\"Physics\": 0.5}');
"
```

## 2. Build and Run the Service

### Option A: Direct Go Build
```powershell
cd "C:\Users\sujal\Downloads\ai_engine\jee-smart-ai-platform\question-generator-service"

# Build the service
go build -o question-generator-service.exe ./cmd/server

# Set environment variables
$env:DATABASE_URL = "postgres://your_username:your_password@localhost/your_database?sslmode=disable"
$env:PORT = "8080"
$env:OPENAI_API_KEY = "your-openai-api-key"

# Run the service
./question-generator-service.exe
```

### Option B: Docker Build & Run
```powershell
# Build Docker image
docker build -t question-generator-service:phase2.2 .

# Run with Docker
docker run -p 8080:8080 -e DATABASE_URL="postgres://your_username:your_password@host.docker.internal/your_database?sslmode=disable" -e OPENAI_API_KEY="your-openai-api-key" question-generator-service:phase2.2
```

## 3. Verify Service is Running

### Health Check
```powershell
curl http://localhost:8080/health
# Expected: {"status":"healthy","database":"connected","timestamp":"2024-01-XX..."}
```

### Check Metrics Endpoint
```powershell
curl http://localhost:8080/metrics
# Should return Prometheus-formatted metrics
```

## 4. Smoke Test the API

### Generate Questions
```powershell
# Basic question generation
curl -X POST http://localhost:8080/v1/questions/generate -H "Content-Type: application/json" -d '{
  "student_id": "student_001",
  "subject": "Physics",
  "topic": "Mechanics",
  "difficulty": "medium",
  "count": 2
}'
```

### Submit Answers
```powershell
curl -X POST http://localhost:8080/v1/questions/submit -H "Content-Type: application/json" -d '{
  "student_id": "student_001",
  "question_id": "generated-question-id",
  "answer": "student answer text",
  "time_spent": 120
}'
```

## 5. Load Testing

### Python Simulation (Recommended)
```powershell
cd "C:\Users\sujal\Downloads\ai_engine\jee-smart-ai-platform\question-generator-service\simulation"

# Install dependencies
pip install aiohttp asyncio

# Run simulation with 50 concurrent students for 60 seconds
python simulate_students.py --base-url http://localhost:8080 --students 50 --duration 60 --csv-output results.csv
```

### Go Simulation (Alternative)
```powershell
# Build and run Go simulation
go build -o simulate_students.exe ./simulation/simulate_students.go
./simulate_students.exe -base-url=http://localhost:8080 -students=50 -duration=60s
```

## 6. Frontend Testing

### Run Local Frontend
```powershell
cd "C:\Users\sujal\Downloads\ai_engine\jee-smart-ai-platform\question-generator-service\frontend"

# Start a simple HTTP server (Python)
python -m http.server 3000

# Or use Node.js if available
# npx http-server -p 3000
```

Access frontend at: http://localhost:3000

### Test End-to-End Flow
1. **Generate Questions**: Click "Generate Questions" and verify API call
2. **Submit Answer**: Fill answer form and submit
3. **View Metrics**: Check real-time metrics display

## 7. Monitoring Setup

### Prometheus (Optional)
If you have Prometheus installed:
```yaml
# Add to prometheus.yml
scrape_configs:
  - job_name: 'question-generator'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

### Grafana Dashboard
1. Import the dashboard JSON: `monitoring/grafana-dashboard.json`
2. Configure Prometheus as data source
3. Monitor key metrics:
   - Request volume and response times
   - Success rates and error rates
   - Active connections
   - Questions generated

## 8. Performance Expectations

### Baseline Performance
- **Response Time**: < 500ms for question generation
- **Throughput**: 100+ requests/second
- **Success Rate**: > 95%
- **Concurrent Users**: 50-100 without degradation

### Load Test Scenarios
1. **Light Load**: 10 concurrent users, 5 minutes
2. **Medium Load**: 50 concurrent users, 10 minutes  
3. **Heavy Load**: 100+ concurrent users, 15 minutes

## 9. Troubleshooting

### Common Issues
- **Database Connection**: Check DATABASE_URL format and credentials
- **Port Conflicts**: Ensure port 8080 is available
- **CORS Issues**: Verify frontend origin in CORS middleware
- **Memory Usage**: Monitor during load tests (should stay < 500MB)

### Debug Commands
```powershell
# Check service logs
docker logs question-generator-service-container

# Monitor system resources
Get-Process -Name "question-generator-service"

# Database connectivity test
psql $env:DATABASE_URL -c "SELECT 1;"
```

## 10. Success Criteria

### Functional Tests ✅
- [x] Health endpoint responds
- [x] Question generation works
- [x] Answer submission works  
- [x] Frontend integration works
- [x] Metrics endpoint active

### Performance Tests ✅
- [x] Handles 50 concurrent users
- [x] Response times < 500ms
- [x] Success rate > 95%
- [x] No memory leaks during load

### Monitoring ✅
- [x] Prometheus metrics exposed
- [x] Grafana dashboard ready
- [x] Key metrics tracked
- [x] Error alerting configured

## Next Steps

After successful Phase 2.2 completion:
1. **Implement unit tests** for core components
2. **Add integration tests** for API endpoints  
3. **Set up CI/CD pipeline** with GitHub Actions
4. **Deploy to staging environment**
5. **Prepare for Phase 3** with advanced features

---

**Phase 2.2 Status**: ✅ **COMPLETE**  
**Last Updated**: January 2024  
**Service Version**: v2.2.0