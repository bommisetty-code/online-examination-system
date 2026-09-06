import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import studentService from '../services/studentService';
import { formatters } from '../utils/helpers';
import '../styles/ResultsPage.css';

export const ResultsPage = () => {
  const { submissionId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const autoSubmitted =
    location.state?.autoSubmitted;

  useEffect(() => {
    loadResult();
  }, [submissionId]);

  const loadResult = async () => {
    try {
      setIsLoading(true);

      const resultData =
        await studentService.getResult(
          submissionId
        );

      setResult(resultData);

    } catch (err) {
      setError('Failed to load result');
      console.error(err);

    } finally {
      setIsLoading(false);
    }
  };

  // ============================================================
  // UTC -> INDIA STANDARD TIME
  // ============================================================

  const formatSubmittedDate = (dateString) => {
    if (!dateString) {
      return '-';
    }

    try {
      let value = String(dateString).trim();

      // Backend sends UTC without timezone information.
      // Explicitly mark it as UTC.
      if (
        !value.endsWith('Z') &&
        !/[+-]\d{2}:\d{2}$/.test(value)
      ) {
        value = `${value}Z`;
      }

      const date = new Date(value);

      if (Number.isNaN(date.getTime())) {
        return '-';
      }

      return date.toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata',
        day: 'numeric',
        month: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      });

    } catch (error) {
      console.error(
        'Date formatting error:',
        error
      );

      return '-';
    }
  };

  if (isLoading) {
    return (
      <div className="loading">
        Loading results...
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">

        <div className="error-box">

          <h2>Error</h2>

          <p>{error}</p>

          <button
            onClick={() =>
              navigate('/student/dashboard')
            }
            className="back-button"
          >
            Return to Dashboard
          </button>

        </div>

      </div>
    );
  }

  if (!result) {
    return (
      <div className="loading">
        No result found
      </div>
    );
  }

  const gradeColor =
    formatters.getGradeColor(
      result.percentage
    );

  const resultStatus =
    result.is_passed
      ? 'PASSED'
      : 'FAILED';

  const resultStatusClass =
    result.is_passed
      ? 'passed'
      : 'failed';

  return (
    <div className="results-container">

      {/* Header */}
      <header className="results-header">

        <button
          onClick={() =>
            navigate('/student/dashboard')
          }
          className="back-button"
        >
          ← Return to Dashboard
        </button>

        <h1>
          Exam Results
        </h1>

      </header>

      {/* Auto-submit notification */}
      {autoSubmitted && (
        <div className="auto-submit-notification">
          ⏰ Your exam was automatically submitted
          because time expired.
        </div>
      )}

      {/* Main Content */}
      <main className="results-main">

        {/* Score Card */}
        <div className="score-card">

          <div className="score-display">

            <div
              className="score-circle"
              style={{
                borderColor: gradeColor
              }}
            >

              <div
                className="score-number"
                style={{
                  color: gradeColor
                }}
              >
                {Number(
                  result.percentage || 0
                ).toFixed(2)}%
              </div>

              <div className="score-label">
                Score
              </div>

            </div>

          </div>

          <div
            className={`result-status ${resultStatusClass}`}
          >
            <h2>
              {resultStatus}
            </h2>
          </div>

          <div className="result-summary">

            <div className="summary-row">
              <span className="label">
                Questions:
              </span>

              <span className="value">
                {result.total_questions}
              </span>
            </div>

            <div className="summary-row">
              <span className="label">
                Correct:
              </span>

              <span className="value correct">
                {result.correct_answers}
              </span>
            </div>

            <div className="summary-row">
              <span className="label">
                Incorrect:
              </span>

              <span className="value incorrect">
                {result.incorrect_answers}
              </span>
            </div>

            <div className="summary-row">
              <span className="label">
                Unanswered:
              </span>

              <span className="value unanswered">
                {result.unanswered}
              </span>
            </div>

            <div className="summary-row">
              <span className="label">
                Marks:
              </span>

              <span className="value">
                {result.score}/
                {result.total_marks}
              </span>
            </div>

            {/* IST Submitted Time */}
            <div className="summary-row">

              <span className="label">
                Submitted:
              </span>

              <span className="value">
                {formatSubmittedDate(
                  result.submitted_at
                )}
              </span>

            </div>

          </div>

        </div>

        {/* Performance Breakdown */}
        <div className="performance-section">

          <h3>
            Performance Breakdown
          </h3>

          <div className="performance-bar">

            <div
              className="bar-segment correct"
              style={{
                width: `${
                  (
                    result.correct_answers /
                    result.total_questions
                  ) * 100
                }%`
              }}
            >
              <span className="bar-label">
                {result.correct_answers} Correct
              </span>
            </div>

            <div
              className="bar-segment incorrect"
              style={{
                width: `${
                  (
                    result.incorrect_answers /
                    result.total_questions
                  ) * 100
                }%`
              }}
            >
              <span className="bar-label">
                {result.incorrect_answers} Incorrect
              </span>
            </div>

            <div
              className="bar-segment unanswered"
              style={{
                width: `${
                  (
                    result.unanswered /
                    result.total_questions
                  ) * 100
                }%`
              }}
            >
              <span className="bar-label">
                {result.unanswered} Unanswered
              </span>
            </div>

          </div>

          <div className="performance-stats">

            <div className="stat">

              <div
                className="stat-value"
                style={{
                  color: '#28a745'
                }}
              >
                {Math.round(
                  (
                    result.correct_answers /
                    result.total_questions
                  ) * 100
                )}%
              </div>

              <div className="stat-label">
                Correct Answers
              </div>

            </div>

            <div className="stat">

              <div
                className="stat-value"
                style={{
                  color: '#dc3545'
                }}
              >
                {Math.round(
                  (
                    result.incorrect_answers /
                    result.total_questions
                  ) * 100
                )}%
              </div>

              <div className="stat-label">
                Incorrect Answers
              </div>

            </div>

            <div className="stat">

              <div
                className="stat-value"
                style={{
                  color: '#6c757d'
                }}
              >
                {Math.round(
                  (
                    result.unanswered /
                    result.total_questions
                  ) * 100
                )}%
              </div>

              <div className="stat-label">
                Unanswered
              </div>

            </div>

          </div>

        </div>

        {/* Result Message */}
        <div className="result-message">

          {result.is_passed ? (
            <>
              <h3>
                🎉 Congratulations!
              </h3>

              <p>
                You have successfully passed
                the exam with a score of{' '}
                {Number(
                  result.percentage || 0
                ).toFixed(2)}%
              </p>
            </>
          ) : (
            <>
              <h3>
                Result
              </h3>

              <p>
                Your score is{' '}
                {Number(
                  result.percentage || 0
                ).toFixed(2)}%.
                You need at least 50% to pass.
                Better luck next time!
              </p>
            </>
          )}

        </div>

        {/* Actions */}
        <div className="result-actions">

          <button
            onClick={() =>
              navigate('/student/dashboard')
            }
            className="primary-button"
          >
            Return to Dashboard
          </button>

        </div>

      </main>

    </div>
  );
};

export default ResultsPage;