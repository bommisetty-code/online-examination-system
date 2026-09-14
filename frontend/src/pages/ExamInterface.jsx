import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import studentService from '../services/studentService';
import { useTimer } from '../hooks/useTimer';
import { useBackButtonProtection } from '../hooks/useBackButtonProtection';
import BackButtonWarning from '../components/BackButtonWarning';
import '../styles/ExamInterface.css';

export const ExamInterface = () => {
  const { submissionId } = useParams();
  const navigate = useNavigate();

  const [exam, setExam] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showBackWarning, setShowBackWarning] = useState(false);
  const [showExitWarning, setShowExitWarning] = useState(false);
  const [durationMinutes, setDurationMinutes] = useState(null);

  // ============================================================
  // RESULT STATE
  // ============================================================

  const [submissionResult, setSubmissionResult] = useState(null);
  const [showResult, setShowResult] = useState(false);

  const { showWarningNeeded, resetWarningFlag } =
    useBackButtonProtection(true);

  // ============================================================
  // TIMER
  // Backend remaining time is the source of truth
  // ============================================================

  const {
    remainingTime,
    formattedTime,
    isExpired
  } = useTimer(
    durationMinutes,
    async () => {
      try {
        setIsSubmitting(true);
        setError('');

        const response =
          await studentService.submitExam(
            submissionId,
            true
          );

        console.log(
          'Auto submit result:',
          response
        );

        setSubmissionResult(
          response?.result || null
        );

        setShowResult(true);

      } catch (err) {
        console.error(
          'Auto submit failed:',
          err
        );

        setError(
          err.response?.data?.message ||
          'Failed to submit exam automatically'
        );

      } finally {
        setIsSubmitting(false);
      }
    }
  );

  // ============================================================
  // LOAD EXAM
  // ============================================================

  useEffect(() => {
    loadExamData();
  }, [submissionId]);

  // ============================================================
  // BACKEND TIMER VALIDATION
  // ============================================================

  useEffect(() => {
    const validateInterval = setInterval(
      async () => {
        try {
          const status =
            await studentService.getSubmissionStatus(
              submissionId
            );

          // Backend says time expired
          if (status.is_expired) {
            if (!isSubmitting) {
              await handleTimeExpired();
            }

            return;
          }

          // Backend says exam is no longer active
          if (!status.is_active) {
            navigate(
              `/student/results/${submissionId}`
            );

            return;
          }

        } catch (err) {
          console.error(
            'Status check failed:',
            err
          );
        }
      },
      5000
    );

    return () =>
      clearInterval(validateInterval);
  }, [
    submissionId,
    isSubmitting,
    navigate
  ]);

  // ============================================================
  // BROWSER BACK BUTTON PROTECTION
  // ============================================================

  useEffect(() => {
    const handlePopState = (e) => {
      e.preventDefault();

      window.history.pushState(
        null,
        '',
        window.location.href
      );

      if (showWarningNeeded()) {
        setShowBackWarning(true);
      } else {
        handleAutoSubmit();
      }
    };

    window.history.pushState(
      null,
      '',
      window.location.href
    );

    window.addEventListener(
      'popstate',
      handlePopState
    );

    return () => {
      window.removeEventListener(
        'popstate',
        handlePopState
      );
    };
  }, [showWarningNeeded]);

  // ============================================================
  // LOAD QUESTIONS + BACKEND REMAINING TIME
  // ============================================================

  const loadExamData = async () => {
    try {
      setIsLoading(true);
      setError('');

      const examData =
        await studentService.getExamQuestions(
          submissionId
        );

      const questionsData =
        examData.questions || [];

      if (questionsData.length === 0) {
        setError(
          'No questions found for this exam'
        );
        return;
      }

      setQuestions(questionsData);

      // --------------------------------------------------------
      // Get exact remaining time from backend
      // --------------------------------------------------------

      let remainingSeconds =
        examData.remainingSeconds;

      // If questions API doesn't return remaining time,
      // get it from backend status API.
      if (
        typeof remainingSeconds !== 'number'
      ) {
        const status =
          await studentService.getSubmissionStatus(
            submissionId
          );

        remainingSeconds =
          Number(status.remaining_seconds);
      }

      if (
        Number.isFinite(remainingSeconds) &&
        remainingSeconds >= 0
      ) {
        // useTimer expects minutes
        setDurationMinutes(
          remainingSeconds / 60
        );
      } else {
        setError(
          'Unable to get exam remaining time from server'
        );
        return;
      }

      // --------------------------------------------------------
      // Initialize existing answers
      // --------------------------------------------------------

      const initialAnswers = {};

      questionsData.forEach((q) => {
        initialAnswers[q.id] =
          q.student_answer || null;
      });

      setAnswers(initialAnswers);

    } catch (err) {
      console.error(
        'Failed to load exam:',
        err
      );

      setError(
        err.response?.data?.message ||
        'Failed to load exam'
      );

    } finally {
      setIsLoading(false);
    }
  };

  // ============================================================
  // CURRENT QUESTION
  // ============================================================

  const currentQuestion =
    questions[currentQuestionIndex];

  const answeredCount =
    Object.values(answers).filter(
      (a) => a !== null
    ).length;

  // ============================================================
  // ANSWER SELECT
  // ============================================================

  const handleAnswerSelect = async (
    optionId
  ) => {
    try {
      setAnswers((prev) => ({
        ...prev,
        [currentQuestion.id]: optionId,
      }));

      await studentService.submitAnswer(
        submissionId,
        currentQuestion.id,
        optionId
      );

    } catch (err) {
      setError(
        err.response?.data?.message ||
        'Failed to save answer'
      );

      console.error(err);
    }
  };

  // ============================================================
  // NAVIGATION
  // ============================================================

  const handleNextQuestion = () => {
    if (
      currentQuestionIndex <
      questions.length - 1
    ) {
      setCurrentQuestionIndex(
        currentQuestionIndex + 1
      );
    }
  };

  const handlePreviousQuestion = () => {
    if (
      currentQuestionIndex > 0
    ) {
      setCurrentQuestionIndex(
        currentQuestionIndex - 1
      );
    }
  };

  // ============================================================
  // TIME EXPIRED
  // ============================================================

  const handleTimeExpired = async () => {
    await handleAutoSubmit();
  };

  // ============================================================
  // AUTO SUBMIT
  // ============================================================

  const handleAutoSubmit = async () => {
    if (isSubmitting) {
      return;
    }

    try {
      setIsSubmitting(true);
      setError('');

      const response =
        await studentService.submitExam(
          submissionId,
          true
        );

      console.log(
        'Auto submit result:',
        response
      );

      // Backend returns result
      setSubmissionResult(
        response?.result || null
      );

      // Show result popup immediately
      setShowResult(true);

    } catch (err) {
      console.error(
        'Auto submit failed:',
        err
      );

      setError(
        err.response?.data?.message ||
        'Failed to submit exam'
      );

    } finally {
      setIsSubmitting(false);
    }
  };

  // ============================================================
  // MANUAL SUBMIT
  // ============================================================

  const handleManualSubmit = async () => {
    setShowExitWarning(false);

    try {
      setIsSubmitting(true);
      setError('');

      const response =
        await studentService.submitExam(
          submissionId,
          false
        );

      console.log(
        'Manual submit result:',
        response
      );

      // Backend returns result
      setSubmissionResult(
        response?.result || null
      );

      // Show result popup immediately
      setShowResult(true);

    } catch (err) {
      console.error(
        'Exam submission failed:',
        err
      );

      setError(
        err.response?.data?.message ||
        'Failed to submit exam'
      );

    } finally {
      setIsSubmitting(false);
    }
  };

  // ============================================================
  // BACK WARNING
  // ============================================================

  const handleBackWarningResponse = (
    confirmed
  ) => {
    setShowBackWarning(false);

    if (confirmed) {
      handleAutoSubmit();
    } else {
      resetWarningFlag();
    }
  };

  // ============================================================
  // LOADING
  // ============================================================

  if (isLoading) {
    return (
      <div className="loading">
        Loading exam...
      </div>
    );
  }

  // ============================================================
  // ERROR
  // ============================================================

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

  if (!currentQuestion) {
    return (
      <div className="loading">
        Loading questions...
      </div>
    );
  }

  // ============================================================
  // UI
  // ============================================================

  return (
    <div className="exam-interface-container">

      {/* ======================================================
          BACK BUTTON WARNING
      ====================================================== */}

      {showBackWarning && (
        <BackButtonWarning
          onResponse={
            handleBackWarningResponse
          }
        />
      )}

      {/* ======================================================
          RESULT MODAL
      ====================================================== */}

      {showResult && submissionResult && (
        <div className="modal-overlay">

          <div className="modal result-modal">

            <h2>
              🎉 Exam Submitted Successfully
            </h2>

            <div className="result-summary">

              {/* Score */}
              <div className="result-item">
                <span>
                  Score
                </span>

                <strong>
                  {submissionResult.score}
                  {' / '}
                  {submissionResult.total_marks}
                </strong>
              </div>

              {/* Percentage */}
              <div className="result-item">
                <span>
                  Percentage
                </span>

                <strong>
                  {submissionResult.percentage}%
                </strong>
              </div>

              {/* Correct */}
              <div className="result-item">
                <span>
                  Correct
                </span>

                <strong>
                  {submissionResult.correct_answers}
                </strong>
              </div>

              {/* Incorrect */}
              <div className="result-item">
                <span>
                  Incorrect
                </span>

                <strong>
                  {submissionResult.incorrect_answers}
                </strong>
              </div>

              {/* Unanswered */}
              <div className="result-item">
                <span>
                  Unanswered
                </span>

                <strong>
                  {submissionResult.unanswered}
                </strong>
              </div>

              {/* Status */}
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

            {/* Buttons */}
            <div className="modal-buttons">

              <button
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

      {/* ======================================================
          HEADER
      ====================================================== */}

      <header className="exam-header">

        <div className="header-left">

          <h2>
            Exam in Progress
          </h2>

        </div>

        <div className="header-center">

          <div
            className={`timer ${
              isExpired
                ? 'expired'
                : remainingTime < 300
                  ? 'warning'
                  : ''
            }`}
          >
            ⏱️ {formattedTime}
          </div>

        </div>

        <div className="header-right">

          <button
            onClick={() =>
              setShowExitWarning(true)
            }
            className="submit-button"
            disabled={isSubmitting}
          >
            Submit Exam
          </button>

        </div>

      </header>

      {/* ======================================================
          SUBMIT CONFIRMATION MODAL
      ====================================================== */}

      {showExitWarning && (
        <div className="modal-overlay">

          <div className="modal">

            <h3>
              Submit Exam?
            </h3>

            <p>
              You have answered{' '}
              <strong>
                {answeredCount}
              </strong>{' '}
              out of{' '}
              <strong>
                {questions.length}
              </strong>{' '}
              questions.
            </p>

            <p>
              Are you sure you want to
              submit? You cannot change
              your answers after submission.
            </p>

            <div className="modal-buttons">

              <button
                onClick={() =>
                  setShowExitWarning(false)
                }
                className="cancel-button"
              >
                Cancel
              </button>

              <button
                onClick={
                  handleManualSubmit
                }
                className="confirm-button"
                disabled={isSubmitting}
              >
                {isSubmitting
                  ? 'Submitting...'
                  : 'Submit'}
              </button>

            </div>

          </div>

        </div>
      )}

      {/* ======================================================
          MAIN CONTENT
      ====================================================== */}

      <main className="exam-main">

        <div className="exam-container">

          {/* ==================================================
              SIDEBAR
          ================================================== */}

          <aside className="exam-sidebar">

            <div className="progress-section">

              <h3>
                Progress
              </h3>

              <div className="progress-bar">

                <div
                  className="progress-fill"
                  style={{
                    width: `${
                      (answeredCount /
                        questions.length) *
                      100
                    }%`
                  }}
                />

              </div>

              <p>
                {answeredCount} of{' '}
                {questions.length}{' '}
                answered
              </p>

            </div>

            <div className="questions-nav">

              <h3>
                Questions
              </h3>

              <div className="question-buttons">

                {questions.map(
                  (q, idx) => (

                    <button
                      key={q.id}
                      onClick={() =>
                        setCurrentQuestionIndex(
                          idx
                        )
                      }
                      className={`question-nav-btn ${
                        idx ===
                        currentQuestionIndex
                          ? 'active'
                          : ''
                      } ${
                        answers[q.id] !== null
                          ? 'answered'
                          : 'unanswered'
                      }`}
                      title={`Question ${
                        idx + 1
                      }`}
                    >
                      {idx + 1}
                    </button>

                  )
                )}

              </div>

            </div>

          </aside>

          {/* ==================================================
              QUESTION
          ================================================== */}

          <section className="exam-content">

            <div className="question-section">

              <div className="question-header">

                <h3>
                  Question{' '}
                  {currentQuestionIndex + 1}{' '}
                  of {questions.length}
                </h3>

              </div>

              <div className="question-box">

                <p className="question-text">
                  {
                    currentQuestion.question_text
                  }
                </p>

                <div className="options-list">

                  {currentQuestion.options.map(
                    (option) => (

                      <div
                        key={option.id}
                        className="option-wrapper"
                      >

                        <label className="option-label">

                          <input
                            type="radio"
                            name={`question-${currentQuestion.id}`}
                            value={option.id}
                            checked={
                              answers[
                                currentQuestion.id
                              ] === option.id
                            }
                            onChange={() =>
                              handleAnswerSelect(
                                option.id
                              )
                            }
                            disabled={
                              isSubmitting
                            }
                          />

                          <span className="option-text">
                            {
                              option.option_text
                            }
                          </span>

                        </label>

                      </div>

                    )
                  )}

                </div>

              </div>

              {/* ==================================================
                  QUESTION NAVIGATION
              ================================================== */}

              <div className="navigation-buttons">

                <button
                  onClick={
                    handlePreviousQuestion
                  }
                  disabled={
                    currentQuestionIndex === 0
                  }
                  className="nav-button prev-button"
                >
                  ← Previous
                </button>

                <span className="question-status">

                  {answers[
                    currentQuestion.id
                  ] !== null
                    ? '✓ Answered'
                    : 'Not answered'}

                </span>

                <button
                  onClick={
                    handleNextQuestion
                  }
                  disabled={
                    currentQuestionIndex ===
                    questions.length - 1
                  }
                  className="nav-button next-button"
                >
                  Next →
                </button>

              </div>

            </div>

          </section>

        </div>

      </main>

      {/* ======================================================
          ERROR MESSAGE
      ====================================================== */}

      {error && (
        <div className="error-message-bar">

          {error}

          <button
            onClick={() =>
              setError('')
            }
            className="close-button"
          >
            ×
          </button>

        </div>
      )}

    </div>
  );
};

export default ExamInterface;