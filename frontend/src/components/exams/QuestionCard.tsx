import React, { memo, useCallback } from 'react';
import { QuestionWithOptions } from '../../api/content';

interface QuestionCardProps {
  question: QuestionWithOptions;
  questionIndex: number;
  selectedAnswer?: number;
  onAnswerSelect: (questionId: string, optionNumber: number) => void;
  showAnswer?: boolean;
}

const QuestionCard: React.FC<QuestionCardProps> = memo(({ 
  question, 
  questionIndex, 
  selectedAnswer, 
  onAnswerSelect,
  showAnswer = false 
}) => {
  const handleOptionSelect = useCallback((optionNumber: number) => {
    onAnswerSelect(question.question_id, optionNumber);
  }, [question.question_id, onAnswerSelect]);

  return (
    <div className="question-card">
      {/* Question Header */}
      <div className="question-header">
        <div className="question-number">
          Question No. {question.question_number}
        </div>
        <div className="question-type">
          Multiple Choice Question
        </div>
      </div>

      {/* Question Content */}
      <div className="question-content">
        <div className="question-text">
          <strong>Q{questionIndex + 1}.</strong> {question.question_text}
        </div>
        
        {/* Placeholder for question diagram */}
        {question.question_id === 'SHT-PHY-001-Q-00001' && (
          <div className="question-diagram">
            <div className="diagram-placeholder">
              [Diagram: Circular disc with removed section]
            </div>
          </div>
        )}
      </div>

      {/* Answer Options */}
      <div className="options-container">
        {question.options.map((option) => {
          const isSelected = selectedAnswer === option.option_number;
          const isCorrect = showAnswer && option.is_correct;
          const isWrong = showAnswer && isSelected && !option.is_correct;
          
          return (
            <div 
              key={option.option_id}
              className={`option ${
                isSelected ? 'selected' : ''
              } ${
                isCorrect ? 'correct' : ''
              } ${
                isWrong ? 'wrong' : ''
              }`}
              onClick={() => !showAnswer && handleOptionSelect(option.option_number)}
            >
              <div className="option-marker">
                {String.fromCharCode(64 + option.option_number)}
              </div>
              <div className="option-text">
                {option.option_text}
              </div>
              {showAnswer && option.is_correct && (
                <div className="correct-indicator">✓</div>
              )}
            </div>
          );
        })}
      </div>

      {/* Show correct answer when in review mode */}
      {showAnswer && (
        <div className="answer-explanation">
          <div className="correct-answer">
            <strong>Correct Answer:</strong> {String.fromCharCode(64 + parseInt(question.correct_option))}
          </div>
        </div>
      )}
    </div>
  );
});

QuestionCard.displayName = 'QuestionCard';

export default QuestionCard;