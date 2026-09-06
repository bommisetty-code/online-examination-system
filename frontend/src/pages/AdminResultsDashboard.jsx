import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import adminService from '../services/adminService';
import '../styles/AdminResultsDashboard.css';

export const AdminResultsDashboard = () => {
  const [exams, setExams] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { logout } = useAuth();

  useEffect(() => {
    loadExams();
  }, []);

  const loadExams = async () => {
    try {
      setIsLoading(true);
      setError('');
      const examsData = await adminService.getExams();
      setExams(examsData);
    } catch (err) {
      setError('Failed to load exams');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleViewResults = (examId) => {
    navigate(`/admin/results/${examId}`);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleBackToDashboard = () => {
    navigate('/admin/dashboard');
  };

  if (isLoading) {
    return (
      <div className="results-dashboard-container">
        <header className="admin-header">
          <div className="header-content">
            <h1>Results Dashboard</h1>
            <button onClick={handleLogout} className="logout-button">
              Logout
            </button>
          </div>
        </header>
        <main className="admin-main">
          <div className="loading">Loading exams...</div>
        </main>
      </div>
    );
  }

  return (
    <div className="results-dashboard-container">
      {/* Header */}
      <header className="admin-header">
        <div className="header-content">
          <h1>Results Dashboard</h1>
          <button onClick={handleLogout} className="logout-button">
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="admin-main">
        <div className="results-section">
          <div className="section-header">
            <h2>Exam Results Overview</h2>
            <button onClick={handleBackToDashboard} className="back-to-dashboard-button">
              Back to Dashboard
            </button>
          </div>

          {error && <div className="error-message">{error}</div>}

          {exams.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📊</div>
              <p>No exams created yet</p>
              <button onClick={handleBackToDashboard} className="create-button">
                Create an Exam
              </button>
            </div>
          ) : (
            <div className="exams-table-wrapper">
              <table className="exams-table">
                <thead>
                  <tr>
                    <th>Exam Name</th>
                    <th>Duration (min)</th>
                    <th>Status</th>
                    <th>Total Questions</th>
                    <th>Passing %</th>
                    <th>Created</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {exams.map((exam) => (
                    <tr key={exam.id}>
                      <td className="exam-name">{exam.name}</td>
                      <td>{exam.duration_minutes}</td>
                      <td>
                        <span className={`status-badge ${exam.is_active ? 'active' : 'inactive'}`}>
                          {exam.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>{exam.total_questions}</td>
                      <td>{exam.passing_percentage}%</td>
                      <td>{new Date(exam.created_at).toLocaleDateString()}</td>
                      <td>
                        <button
                          onClick={() => handleViewResults(exam.id)}
                          className="view-results-button"
                        >
                          View Results
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default AdminResultsDashboard;
