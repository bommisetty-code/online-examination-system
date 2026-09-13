import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { studentService } from '../services/studentService';
import './StudentAnswerReview.css';

function StudentAnswerReview() {
  const { submissionId } = useParams();
  const navigate = useNavigate();

  const [reviewData, setReviewData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadReview();
  }, [submissionId]);

  const loadReview = async () => {
    try {
      setLoading(true);
      setError('');

      if (!submissionId) {
        setError('Invalid submission.');
        return;
      }

      const data = await studentService.getResultReview(
        submissionId
      );

      setReviewData(data);

    } catch (err) {
      console.error('Failed to load answer review:', err);

      setError(
        err.response?.data?.message ||
        'Failed to load answer review.'
      );
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="review-page">
        <div className="review-container">
          <div className="review-loading">
            Loading answer review...
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="review-page">
        <div className="review-container">

          <div className="review-error">
            {error}
          </div>

          <button
            type="button"
            className="back-button"
            onClick={() => navigate('/student/dashboard')}
          >
            Back to Dashboard
          </button>

        </div>
      </div>
    );
  }

  const review = reviewData?.review || [];
  const summary = reviewData?.summary || {};
  const result = reviewData?.result || {};
  const exam = reviewData?.exam || {};
  const submission = reviewData?.submission || {};

  const correctCount = summary.correct ?? 0;
  const incorrectCount = summary.incorrect ?? 0;
  const unansweredCount = summary.unanswered ?? 0;

  const totalQuestions =
    review.length ||
    summary.total_questions ||
    result.total_questions ||
    0;

  return (
    <div className="review-page">

      <div className="review-container">

        {/* =====================================================
            HEADER
        ===================================================== */}

        <div className="review-header">

          <button
            type="button"
            className="back-button"
            onClick={() => navigate('/student/dashboard')}
          >
            ← Back to Dashboard
          </button>

          <h1>Answer Review</h1>

          <p>
            {exam.name || 'Exam'}
          </p>

        </div>


        {/* =====================================================
            RESULT SUMMARY
        ===================================================== */}

        <div className="review-summary">

          <div className="summary-card">
            <span className="summary-label">
              Total Questions
            </span>

            <strong>
              {totalQuestions}
            </strong>
          </div>


          <div className="summary-card correct-card">
            <span className="summary-label">
              Correct
            </span>

            <strong>
              {correctCount}
            </strong>
          </div>


          <div className="summary-card incorrect-card">
            <span className="summary-label">
              Incorrect
            </span>

            <strong>
              {incorrectCount}
            </strong>
          </div>


          <div className="summary-card unanswered-card">
            <span className="summary-label">
              Unanswered
            </span>

            <strong>
              {unansweredCount}
            </strong>
          </div>

        </div>


        {/* =====================================================
            SCORE
        ===================================================== */}

        {result && (
          <div className="score-section">

            <div>
              <span>Score</span>
              <strong>
                {result.score ?? 0}
              </strong>
            </div>

            <div>
              <span>Percentage</span>
              <strong>
                {result.percentage ?? 0}%
              </strong>
            </div>

            <div>
              <span>Status</span>
              <strong>
                {submission.status || 'Submitted'}
              </strong>
            </div>

          </div>
        )}


        {/* =====================================================
            QUESTIONS
        ===================================================== */}

        <div className="questions-section">

          <h2>Question-wise Review</h2>

          {review.length === 0 ? (

            <div className="no-review">
              No questions available for review.
            </div>

          ) : (

            review.map((item, index) => {

              const status =
                item.answer_status || 'unanswered';

              const isCorrect =
                status === 'correct';

              const isIncorrect =
                status === 'incorrect';

              const isUnanswered =
                status === 'unanswered';

              return (
                <div
                  className={`review-question-card ${
                    isCorrect
                      ? 'question-correct'
                      : isIncorrect
                      ? 'question-incorrect'
                      : 'question-unanswered'
                  }`}
                  key={item.question_id || index}
                >

                  {/* Question Header */}

                  <div className="question-header">

                    <h3>
                      Question {item.question_number || index + 1}
                    </h3>

                    <span
                      className={`answer-status ${
                        isCorrect
                          ? 'status-correct'
                          : isIncorrect
                          ? 'status-incorrect'
                          : 'status-unanswered'
                      }`}
                    >
                      {isCorrect
                        ? '✓ Correct'
                        : isIncorrect
                        ? '✗ Incorrect'
                        : '○ Unanswered'}
                    </span>

                  </div>


                  {/* Question Text */}

                  <div className="question-text">
                    {item.question_text}
                  </div>


                  {/* Student Answer */}

                  <div className="answer-box student-answer">

                    <div className="answer-label">
                      Your Answer
                    </div>

                    <div className="answer-value">
                      {item.student_answer ? (
                        item.student_answer
                      ) : (
                        <span className="not-answered">
                          Not Answered
                        </span>
                      )}
                    </div>

                  </div>


                  {/* Correct Answer */}

                  <div className="answer-box correct-answer">

                    <div className="answer-label">
                      Correct Answer
                    </div>

                    <div className="answer-value">
                      {item.correct_answer || 'Not Available'}
                    </div>

                  </div>

                </div>
              );
            })

          )}

        </div>


        {/* =====================================================
            BOTTOM BUTTON
        ===================================================== */}

        <div className="review-footer">

          <button
            type="button"
            className="back-button"
            onClick={() => navigate('/student/dashboard')}
          >
            Back to Dashboard
          </button>

        </div>

      </div>

    </div>
  );
}

export default StudentAnswerReview;