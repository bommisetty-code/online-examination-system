import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import studentService from '../services/studentService';
import '../styles/StudentDashboard.css';

export const StudentDashboard = () => {
  const [exams, setExams] = useState([]);
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('available');

  const navigate = useNavigate();
  const { user, logout } = useAuth();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
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
      setError(
        err.response?.data?.message || 'Failed to load data'
      );
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartExam = async (examId) => {
    try {
      setError('');

      const response = await studentService.startExam(examId);

      if (!response?.submission_id) {
        setError('Unable to start exam. Submission ID not received.');
        return;
      }

      navigate(`/student/exam/${response.submission_id}`);
    } catch (err) {
      setError(
        err.response?.data?.message || 'Failed to start exam'
      );
      console.error(err);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getGradeColor = (percentage) => {
    if (percentage >= 80) return '#28a745';
    if (percentage >= 70) return '#ffc107';
    if (percentage >= 60) return '#fd7e14';
    return '#dc3545';
  };

  if (isLoading) {
    return <div className="loading">Loading exams...</div>;
  }

  /*
   * Student class
   *
   * Backend should return one of these:
   * user.class_name
   * user.student_class
   * user.class
   */
  const studentClass =
    user?.class_name ||
    user?.student_class ||
    user?.class ||
    '';

  /*
   * Show only exams belonging to student's class.
   *
   * Example:
   * Student class = 7
   * → Only 7th class exams are displayed.
   *
   * Student class = 8
   * → Only 8th class exams are displayed.
   *
   * Student class = 10
   * → Only 10th class exams are displayed.
   */
  const classFilteredExams = exams.filter((exam) => {
    if (!studentClass) {
      return true;
    }

    const examClass =
      exam.class_name ||
      exam.student_class ||
      exam.class ||
      '';

    return String(examClass).trim() === String(studentClass).trim();
  });

  const availableExams = classFilteredExams.filter(
    (exam) => !exam.already_taken
  );

  const completedExams = classFilteredExams.filter(
    (exam) => exam.already_taken
  );

  return (
    <div className="student-container">

      {/* Header */}
      <header className="student-header">
        <div className="header-content">

          <div>
            <h1>
              Welcome, {user?.full_name || user?.username}
            </h1>

            {studentClass && (
              <p className="student-class">
                Class: {studentClass}
              </p>
            )}
          </div>

          <button
            onClick={handleLogout}
            className="logout-button"
          >
            Logout
          </button>

        </div>
      </header>

      <main className="student-main">

        {/* Tabs */}
        <div className="tabs">

          <button
            className={`tab-button ${
              activeTab === 'available' ? 'active' : ''
            }`}
            onClick={() => setActiveTab('available')}
          >
            Available Exams ({availableExams.length})
          </button>

          <button
            className={`tab-button ${
              activeTab === 'completed' ? 'active' : ''
            }`}
            onClick={() => setActiveTab('completed')}
          >
            Completed Exams ({completedExams.length})
          </button>

          <button
            className={`tab-button ${
              activeTab === 'results' ? 'active' : ''
            }`}
            onClick={() => setActiveTab('results')}
          >
            Results ({results.length})
          </button>

        </div>

        {/* Error */}
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {/* ================= AVAILABLE EXAMS ================= */}

        {activeTab === 'available' && (
          <section className="exams-section">

            <h2>
              {studentClass
                ? `${studentClass} Class - Available Exams`
                : 'Available Exams'}
            </h2>

            {availableExams.length === 0 ? (

              <p className="no-exams">
                No available exams for your class at the moment.
              </p>

            ) : (

              <div className="exams-grid">

                {availableExams.map((exam) => (

                  <div
                    key={exam.id}
                    className="exam-card"
                  >

                    <div className="exam-header">

                      <h3>{exam.name}</h3>

                      <span className="exam-status active">
                        Available
                      </span>

                    </div>

                    {exam.description && (
                      <p className="exam-description">
                        {exam.description}
                      </p>
                    )}

                    <div className="exam-meta">

                      <div className="meta-item">
                        <span className="label">
                          Class:
                        </span>

                        <span className="value">
                          {exam.class_name ||
                            exam.student_class ||
                            exam.class ||
                            studentClass}
                        </span>
                      </div>

                      <div className="meta-item">
                        <span className="label">
                          Duration:
                        </span>

                        <span className="value">
                          {exam.duration_minutes} min
                        </span>
                      </div>

                      <div className="meta-item">
                        <span className="label">
                          Questions:
                        </span>

                        <span className="value">
                          {exam.total_questions}
                        </span>
                      </div>

                      <div className="meta-item">
                        <span className="label">
                          Passing:
                        </span>

                        <span className="value">
                          {exam.passing_percentage}%
                        </span>
                      </div>

                      {exam.admin_name && (
                        <div className="meta-item">

                          <span className="label">
                            By:
                          </span>

                          <span className="value">
                            {exam.admin_name}
                          </span>

                        </div>
                      )}

                    </div>

                    <button
                      onClick={() => handleStartExam(exam.id)}
                      className="start-exam-button"
                    >
                      Start Exam
                    </button>

                  </div>

                ))}

              </div>

            )}

          </section>
        )}

        {/* ================= COMPLETED EXAMS ================= */}

        {activeTab === 'completed' && (
          <section className="exams-section">

            <h2>
              {studentClass
                ? `${studentClass} Class - Completed Exams`
                : 'Completed Exams'}
            </h2>

            {completedExams.length === 0 ? (

              <p className="no-exams">
                You haven't completed any exams yet.
              </p>

            ) : (

              <div className="exams-list">

                {completedExams.map((exam) => (

                  <div
                    key={exam.id}
                    className="exam-item"
                  >

                    <div className="exam-info">

                      <h3>{exam.name}</h3>

                      <p>
                        You cannot retake this exam.
                      </p>

                    </div>

                    <span className="exam-status completed">
                      Completed
                    </span>

                  </div>

                ))}

              </div>

            )}

          </section>
        )}

        {/* ================= RESULTS ================= */}

        {activeTab === 'results' && (
          <section className="results-section">

            <h2>Exam Results</h2>

            {results.length === 0 ? (

              <p className="no-results">
                No results yet.
              </p>

            ) : (

              <div className="results-table">

                <div className="table-header">

                  <div className="col-exam">
                    Exam Name
                  </div>

                  <div className="col-score">
                    Score
                  </div>

                  <div className="col-percentage">
                    Percentage
                  </div>

                  <div className="col-status">
                    Status
                  </div>

                  <div className="col-date">
                    Date
                  </div>

                </div>

                {results.map((result) => (

                  <div
                    key={result.id}
                    className="table-row"
                  >

                    <div className="col-exam">
                      {result.exam_name}
                    </div>

                    <div className="col-score">
                      {result.correct_answers}/
                      {result.total_questions}
                    </div>

                    <div className="col-percentage">

                      <span
                        className="percentage-badge"
                        style={{
                          backgroundColor:
                            getGradeColor(
                              result.percentage
                            ),
                        }}
                      >
                        {Number(result.percentage).toFixed(2)}%
                      </span>

                    </div>

                    <div className="col-status">

                      <span
                        className={`status-badge ${
                          result.is_passed
                            ? 'passed'
                            : 'failed'
                        }`}
                      >
                        {result.is_passed
                          ? 'Passed'
                          : 'Failed'}
                      </span>

                    </div>

                    <div className="col-date">

                      {new Date(
                        result.submitted_at
                      ).toLocaleDateString(
                        'en-US',
                        {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        }
                      )}

                    </div>

                  </div>

                ))}

              </div>

            )}

          </section>
        )}

      </main>
    </div>
  );
};

export default StudentDashboard;