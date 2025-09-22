// Question Generator Frontend - Phase 2.2 Testing Interface
class QuestionGeneratorApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8080/v1';
        this.currentQuestion = null;
        this.selectedAnswer = null;
        
        this.initializeEventListeners();
        this.checkApiStatus();
        this.setupDifficultySlider();
    }

    // Initialize all event listeners
    initializeEventListeners() {
        const questionForm = document.getElementById('questionForm');
        const generateBtn = document.getElementById('generateBtn');
        const clearBtn = document.getElementById('clearBtn');
        const submitAnswer = document.getElementById('submitAnswer');
        const showSolution = document.getElementById('showSolution');
        const generateAnother = document.getElementById('generateAnother');
        const retryBtn = document.getElementById('retryBtn');

        // Form submission
        questionForm.addEventListener('submit', (e) => this.handleQuestionGeneration(e));
        
        // Button clicks
        clearBtn.addEventListener('click', () => this.clearForm());
        submitAnswer.addEventListener('click', () => this.handleAnswerSubmission());
        showSolution.addEventListener('click', () => this.showSolution());
        generateAnother.addEventListener('click', () => this.resetAndGenerate());
        retryBtn.addEventListener('click', () => this.retryLastRequest());

        // Subject and exam type validation
        document.getElementById('examType').addEventListener('change', () => this.validateSubjectExamCombination());
        document.getElementById('subject').addEventListener('change', () => this.validateSubjectExamCombination());
    }

    // Setup difficulty slider with real-time updates
    setupDifficultySlider() {
        const difficultySlider = document.getElementById('difficulty');
        const difficultyValue = document.getElementById('difficultyValue');
        
        difficultySlider.addEventListener('input', (e) => {
            const value = parseFloat(e.target.value).toFixed(1);
            difficultyValue.textContent = value;
            
            // Update difficulty label
            let label = 'Medium';
            if (value <= 0.3) label = 'Easy';
            else if (value <= 0.7) label = 'Medium';
            else label = 'Hard';
            
            difficultyValue.setAttribute('data-label', label);
        });
    }

    // Check API server status
    async checkApiStatus() {
        const statusElement = document.getElementById('apiStatus');
        
        try {
            const response = await fetch(`${this.apiBaseUrl.replace('/v1', '')}/health`, {
                method: 'GET',
                timeout: 5000
            });
            
            if (response.ok) {
                const data = await response.json();
                statusElement.textContent = `✅ Online (${data.version})`;
                statusElement.className = 'status-online';
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            statusElement.textContent = '❌ Offline';
            statusElement.className = 'status-offline';
            console.warn('API health check failed:', error);
        }
    }

    // Validate subject-exam type combinations
    validateSubjectExamCombination() {
        const examType = document.getElementById('examType').value;
        const subject = document.getElementById('subject').value;
        const generateBtn = document.getElementById('generateBtn');

        let isValid = true;
        let errorMessage = '';

        // Business rules validation
        if (examType === 'NEET' && subject === 'MATHEMATICS') {
            isValid = false;
            errorMessage = 'NEET exam does not include Mathematics';
        } else if (examType === 'JEE_MAIN' && subject === 'BIOLOGY') {
            isValid = false;
            errorMessage = 'JEE Main does not typically include Biology';
        }

        // Update UI based on validation
        const formGroup = document.querySelector('.form-actions');
        let existingError = formGroup.querySelector('.validation-error');
        
        if (!isValid) {
            generateBtn.disabled = true;
            if (!existingError) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'validation-error';
                errorDiv.textContent = errorMessage;
                formGroup.insertBefore(errorDiv, generateBtn);
            } else {
                existingError.textContent = errorMessage;
            }
        } else {
            generateBtn.disabled = false;
            if (existingError) {
                existingError.remove();
            }
        }
    }

    // Handle question generation form submission
    async handleQuestionGeneration(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const requestData = {
            student_id: formData.get('studentId'),
            topic_id: formData.get('topicId'),
            exam_type: formData.get('examType'),
            subject: formData.get('subject'),
            format: formData.get('format'),
            requested_difficulty: parseFloat(formData.get('difficulty')),
            session_id: this.generateSessionId(),
            request_id: this.generateRequestId()
        };

        this.showLoadingState();
        this.simulateProgressSteps();

        try {
            const response = await this.callQuestionGenerationAPI(requestData);
            
            if (response.status === 'success') {
                this.currentQuestion = response;
                this.displayGeneratedQuestion(response);
                this.hideLoadingState();
            } else {
                throw new Error(response.message || 'Generation failed');
            }
        } catch (error) {
            this.hideLoadingState();
            this.showError('Question Generation Failed', error.message);
            console.error('Question generation error:', error);
        }
    }

    // Call the question generation API with proper error handling
    async callQuestionGenerationAPI(requestData) {
        const response = await fetch(`${this.apiBaseUrl}/questions/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Request-ID': requestData.request_id
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    }

    // Simulate progress steps during generation
    simulateProgressSteps() {
        const steps = ['step1', 'step2', 'step3', 'step4'];
        
        steps.forEach((stepId, index) => {
            setTimeout(() => {
                document.getElementById(stepId).innerHTML = '✓ ' + document.getElementById(stepId).textContent.replace('⏳ ', '');
                document.getElementById(stepId).classList.add('completed');
            }, (index + 1) * 800);
        });
    }

    // Display the generated question
    displayGeneratedQuestion(questionData) {
        // Hide other sections
        this.hideAllSections();
        
        // Show question section
        document.getElementById('questionSection').classList.remove('hidden');

        // Populate question details
        document.getElementById('questionId').textContent = questionData.question_id;
        document.getElementById('questionText').textContent = questionData.question_text;
        
        // Set metadata
        document.getElementById('difficultyBadge').textContent = `Difficulty: ${questionData.difficulty}`;
        document.getElementById('generationTime').textContent = `${questionData.generation_time}ms`;

        // Populate options if MCQ
        this.displayQuestionOptions(questionData);

        // Update quality metrics
        this.updateQualityMetrics(questionData);
    }

    // Display question options based on format
    displayQuestionOptions(questionData) {
        const optionsContainer = document.getElementById('optionsContainer');
        optionsContainer.innerHTML = '';

        if (questionData.options && Object.keys(questionData.options).length > 0) {
            const optionsList = document.createElement('div');
            optionsList.className = 'options-list';

            Object.entries(questionData.options).forEach(([key, value]) => {
                const optionElement = document.createElement('label');
                optionElement.className = 'option-item';
                
                optionElement.innerHTML = `
                    <input type="radio" name="answer" value="${key}">
                    <span class="option-key">${key}.</span>
                    <span class="option-text">${value}</span>
                `;

                optionsList.appendChild(optionElement);
            });

            optionsContainer.appendChild(optionsList);

            // Add event listeners for option selection
            optionsContainer.querySelectorAll('input[name="answer"]').forEach(input => {
                input.addEventListener('change', (e) => {
                    this.selectedAnswer = e.target.value;
                    document.getElementById('submitAnswer').disabled = false;
                });
            });
        } else {
            optionsContainer.innerHTML = '<p class="no-options">Numerical answer question</p>';
            document.getElementById('submitAnswer').disabled = false;
        }
    }

    // Update quality metrics display
    updateQualityMetrics(questionData) {
        const metadata = questionData.metadata || {};
        
        document.getElementById('ragAlignment').textContent = 
            metadata.rag_alignment_score ? `${(metadata.rag_alignment_score * 100).toFixed(1)}%` : 'N/A';
        
        document.getElementById('bktMastery').textContent = 
            metadata.bkt_mastery ? `${(metadata.bkt_mastery * 100).toFixed(1)}%` : 'N/A';
        
        document.getElementById('qualityScore').textContent = 
            questionData.quality_score ? `${(questionData.quality_score * 100).toFixed(1)}%` : 'N/A';
        
        document.getElementById('templateId').textContent = 
            metadata.template_id || 'N/A';
    }

    // Handle answer submission
    handleAnswerSubmission() {
        if (!this.selectedAnswer && this.currentQuestion.options) {
            alert('Please select an answer before submitting.');
            return;
        }

        const isCorrect = this.selectedAnswer === this.currentQuestion.correct_answer;
        
        // Show answer result
        this.displayAnswerResult(isCorrect);
    }

    // Display answer result
    displayAnswerResult(isCorrect) {
        const answerSection = document.getElementById('answerSection');
        const answerStatus = document.getElementById('answerStatus');
        const correctAnswer = document.getElementById('correctAnswer');

        answerSection.classList.remove('hidden');

        if (isCorrect) {
            answerStatus.innerHTML = '<div class="status-correct">✅ Correct!</div>';
        } else {
            answerStatus.innerHTML = '<div class="status-incorrect">❌ Incorrect</div>';
        }

        correctAnswer.innerHTML = `
            <strong>Correct Answer:</strong> ${this.currentQuestion.correct_answer}
            ${this.currentQuestion.options ? ` - ${this.currentQuestion.options[this.currentQuestion.correct_answer]}` : ''}
        `;
    }

    // Show solution
    showSolution() {
        const solutionSteps = document.getElementById('solutionSteps');
        const answerSection = document.getElementById('answerSection');
        
        answerSection.classList.remove('hidden');

        // Mock solution for Phase 2.2
        solutionSteps.innerHTML = `
            <h4>Solution Steps:</h4>
            <ol>
                <li>Apply the formula: g = 9.8 m/s²</li>
                <li>This is a standard constant for Earth's gravitational acceleration</li>
                <li>The value is approximately 9.8 m/s² at sea level</li>
            </ol>
        `;
    }

    // Utility functions
    showLoadingState() {
        this.hideAllSections();
        document.getElementById('loadingSection').classList.remove('hidden');
        
        // Reset progress steps
        ['step1', 'step2', 'step3', 'step4'].forEach(stepId => {
            const step = document.getElementById(stepId);
            step.classList.remove('completed');
            step.innerHTML = step.innerHTML.replace('✓ ', '⏳ ');
        });
    }

    hideLoadingState() {
        document.getElementById('loadingSection').classList.add('hidden');
    }

    hideAllSections() {
        ['loadingSection', 'questionSection', 'answerSection', 'errorSection'].forEach(id => {
            document.getElementById(id).classList.add('hidden');
        });
    }

    showError(title, message) {
        this.hideAllSections();
        
        document.getElementById('errorSection').classList.remove('hidden');
        document.getElementById('errorMessage').innerHTML = `
            <strong>${title}:</strong><br>
            ${message}
        `;
    }

    clearForm() {
        document.getElementById('questionForm').reset();
        document.getElementById('difficultyValue').textContent = '0.5';
        this.hideAllSections();
        this.currentQuestion = null;
        this.selectedAnswer = null;
    }

    resetAndGenerate() {
        this.hideAllSections();
        this.currentQuestion = null;
        this.selectedAnswer = null;
    }

    retryLastRequest() {
        const form = document.getElementById('questionForm');
        form.dispatchEvent(new Event('submit'));
    }

    // Utility functions for ID generation
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    generateRequestId() {
        return 'req_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.questionGeneratorApp = new QuestionGeneratorApp();
});