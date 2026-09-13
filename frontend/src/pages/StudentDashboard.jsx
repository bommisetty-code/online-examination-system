import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import studentService from '../services/studentService';
import './StudentDashboard.css';

const StudentDashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [exams, setExams] = useState([]);
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('exams');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      setError('');

      const [examsData, resultsData] = await Promise.all([
        studentService.getAvailableExams(),
        studentService.getResultHistory(),
      ]);

      setExams(examsData || []);
      setResults(resultsData || []);
    } catch (err) {
      console.error('Dashboard loading error:', err);

      setError(
        err.response?.data?.message ||
        'Failed to load dashboard data.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartExam = async (examId) => {
    try {
      setError('');

      const response = await studentService.startExam(examId);

      if (response?.submission_id) {
        navigate(`/student/exam/${response.submission_id}`);
      } else {
        setError('Unable to start exam.');
      }
    } catch (err) {
      console.error('Start exam error:', err);

      setError(
        err.response?.data?.message ||
        'Unable to start exam.'
      );
    }
  };

  const handleViewReview = (submissionId) => {
    if (!submissionId) {
      setError('Unable to open answer review.');
      return;
    }

    navigate(`/student/result-review/${submissionId}`);
  };

  const formatDate = (dateValue) => {
    if (!dateValue) {
      return '-';
    }

    try {
      return new Date(dateValue).toLocaleDateString();
    } catch {
      return '-';
    }
  };

  if (isLoading) {
    return (
      <div className="student-dashboard">
        <div className="dashboard-loading">
          Loading...
        </div>
      </div>
    );
  }

  return (
    <div className="student-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div>
          <h1>Student Dashboard</h1>
          <p>
            Welcome, {user?.full_name || user?.username || 'Student'}
          </p>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="dashboard-error">
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="dashboard-tabs">
        <button
          className={activeTab === 'exams' ? 'active' : ''}
          onClick={() => setActiveTab('exams')}
        >
          Available Exams
        </button>

        <button
          className={activeTab === 'results' ? 'active' : ''}
          onClick={() => setActiveTab('results')}
        >
          My Results
        </button>
      </div>

      {/* Available Exams */}
      {activeTab === 'exams' && (
        <div className="dashboard-section">
          <h2>Available Exams</h2>

          {exams.length === 0 ? (
            <div className="empty-state">
              No exams are currently available.
            </div>
          ) : (
            <div className="exam-grid">
              {exams.map((exam) => (
                <div
                  className="exam-card"
                  key={exam.id}
                >
                  <h3>{exam.name}</h3>

                  {exam.description && (
                    <p>{exam.description}</p>
                  )}

                  <div className="exam-details">
                    <span>
                      Duration: {exam.duration_minutes} minutes
                    </span>

                    <span>
                      Questions: {exam.total_questions}
                    </span>
                  </div>

                  <button
                    className="start-exam-button"
                    onClick={() => handleStartExam(exam.id)}
                  >
                    Start Exam
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Results */}
      {activeTab === 'results' && (
        <div className="dashboard-section">
          <h2>My Results</h2>

          {results.length === 0 ? (
            <div className="empty-state">
              No exam results available.
            </div>
          ) : (
            <div className="results-table-container">
              <table className="results-table">
                <thead>
                  <tr>
                    <th>Exam Name</th>
                    <th>Score</th>
                    <th>Percentage</th>
                    <th>Status</th>
                    <th>Date</th>
                    <th>Review</th>
                  </tr>
                </thead>

                <tbody>
                  {results.map((result) => (
                    <tr key={result.id}>
                      <td>
                        {result.exam_name || result.exam?.name || '-'}
                      </td>

                      <td>
                        {result.score ?? 0} / {result.total_questions ?? 0}
                      </td>

                      <td>
                        {result.percentage != null
                          ? `${result.percentage}%`
                          : '-'}
                      </td>

                      <td>
                        <span
                          className={`result-status ${
                            result.status || ''
                          }`}
                        >
                          {result.status || 'Completed'}
                        </span>
                      </td>

                      <td>
                        {formatDate(
                          result.submitted_at ||
                          result.created_at ||
                          result.date
                        )}
                      </td>

                      <td>
                        {result.submission_id ? (
                          <button
                            type="button"
                            className="view-review-button"
                            onClick={() =>
                              handleViewReview(result.submission_id)
                            }
                          >
                            View Review
                          </button>
                        ) : (
                          <span className="review-unavailable">
                            Not Available
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StudentDashboard;