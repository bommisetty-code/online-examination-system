import React, {
  useCallback,
  useEffect,
  useState
} from "react";

import {
  useNavigate,
  useParams
} from "react-router-dom";

import { studentService } from "../services/studentService";

import "../styles/ExamInterface.css";

const ExamInterface = () => {

  // ==========================================
  // URL PARAMETER
  // ==========================================

  const { submissionId: routeSubmissionId } =
    useParams();

  const navigate = useNavigate();


  // ==========================================
  // STATE
  // ==========================================

  const [loading, setLoading] =
    useState(true);

  const [examData, setExamData] =
    useState(null);

  const [questions, setQuestions] =
    useState([]);

  const [submissionId, setSubmissionId] =
    useState(null);

  const [answers, setAnswers] =
    useState({});

  const [currentQuestion, setCurrentQuestion] =
    useState(0);

  const [timeRemaining, setTimeRemaining] =
    useState(0);

  const [submitting, setSubmitting] =
    useState(false);

  const [submissionResult, setSubmissionResult] =
    useState(null);

  const [showResult, setShowResult] =
    useState(false);

  const [showSubmitConfirm, setShowSubmitConfirm] =
    useState(false);

  const [error, setError] =
    useState("");


  // ==========================================
  // LOAD EXAM QUESTIONS
  // ==========================================

  const loadExam = useCallback(async () => {

    try {

      setLoading(true);

      setError("");


      // ----------------------------------------
      // Validate submission ID
      // ----------------------------------------

      if (!routeSubmissionId) {

        throw new Error(
          "Invalid submission ID"
        );

      }


      console.log(
        "Loading submission:",
        routeSubmissionId
      );


      // ----------------------------------------
      // IMPORTANT:
      // Do NOT call startExam() here.
      //
      // StudentDashboard already started
      // the exam and created submission.
      // ----------------------------------------

      const questionResponse =
        await studentService.getExamQuestions(
          routeSubmissionId
        );


      console.log(
        "Questions response:",
        questionResponse
      );


      // ----------------------------------------
      // Submission ID
      // ----------------------------------------

      const currentSubmissionId =
        questionResponse.submissionId ||
        routeSubmissionId;


      setSubmissionId(
        currentSubmissionId
      );


      // ----------------------------------------
      // Questions
      // ----------------------------------------

      const loadedQuestions =
        questionResponse.questions || [];


      setQuestions(
        loadedQuestions
      );


      // ----------------------------------------
      // Restore answers if available
      // ----------------------------------------

      if (questionResponse.answers) {

        setAnswers(
          questionResponse.answers
        );

      }


      // ----------------------------------------
      // Get Exam ID
      // ----------------------------------------

      const examId =
        questionResponse.examId;


      // ----------------------------------------
      // Load exam details
      // ----------------------------------------

      if (examId) {

        try {

          const examDetails =
            await studentService.getExamDetails(
              examId
            );

          setExamData(
            examDetails
          );

        } catch (detailsError) {

          console.warn(
            "Could not load exam details:",
            detailsError
          );

          // Questions can still be displayed
          // even if exam details fail.
          setExamData(null);

        }

      }


      // ----------------------------------------
      // TIMER
      // ----------------------------------------

      if (
        questionResponse.remainingSeconds !==
          null &&
        questionResponse.remainingSeconds !==
          undefined
      ) {

        setTimeRemaining(
          Math.max(
            0,
            Number(
              questionResponse.remainingSeconds
            )
          )
        );

      } else if (
        questionResponse.durationMinutes !==
          null &&
        questionResponse.durationMinutes !==
          undefined
      ) {

        setTimeRemaining(
          Math.max(
            0,
            Number(
              questionResponse.durationMinutes
            ) * 60
          )
        );

      }


      // ----------------------------------------
      // Reset current question
      // ----------------------------------------

      setCurrentQuestion(0);

    } catch (err) {

      console.error(
        "Failed to load exam:",
        err
      );


      const message =
        err?.response?.data?.message ||
        err?.message ||
        "Failed to load exam";


      setError(message);

    } finally {

      setLoading(false);

    }

  }, [routeSubmissionId]);


  // ==========================================
  // LOAD WHEN PAGE OPENS
  // ==========================================

  useEffect(() => {

    loadExam();

  }, [loadExam]);


  // ==========================================
  // TIMER
  // ==========================================

  useEffect(() => {

    if (
      loading ||
      showResult ||
      submitting
    ) {

      return;

    }


    if (timeRemaining <= 0) {

      return;

    }


    const timer =
      setInterval(() => {

        setTimeRemaining(
          (previous) => {

            if (previous <= 1) {

              clearInterval(timer);

              return 0;

            }

            return previous - 1;

          }
        );

      }, 1000);


    return () => {

      clearInterval(timer);

    };

  }, [
    loading,
    showResult,
    submitting,
    timeRemaining
  ]);


  // ==========================================
  // AUTO SUBMIT WHEN TIMER ENDS
  // ==========================================

  useEffect(() => {

    if (
      !loading &&
      !showResult &&
      !submitting &&
      timeRemaining === 0 &&
      submissionId &&
      questions.length > 0
    ) {

      handleAutoSubmit();

    }

  }, [
    timeRemaining,
    loading,
    showResult,
    submitting,
    submissionId,
    questions.length
  ]);


  // ==========================================
  // FORMAT TIMER
  // ==========================================

  const formatTime = (seconds) => {

    const safeSeconds =
      Math.max(
        0,
        Number(seconds) || 0
      );


    const hours =
      Math.floor(
        safeSeconds / 3600
      );


    const minutes =
      Math.floor(
        (safeSeconds % 3600) / 60
      );


    const secs =
      safeSeconds % 60;


    if (hours > 0) {

      return `${String(hours).padStart(
        2,
        "0"
      )}:${String(minutes).padStart(
        2,
        "0"
      )}:${String(secs).padStart(
        2,
        "0"
      )}`;

    }


    return `${String(minutes).padStart(
      2,
      "0"
    )}:${String(secs).padStart(
      2,
      "0"
    )}`;

  };


  // ==========================================
  // SELECT ANSWER
  // ==========================================

  const handleAnswerChange = async (
    questionId,
    optionId
  ) => {

    if (
      !submissionId ||
      submitting ||
      showResult
    ) {

      return;

    }


    try {

      // Update UI immediately

      setAnswers(
        (previous) => ({
          ...previous,
          [questionId]: optionId
        })
      );


      // Save answer in backend

      await studentService.submitAnswer(
        submissionId,
        questionId,
        optionId
      );

    } catch (err) {

      console.error(
        "Failed to save answer:",
        err
      );


      setError(
        err?.response?.data?.message ||
        "Failed to save answer"
      );

    }

  };


  // ==========================================
  // NEXT QUESTION
  // ==========================================

  const handleNext = () => {

    if (
      currentQuestion <
      questions.length - 1
    ) {

      setCurrentQuestion(
        (previous) =>
          previous + 1
      );

    }

  };


  // ==========================================
  // PREVIOUS QUESTION
  // ==========================================

  const handlePrevious = () => {

    if (
      currentQuestion > 0
    ) {

      setCurrentQuestion(
        (previous) =>
          previous - 1
      );

    }

  };


  // ==========================================
  // QUESTION NAVIGATION
  // ==========================================

  const handleQuestionNavigation = (
    index
  ) => {

    setCurrentQuestion(
      index
    );

  };


  // ==========================================
  // MANUAL SUBMIT
  // ==========================================

  const handleManualSubmit = async () => {

    if (
      !submissionId ||
      submitting ||
      showResult
    ) {

      return;

    }


    try {

      setSubmitting(true);

      setShowSubmitConfirm(false);

      setError("");


      const response =
        await studentService.submitExam(
          submissionId,
          false
        );


      console.log(
        "Submit response:",
        response
      );


      // Backend returns result

      if (response?.result) {

        setSubmissionResult(
          response.result
        );

      } else {

        setSubmissionResult(null);

      }


      // Show result popup

      setShowResult(true);

    } catch (err) {

      console.error(
        "Failed to submit exam:",
        err
      );


      setError(
        err?.response?.data?.message ||
        "Failed to submit exam"
      );


      setSubmitting(false);

    }

  };


  // ==========================================
  // AUTO SUBMIT
  // ==========================================

  const handleAutoSubmit = async () => {

    if (
      !submissionId ||
      submitting ||
      showResult
    ) {

      return;

    }


    try {

      setSubmitting(true);

      setError("");


      const response =
        await studentService.submitExam(
          submissionId,
          true
        );


      console.log(
        "Auto submit response:",
        response
      );


      if (response?.result) {

        setSubmissionResult(
          response.result
        );

      } else {

        setSubmissionResult(null);

      }


      setShowResult(true);

    } catch (err) {

      console.error(
        "Failed to auto submit exam:",
        err
      );


      setError(
        err?.response?.data?.message ||
        "Failed to submit exam automatically"
      );


      setSubmitting(false);

    }

  };


  // ==========================================
  // BACK BUTTON PROTECTION
  // ==========================================

  useEffect(() => {

    if (
      loading ||
      showResult ||
      !submissionId
    ) {

      return;

    }


    window.history.pushState(
      null,
      "",
      window.location.href
    );


    let backPressedOnce =
      false;


    const handlePopState = () => {

      if (!backPressedOnce) {

        backPressedOnce = true;


        alert(
          "⚠️ If you press Back again, your exam will be submitted automatically."
        );


        window.history.pushState(
          null,
          "",
          window.location.href
        );


        setTimeout(() => {

          backPressedOnce = false;

        }, 3000);


        return;

      }


      window.removeEventListener(
        "popstate",
        handlePopState
      );


      handleAutoSubmit();

    };


    window.addEventListener(
      "popstate",
      handlePopState
    );


    return () => {

      window.removeEventListener(
        "popstate",
        handlePopState
      );

    };

  }, [
    loading,
    showResult,
    submissionId
  ]);


  // ==========================================
  // LOADING SCREEN
  // ==========================================

  if (loading) {

    return (

      <div className="exam-page">

        <div className="exam-loading">

          <div className="loading-spinner"></div>

          <h2>
            Loading Exam...
          </h2>

          <p>
            Please wait while your exam
            is being loaded.
          </p>

        </div>

      </div>

    );

  }


  // ==========================================
  // ERROR SCREEN
  // ==========================================

  if (
    error &&
    !questions.length
  ) {

    return (

      <div className="exam-page">

        <div className="exam-error">

          <h2>
            Unable to Load Exam
          </h2>

          <p>
            {error}
          </p>

          <button
            className="confirm-button"
            onClick={() =>
              navigate(
                "/student/dashboard"
              )
            }
          >
            Back to Dashboard
          </button>

        </div>

      </div>

    );

  }


  // ==========================================
  // NO QUESTIONS
  // ==========================================

  if (!questions.length) {

    return (

      <div className="exam-page">

        <div className="exam-error">

          <h2>
            No Questions Available
          </h2>

          <p>
            This exam does not contain
            any questions.
          </p>

          <button
            className="confirm-button"
            onClick={() =>
              navigate(
                "/student/dashboard"
              )
            }
          >
            Back to Dashboard
          </button>

        </div>

      </div>

    );

  }


  // ==========================================
  // CURRENT QUESTION
  // ==========================================

  const question =
    questions[currentQuestion];


  const selectedOption =
    answers[question.id];


  const answeredCount =
    Object.keys(answers).length;


  const progressPercentage =
    questions.length > 0
      ? Math.round(
          ((currentQuestion + 1) /
            questions.length) *
            100
        )
      : 0;


  // ==========================================
  // MAIN UI
  // ==========================================

  return (
    <div className="exam-page">

      {/* ====================================== */}
      {/* HEADER */}
      {/* ====================================== */}

      <header className="exam-header">

        <div className="exam-header-left">

          <h1>
            {examData?.name ||
              "Online Examination"}
          </h1>

          <span>
            Question{" "}
            {currentQuestion + 1} of{" "}
            {questions.length}
          </span>

        </div>


        <div className="exam-timer">

          <span>
            ⏱️
          </span>

          <strong>
            {formatTime(
              timeRemaining
            )}
          </strong>

        </div>

      </header>


      {/* ====================================== */}
      {/* ERROR MESSAGE */}
      {/* ====================================== */}

      {error && (
        <div className="exam-alert">
          {error}
        </div>
      )}


      {/* ====================================== */}
      {/* PROGRESS */}
      {/* ====================================== */}

      <div className="exam-progress-container">

        <div className="exam-progress-info">

          <span>
            Progress
          </span>

          <span>
            {progressPercentage}%
          </span>

        </div>


        <div className="exam-progress-bar">

          <div
            className="exam-progress-fill"
            style={{
              width:
                `${progressPercentage}%`
            }}
          />

        </div>

      </div>


      {/* ====================================== */}
      {/* CONTENT */}
      {/* ====================================== */}

      <div className="exam-content">

        {/* ====================================== */}
        {/* QUESTION NAVIGATION */}
        {/* ====================================== */}

        <aside className="question-navigation">

          <h3>
            Questions
          </h3>

          <div className="question-grid">

            {questions.map(
              (item, index) => {

                const isAnswered =
                  answers[item.id] !== undefined;

                const isCurrent =
                  index === currentQuestion;

                return (
                  <button
                    key={item.id}
                    type="button"
                    className={`
                      question-number
                      ${isCurrent ? "current" : ""}
                      ${isAnswered ? "answered" : ""}
                    `}
                    onClick={() =>
                      handleQuestionNavigation(index)
                    }
                  >
                    {index + 1}
                  </button>
                );
              }
            )}

          </div>


          {/* ====================================== */}
          {/* QUESTION LEGEND */}
          {/* ====================================== */}

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


        {/* ====================================== */}
        {/* QUESTION AREA */}
        {/* ====================================== */}

        <main className="question-area">

          <div className="question-card">

            <div className="question-number-label">
              Question {currentQuestion + 1}
            </div>


            <h2 className="question-text">

              {question.question_text ||
                question.text ||
                question.question}

            </h2>


            {/* ====================================== */}
            {/* OPTIONS */}
            {/* ====================================== */}

            <div className="options-container">

              {(question.options || []).map(
                (option, index) => {

                  const optionId =
                    option.id;

                  const isSelected =
                    Number(selectedOption) ===
                    Number(optionId);

                  return (

                    <label
                      key={optionId}
                      className={`
                        option-item
                        ${isSelected ? "selected" : ""}
                      `}
                    >

                      <input
                        type="radio"
                        name={`question-${question.id}`}
                        value={optionId}
                        checked={isSelected}
                        onChange={() =>
                          handleAnswerChange(
                            question.id,
                            optionId
                          )
                        }
                      />


                      <span className="option-letter">

                        {String.fromCharCode(
                          65 + index
                        )}

                      </span>


                      <span className="option-text">

                        {option.option_text ||
                          option.text ||
                          option.value}

                      </span>

                    </label>

                  );
                }
              )}

            </div>


            {/* ====================================== */}
            {/* QUESTION ACTIONS */}
            {/* ====================================== */}

            <div className="question-actions">

              <button
                type="button"
                className="secondary-button"
                onClick={handlePrevious}
                disabled={
                  currentQuestion === 0 ||
                  submitting
                }
              >
                ← Previous
              </button>


              {currentQuestion <
              questions.length - 1 ? (

                <button
                  type="button"
                  className="primary-button"
                  onClick={handleNext}
                  disabled={submitting}
                >
                  Next →
                </button>

              ) : (

                <button
                  type="button"
                  className="submit-button"
                  onClick={() =>
                    setShowSubmitConfirm(true)
                  }
                  disabled={submitting}
                >
                  Submit Exam
                </button>

              )}

            </div>

          </div>


          {/* ====================================== */}
          {/* BOTTOM INFO */}
          {/* ====================================== */}

          <div className="exam-bottom-info">

            <span>

              Answered:{" "}

              <strong>
                {answeredCount}
              </strong>{" "}

              /{" "}
              {questions.length}

            </span>


            <button
              type="button"
              className="submit-link"
              onClick={() =>
                setShowSubmitConfirm(true)
              }
              disabled={submitting}
            >
              Submit Exam
            </button>

          </div>

        </main>

      </div>



      {/* ====================================== */}
      {/* SUBMIT CONFIRMATION MODAL */}
      {/* ====================================== */}

      {showSubmitConfirm && (
        <div className="modal-overlay">

          <div className="modal">

            <h2>
              Submit Exam?
            </h2>


            <p>
              Are you sure you want to
              submit the exam?
            </p>


            <div className="submit-warning">

              <strong>
                {questions.length - answeredCount}
              </strong>{" "}

              question(s) are unanswered.

            </div>


            <div className="modal-buttons">

              <button
                type="button"
                className="cancel-button"
                onClick={() =>
                  setShowSubmitConfirm(false)
                }
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
                  ? "Submitting..."
                  : "Yes, Submit"}
              </button>

            </div>

          </div>

        </div>
      )}


      {/* ====================================== */}
      {/* RESULT MODAL */}
      {/* ====================================== */}

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
                    {submissionResult.score} /{" "}
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
                        ? "passed"
                        : "failed"
                    }
                  >
                    {submissionResult.is_passed
                      ? "PASS"
                      : "FAIL"}
                  </strong>

                </div>

              </div>


              {/* ====================================== */}
              {/* RESULT BUTTONS */}
              {/* ====================================== */}

              <div className="modal-buttons">

                <button
                  type="button"
                  className="cancel-button"
                  onClick={() =>
                    navigate(
                      "/student/dashboard"
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

    </div>
  );
};

export default ExamInterface;