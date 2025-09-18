import React, { useState, useEffect, useCallback } from 'react';
import QuestionCard from '../exams/QuestionCard';
import { contentAPI, QuestionWithOptions } from '../../api/content';

interface UserAnswers {
  [questionId: string]: number;
}

const TestPage: React.FC = () => {
  const [questions, setQuestions] = useState<QuestionWithOptions[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState<UserAnswers>({});
  const [showAnswers, setShowAnswers] = useState(false);
  const [timeLeft, setTimeLeft] = useState(3600); // 60 minutes in seconds

  // Load questions on component mount
  useEffect(() => {
    const loadQuestions = async () => {
      try {
        setLoading(true);
        const response = await contentAPI.getQuestions(1, 10);
        setQuestions(response.questions);
        setError(null);
      } catch (err) {
        setError('Failed to load questions. Please try again.');
        console.error('Error loading questions:', err);
      } finally {
        setLoading(false);
      }
    };

    loadQuestions();
  }, []);

  // Timer countdown
  useEffect(() => {
    if (timeLeft > 0 && !showAnswers) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [timeLeft, showAnswers]);

  // Handle answer selection
  const handleAnswerSelect = useCallback((questionId: string, optionNumber: number) => {
    setUserAnswers(prev => ({
      ...prev,
      [questionId]: optionNumber,
    }));
  }, []);

  // Navigation functions
  const goToQuestion = useCallback((index: number) => {
    if (index >= 0 && index < questions.length) {
      setCurrentQuestionIndex(index);
    }
  }, [questions.length]);

  const goToPrevious = useCallback(() => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  }, [currentQuestionIndex]);

  const goToNext = useCallback(() => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  }, [currentQuestionIndex, questions.length]);

  // Submit test
  const handleSubmit = useCallback(() => {
    setShowAnswers(true);
    setTimeLeft(0);
  }, []);

  // Format time display
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      if (showAnswers) return;
      
      switch (event.key) {
        case 'ArrowLeft':
          goToPrevious();
          break;
        case 'ArrowRight':
          goToNext();
          break;
        case '1':
        case '2':
        case '3':
        case '4':
          if (questions[currentQuestionIndex]) {
            handleAnswerSelect(questions[currentQuestionIndex].question_id, parseInt(event.key));
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [currentQuestionIndex, questions, showAnswers, handleAnswerSelect, goToPrevious, goToNext]);

  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="test-container">
        <div className="test-header">ERROR</div>
        <div style={{ padding: '40px', textAlign: 'center', color: '#d32f2f' }}>
          {error}
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];
  const answeredCount = Object.keys(userAnswers).length;

  return (
    <div className="test-container">
      {/* Test Header */}
      <div className="test-header">
        TEST INTERFACE
      </div>

      {/* Exam Info Bar */}
      <div className="exam-info">
        <div className="subject-info">
          Exam: NEET / AIPMT | Biology | Groupwise / Revision / Mock Test
        </div>
        <div className="time-info">
          Time Left: {formatTime(timeLeft)}
        </div>
      </div>

      {/* Main Content */}
      <div className="test-content">
        {/* Questions Area */}
        <div className="questions-area">
          {currentQuestion ? (
            <QuestionCard
              question={currentQuestion}
              questionIndex={currentQuestionIndex}
              selectedAnswer={userAnswers[currentQuestion.question_id]}
              onAnswerSelect={handleAnswerSelect}
              showAnswer={showAnswers}
            />
          ) : (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              No questions available
            </div>
          )}
        </div>

        {/* Question Palette */}
        <div className="question-palette">
          <div className="palette-title">Question Palette</div>
          <div className="palette-grid">
            {questions.map((_, index) => {
              const questionId = questions[index].question_id;
              const isAnswered = userAnswers[questionId] !== undefined;
              const isCurrent = index === currentQuestionIndex;
              
              return (
                <div
                  key={index}
                  className={`palette-item ${
                    isCurrent ? 'current' : ''
                  } ${
                    isAnswered ? 'answered' : ''
                  }`}
                  onClick={() => goToQuestion(index)}
                >
                  {index + 1}
                </div>
              );
            })}
          </div>

          {/* Legend */}
          <div style={{ marginTop: '20px', fontSize: '11px' }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
              <div className="palette-item" style={{ width: '16px', height: '16px', marginRight: '8px' }}></div>
              <span>Not Visited</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
              <div className="palette-item answered" style={{ width: '16px', height: '16px', marginRight: '8px' }}></div>
              <span>Answered</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
              <div className="palette-item current" style={{ width: '16px', height: '16px', marginRight: '8px' }}></div>
              <span>Current</span>
            </div>
          </div>

          {/* Stats */}
          <div style={{ marginTop: '16px', fontSize: '12px', background: '#f0f0f0', padding: '8px', borderRadius: '4px' }}>
            <div>Answered: {answeredCount}/{questions.length}</div>
            <div>Not Visited: {questions.length - answeredCount}</div>
          </div>
        </div>
      </div>

      {/* Navigation Controls */}
      <div className="navigation-controls">
        <div>
          <button 
            className="nav-button" 
            onClick={goToPrevious}
            disabled={currentQuestionIndex === 0}
          >
            ← Previous
          </button>
          <button 
            className="nav-button" 
            onClick={goToNext}
            disabled={currentQuestionIndex === questions.length - 1}
            style={{ marginLeft: '8px' }}
          >
            Next →
          </button>
        </div>

        <div>
          <button 
            className="nav-button primary" 
            onClick={handleSubmit}
            disabled={showAnswers}
          >
            {showAnswers ? 'Test Completed' : 'Submit Test'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default TestPage;