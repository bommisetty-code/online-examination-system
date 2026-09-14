import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import studentService from '../services/studentService';
import './ExamInterface.css';

const ExamInterface = () => {
  const { examId } = useParams();
  const navigate = useNavigate();

  const [examData, setExamData] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [submissionId, setSubmissionId] = useState(null);

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});

  const [timeRemaining, setTimeRemaining] = useState(0);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const [showSubmitModal, setShowSubmitModal] = useState(false);

  // Final result
  const [submissionResult, setSubmissionResult] = useState(null);
  const [showResult, setShowResult] = useState(false);

  const currentQuestion = questions[currentQuestionIndex];

  // =========================================================
  // LOAD EXAM
  // =========================================================

  useEffect(() => {
    const loadExam = async () => {
      try {
        setLoading(true);
        setError('');

        const response = await studentService.startExam(examId);

        setExamData(response.exam || response);
        setQuestions(response.questions || []);
        setSubmissionId(response.submission_id);

        if (response.answers) {
          setAnswers(response.answers);
        }

        if (response.expiry_time) {
          const expiry = new Date(
            response.expiry_time
          ).getTime();

          const now = Date.now();

          setTimeRemaining(
            Math.max(
              0,
              Math.floor((expiry - now) / 1000)
            )
          );
        }
      } catch (err) {
        console.error('Failed to load exam:', err);

        setError(
          err?.response?.data?.message ||
          'Failed to load exam'
        );
      } finally {
        setLoading(false);
      }
    };

    loadExam();
  }, [examId]);

  // =========================================================
  // SAVE ANSWER
  // =========================================================

  const handleAnswerSelect = async (
    questionId,
    optionId
  ) => {
    try {
      setAnswers(prev => ({
        ...prev,
        [questionId]: optionId
      }));

      await studentService.submitAnswer(
        submissionId,
        questionId,
        optionId
      );
    } catch (err) {
      console.error(
        'Failed to save answer:',
        err
      );

      setError(
        err?.response?.data?.message ||
        'Failed to save answer'
      );
    }
  };

  // =========================================================
  // SUBMIT EXAM
  // =========================================================

  const submitExam = useCallback(async () => {
    if (!submissionId || submitting) {
      return null;
    }

    try {
      setSubmitting(true);
      setError('');

      const response =
        await studentService.submitExam(
          submissionId
        );

      return response;
    } catch (err) {
      console.error(
        'Failed to submit exam:',
        err
      );

      setError(
        err?.response?.data?.message ||
        'Failed to submit exam'
      );

      return null;
    } finally {
      setSubmitting(false);
    }
  }, [submissionId, submitting]);

  // =========================================================
  // MANUAL SUBMIT
  // =========================================================

  const handleManualSubmit = async () => {
    setShowSubmitModal(false);

    const response = await submitExam();

    if (response?.result) {
      setSubmissionResult(response.result);
      setShowResult(true);
    }
  };

  // =========================================================
  // AUTO SUBMIT
  // =========================================================

  const handleAutoSubmit = useCallback(async () => {
    if (showResult || submitting) {
      return;
    }

    const response = await submitExam();

    if (response?.result) {
      setSubmissionResult(response.result);
      setShowResult(true);
    }
  }, [
    showResult,
    submitting,
    submitExam
  ]);

  // =========================================================
  // TIMER
  // =========================================================

  useEffect(() => {
    // IMPORTANT:
    // After result popup appears, stop timer completely.
    if (loading || showResult) {
      return;
    }

    if (timeRemaining <= 0) {
      handleAutoSubmit();
      return;
    }

    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }

        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [
    loading,
    timeRemaining,
    showResult,
    handleAutoSubmit
  ]);

  // =========================================================
  // FORMAT TIMER
  // =========================================================

  const formatTime = seconds => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;

    return `${String(mins).padStart(2, '0')}:${String(
      secs
    ).padStart(2, '0')}`;
  };

  // =========================================================
  // QUESTION NAVIGATION
  // =========================================================

  const goToQuestion = index => {
    if (
      index >= 0 &&
      index < questions.length
    ) {
      setCurrentQuestionIndex(index);
    }
  };

  const handleNext = () => {
    if (
      currentQuestionIndex <
      questions.length - 1
    ) {
      setCurrentQuestionIndex(
        prev => prev + 1
      );
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(
        prev => prev - 1
      );
    }
  };

  // =========================================================
  // LOADING
  // =========================================================

  if (loading) {
    return (
      <div className="exam-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>

          <p>Loading exam...</p>
        </div>
      </div>
    );
  }

  // =========================================================
  // ERROR
  // =========================================================

  if (error && !examData) {
    return (
      <div className="exam-page">
        <div className="error-container">

          <h2>Unable to Load Exam</h2>

          <p>{error}</p>

          <button
            className="confirm-button"
            onClick={() =>
              navigate('/student/dashboard')
            }
          >
            Back to Dashboard
          </button>

        </div>
      </div>
    );
  }

  // =========================================================
  // NO QUESTIONS
  // =========================================================

  if (!currentQuestion) {
    return (
      <div className="exam-page">

        <div className="error-container">

          <h2>No Questions Found</h2>

          <button
            className="confirm-button"
            onClick={() =>
              navigate('/student/dashboard')
            }
          >
            Back to Dashboard
          </button>

        </div>

      </div>
    );
  }

  // =========================================================
  // MAIN UI
  // =========================================================

  return (
    <div className="exam-page">

      {/* HEADER */}
      <header className="exam-header">

        <div>
          <h1>
            {examData?.name ||
              'Online Examination'}
          </h1>

          {examData?.description && (
            <p>
              {examData.description}
            </p>
          )}
        </div>

        <div className="timer-box">

          <span>
            Time Remaining
          </span>

          <strong
            className={
              timeRemaining <= 60
                ? 'timer-danger'
                : ''
            }
          >
            {formatTime(timeRemaining)}
          </strong>

        </div>

      </header>

      {/* MAIN CONTENT */}
      <main className="exam-content">

        {/* QUESTIONS */}
        <section className="questions-section">

          <div className="question-header">

            <span>
              Question{' '}
              {currentQuestionIndex + 1}{' '}
              of {questions.length}
            </span>

            <span>
              {Object.keys(answers).length}{' '}
              answered
            </span>

          </div>

          {/* QUESTION */}
          <div className="question-box">

            <h2 className="question-text">
              {currentQuestion.question_text}
            </h2>

            <div className="options-list">

              {currentQuestion.options?.map(
                (option, index) => {

                  const optionId =
                    option.id;

                  const selected =
                    answers[
                      currentQuestion.id
                    ] === optionId;

                  return (
                    <button
                      key={optionId}
                      type="button"
                      className={`option-button ${
                        selected
                          ? 'selected'
                          : ''
                      }`}
                      onClick={() =>
                        handleAnswerSelect(
                          currentQuestion.id,
                          optionId
                        )
                      }
                    >

                      <span className="option-label">
                        {String.fromCharCode(
                          65 + index
                        )}
                      </span>

                      <span className="option-text">
                        {option.option_text}
                      </span>

                    </button>
                  );
                }
              )}

            </div>

          </div>

          {/* NAVIGATION */}
          <div className="navigation-buttons">

            <button
              type="button"
              className="secondary-button"
              onClick={handlePrevious}
              disabled={
                currentQuestionIndex === 0
              }
            >
              ← Previous
            </button>

            {currentQuestionIndex <
            questions.length - 1 ? (

              <button
                type="button"
                className="confirm-button"
                onClick={handleNext}
              >
                Next →
              </button>

            ) : (

              <button
                type="button"
                className="submit-button"
                onClick={() =>
                  setShowSubmitModal(true)
                }
                disabled={
                  submitting ||
                  showResult
                }
              >
                {submitting
                  ? 'Submitting...'
                  : 'Submit Exam'}
              </button>

            )}

          </div>

        </section>

        {/* QUESTION SIDEBAR */}
        <aside className="question-sidebar">

          <h3>Questions</h3>

          <div className="question-grid">

            {questions.map(
              (question, index) => {

                const answered =
                  answers[
                    question.id
                  ] !== undefined &&
                  answers[
                    question.id
                  ] !== null;

                return (
                  <button
                    key={question.id}
                    type="button"
                    className={`question-number ${
                      index ===
                      currentQuestionIndex
                        ? 'current'
                        : ''
                    } ${
                      answered
                        ? 'answered'
                        : ''
                    }`}
                    onClick={() =>
                      goToQuestion(index)
                    }
                  >
                    {index + 1}
                  </button>
                );
              }
            )}

          </div>

          <div className="question-legend">

            <div>
              <span className="legend-box current"></span>
              Current
            </div>

            <div>
              <span className="legend-box answered"></span>
              Answered
            </div>

            <div>
              <span className="legend-box"></span>
              Not Answered
            </div>

          </div>

        </aside>

      </main>

      {/* =====================================================
          SUBMIT CONFIRMATION MODAL
          ===================================================== */}

      {showSubmitModal && (

        <div className="modal-overlay">

          <div className="modal">

            <h2>
              Submit Exam?
            </h2>

            <p>
              Are you sure you want to
              submit the exam?
            </p>

            <p>
              You have answered{' '}
              <strong>
                {Object.keys(answers).length}
              </strong>{' '}
              out of{' '}
              <strong>
                {questions.length}
              </strong>{' '}
              questions.
            </p>

            <div className="modal-buttons">

              <button
                type="button"
                className="cancel-button"
                onClick={() =>
                  setShowSubmitModal(false)
                }
                disabled={submitting}
              >
                Cancel
              </button>

              <button
                type="button"
                className="confirm-button"
                onClick={handleManualSubmit}
                disabled={submitting}
              >
                {submitting
                  ? 'Submitting...'
                  : 'Yes, Submit'}
              </button>

            </div>

          </div>

        </div>

      )}

      {/* =====================================================
          RESULT MODAL
          ===================================================== */}

      {showResult &&
        submissionResult && (

          <div className="modal-overlay">

            <div className="modal result-modal">

              <h2>
                🎉 Exam Submitted Successfully
              </h2>

              <div className="result-summary">

                <div className="result-item">

                  <span>
                    Score
                  </span>

                  <strong>
                    {submissionResult.score}{' '}
                    /{' '}
                    {submissionResult.total_marks}
                  </strong>

                </div>

                <div className="result-item">

                  <span>
                    Percentage
                  </span>

                  <strong>
                    {submissionResult.percentage}%
                  </strong>

                </div>

                <div className="result-item">

                  <span>
                    Correct
                  </span>

                  <strong>
                    {submissionResult.correct_answers}
                  </strong>

                </div>

                <div className="result-item">

                  <span>
                    Incorrect
                  </span>

                  <strong>
                    {submissionResult.incorrect_answers}
                  </strong>

                </div>

                <div className="result-item">

                  <span>
                    Unanswered
                  </span>

                  <strong>
                    {submissionResult.unanswered}
                  </strong>

                </div>

                <div className="result-item">

                  <span>
                    Status
                  </span>

                  <strong
                    className={
                      submissionResult.is_passed
                        ? 'passed'
                        : 'failed'
                    }
                  >
                    {submissionResult.is_passed
                      ? 'PASS'
                      : 'FAIL'}
                  </strong>

                </div>

              </div>

              <div className="modal-buttons">

                <button
                  type="button"
                  className="cancel-button"
                  onClick={() =>
                    navigate(
                      '/student/dashboard'
                    )
                  }
                >
                  Back to Dashboard
                </button>

                <button
                  type="button"
                  className="confirm-button"
                  onClick={() =>
                    navigate(
                      `/student/result-review/${submissionId}`
                    )
                  }
                >
                  View Detailed Review
                </button>

              </div>

            </div>

          </div>

        )}

      {/* ERROR MESSAGE */}
      {error && (

        <div className="error-message">
          {error}
        </div>

      )}

    </div>
  );
};

export default ExamInterface;