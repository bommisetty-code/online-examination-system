import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import adminService from '../services/adminService';
import '../styles/AdminResultsDashboard.css';

export const ResultsDetailView = () => {
  const { examId } = useParams();
  const navigate = useNavigate();
  const { logout } = useAuth();

  const [exam, setExam] = useState(null);
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedStudentId, setExpandedStudentId] = useState(null);
  const [selectedStudentResult, setSelectedStudentResult] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    loadData();
  }, [examId]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      setError('');

      const [examData, resultsData] = await Promise.all([
        adminService.getExam(examId),
        adminService.getExamResults(examId),
      ]);

      setExam(examData);
      setResults(resultsData);
    } catch (err) {
      setError('Failed to load results');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewDetails = async (studentId) => {
    if (expandedStudentId === studentId) {
      setExpandedStudentId(null);
      setSelectedStudentResult(null);
      return;
    }

    try {
      setLoadingDetail(true);

      const detailData =
        await adminService.getStudentResult(
          examId,
          studentId
        );

      setExpandedStudentId(studentId);
      setSelectedStudentResult(detailData);
    } catch (err) {
      setError('Failed to load student result details');
      console.error(err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleBackToResults = () => {
    navigate('/admin/results');
  };

  // ============================================================
  // UTC -> INDIA STANDARD TIME
  // ============================================================

  const formatDate = (dateString) => {
    if (!dateString) {
      return '-';
    }

    try {
      let value = String(dateString).trim();

      // Flask/MySQL may return UTC without Z.
      // Example:
      // 2026-09-06T05:26:00
      //
      // Treat it explicitly as UTC.
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
      console.error('Date formatting error:', error);
      return '-';
    }
  };

  const calculateStats = () => {
    if (results.length === 0) {
      return {
        avgScore: 0,
        passRate: 0,
        totalAttempts: 0
      };
    }

    const totalAttempts = results.length;

    const passCount = results.filter(
      r => r.result.is_passed
    ).length;

    const totalScore = results.reduce(
      (sum, r) =>
        sum + Number(r.result.percentage || 0),
      0
    );

    return {
      totalAttempts,
      passRate: (
        (passCount / totalAttempts) *
        100
      ).toFixed(2),
      avgScore: (
        totalScore / totalAttempts
      ).toFixed(2),
    };
  };

  const getGradeColor = (percentage) => {
    if (percentage >= 80) return '#28a745';
    if (percentage >= 70) return '#ffc107';
    if (percentage >= 60) return '#fd7e14';
    return '#dc3545';
  };

  if (isLoading) {
    return (
      <div className="results-detail-container">
        <header className="admin-header">
          <div className="header-content">
            <h1>Results Details</h1>

            <button
              onClick={handleLogout}
              className="logout-button"
            >
              Logout
            </button>
          </div>
        </header>

        <main className="admin-main">
          <div className="loading">
            Loading results...
          </div>
        </main>
      </div>
    );
  }

  const stats = calculateStats();

  return (
    <div className="results-detail-container">

      {/* Header */}
      <header className="admin-header">
        <div className="header-content">

          <h1>Results Details</h1>

          <button
            onClick={handleLogout}
            className="logout-button"
          >
            Logout
          </button>

        </div>
      </header>

      {/* Main Content */}
      <main className="admin-main">

        <div className="results-section">

          {/* Navigation */}
          <div className="section-header">

            <div>
              <h2>
                {exam?.name || 'Exam Results'}
              </h2>

              <p className="exam-subtitle">
                Duration: {exam?.duration_minutes} minutes
                {' | '}
                Questions: {exam?.total_questions}
              </p>
            </div>

            <button
              onClick={handleBackToResults}
              className="back-button"
            >
              ← Back to Results
            </button>

          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {/* Analytics Cards */}
          {results.length > 0 && (
            <div className="analytics-grid">

              <div className="analytics-card">
                <div className="stat-value">
                  {stats.totalAttempts}
                </div>

                <div className="stat-label">
                  Total Attempts
                </div>
              </div>

              <div className="analytics-card">
                <div className="stat-value">
                  {stats.passRate}%
                </div>

                <div className="stat-label">
                  Pass Rate
                </div>
              </div>

              <div className="analytics-card">
                <div className="stat-value">
                  {stats.avgScore}%
                </div>

                <div className="stat-label">
                  Average Score
                </div>
              </div>

            </div>
          )}

          {/* Results */}
          {results.length === 0 ? (

            <div className="empty-state">
              <div className="empty-icon">
                📋
              </div>

              <p>
                No student results for this exam yet
              </p>
            </div>

          ) : (

            <div className="results-list">

              {results.map((resultData) => {

                const result = resultData.result;
                const student = resultData.student;

                const isExpanded =
                  expandedStudentId === student.id;

                return (
                  <div
                    key={student.id}
                    className="result-card"
                  >

                    {/* Summary Row */}
                    <div
                      className="result-summary-row"
                      onClick={() =>
                        handleViewDetails(student.id)
                      }
                    >

                      <div className="result-main-info">

                        <div className="student-info">

                          <h3>
                            {student.full_name ||
                              student.username}
                          </h3>

                          <p className="student-email">
                            {student.email}
                          </p>

                        </div>

                        <div
                          className="result-score"
                          style={{
                            borderColor:
                              getGradeColor(
                                result.percentage
                              )
                          }}
                        >

                          <span
                            className="score-number"
                            style={{
                              color:
                                getGradeColor(
                                  result.percentage
                                )
                            }}
                          >
                            {Number(
                              result.percentage || 0
                            ).toFixed(1)}%
                          </span>

                        </div>

                        <div className="result-details-summary">

                          <span className="score-text">
                            Score: {result.score}/
                            {result.total_marks}
                          </span>

                          <span
                            className={`status-badge ${
                              result.is_passed
                                ? 'passed'
                                : 'failed'
                            }`}
                          >
                            {result.is_passed
                              ? '✓ Passed'
                              : '✗ Failed'}
                          </span>

                        </div>

                        {/* IST TIME */}
                        <div className="submission-time">
                          <span>
                            {formatDate(
                              result.submitted_at
                            )}
                          </span>
                        </div>

                      </div>

                      <div className="expand-toggle">
                        <span className="toggle-icon">
                          {isExpanded ? '▼' : '▶'}
                        </span>
                      </div>

                    </div>

                    {/* Expanded Details */}
                    {isExpanded && (
                      <div className="result-details-expanded">

                        {loadingDetail ? (

                          <div className="loading-details">
                            Loading answer details...
                          </div>

                        ) : selectedStudentResult ? (

                          <div className="detailed-answers">

                            <div className="detail-header">

                              <h4>
                                Answer Review
                              </h4>

                              <div className="detail-stats">

                                <span>
                                  Correct:{' '}
                                  <strong className="correct">
                                    {result.correct_answers}
                                  </strong>
                                </span>

                                <span>
                                  Incorrect:{' '}
                                  <strong className="incorrect">
                                    {result.incorrect_answers}
                                  </strong>
                                </span>

                                <span>
                                  Unanswered:{' '}
                                  <strong className="unanswered">
                                    {result.unanswered}
                                  </strong>
                                </span>

                              </div>

                            </div>

                            <div className="answers-grid">

                              {selectedStudentResult.answers.map(
                                (answer, index) => (

                                  <div
                                    key={index}
                                    className={`answer-card ${
                                      answer.is_correct
                                        ? 'correct'
                                        : 'incorrect'
                                    }`}
                                  >

                                    <div className="answer-header">

                                      <span className="question-number">
                                        Q{index + 1}
                                      </span>

                                      <span
                                        className={`answer-status ${
                                          answer.is_correct
                                            ? 'correct'
                                            : 'incorrect'
                                        }`}
                                      >
                                        {answer.is_correct
                                          ? '✓ Correct'
                                          : '✗ Incorrect'}
                                      </span>

                                    </div>

                                    <p className="question-text">
                                      {answer.question_text}
                                    </p>

                                    <div className="answer-options">

                                      <div className="option student">

                                        <span className="label">
                                          Student Answer:
                                        </span>

                                        <span className="value">
                                          {answer.student_answer?.option_text ||
                                            '(Not answered)'}
                                        </span>

                                      </div>

                                      <div className="option correct">

                                        <span className="label">
                                          Correct Answer:
                                        </span>

                                        <span className="value">
                                          {answer.correct_answer?.option_text ||
                                            '-'}
                                        </span>

                                      </div>

                                    </div>

                                  </div>

                                )
                              )}

                            </div>

                          </div>

                        ) : null}

                      </div>
                    )}

                  </div>
                );
              })}

            </div>
          )}

        </div>

      </main>

    </div>
  );
};

export default ResultsDetailView;