import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import adminService from '../services/adminService';
import '../styles/AdminDashboard.css';

export const AdminDashboard = () => {
  const [exams, setExams] = useState([]);
  const [students, setStudents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showStudentForm, setShowStudentForm] = useState(false);

  // Exam form
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    duration_minutes: 30,
    passing_percentage: 50,
    student_class: '7th',
  });

  // Student form
  const [studentForm, setStudentForm] = useState({
    email: '',
    username: '',
    password: '',
    full_name: '',
    student_class: '7th',
  });

  const navigate = useNavigate();
  const { logout } = useAuth();

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setIsLoading(true);
      setError('');

      const [examsData, studentsData] = await Promise.all([
        adminService.getExams(),
        adminService.getStudents(),
      ]);

      setExams(examsData);
      setStudents(studentsData);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // =========================
  // EXAM INPUT CHANGE
  // =========================
  const handleInputChange = (e) => {
    const { name, value } = e.target;

    setFormData(prev => ({
      ...prev,
      [name]:
        name === 'duration_minutes' || name === 'passing_percentage'
          ? parseInt(value, 10)
          : value,
    }));
  };

  // =========================
  // CREATE EXAM
  // =========================
  const handleCreateExam = async (e) => {
    e.preventDefault();

    try {
      setError('');

      await adminService.createExam(formData);

      setFormData({
        name: '',
        description: '',
        duration_minutes: 30,
        passing_percentage: 50,
        student_class: '7th',
      });

      setShowCreateForm(false);

      await loadDashboard();
    } catch (err) {
      setError(
        err.response?.data?.message || 'Failed to create exam'
      );
    }
  };

  // =========================
  // CREATE STUDENT
  // =========================
  const handleCreateStudent = async (e) => {
    e.preventDefault();

    try {
      setError('');

      await adminService.createStudent(studentForm);

      setStudentForm({
        email: '',
        username: '',
        password: '',
        full_name: '',
        student_class: '7th',
      });

      setShowStudentForm(false);

      await loadDashboard();
    } catch (err) {
      setError(
        err.response?.data?.message || 'Failed to create student'
      );
    }
  };

  // =========================
  // TOGGLE EXAM ACTIVE
  // =========================
  const handleToggleActive = async (examId, currentStatus) => {
    try {
      setError('');

      await adminService.activateExam(
        examId,
        !currentStatus
      );

      await loadDashboard();
    } catch (err) {
      setError('Failed to update exam status');
    }
  };

  // =========================
  // DELETE EXAM
  // =========================
  const handleDeleteExam = async (examId) => {
    if (
      window.confirm(
        'Are you sure you want to delete this exam? This action cannot be undone.'
      )
    ) {
      try {
        setError('');

        await adminService.deleteExam(examId);

        await loadDashboard();
      } catch (err) {
        setError('Failed to delete exam');
      }
    }
  };

  // =========================
  // LOGOUT
  // =========================
  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // =========================
  // RESULTS
  // =========================
  const handleViewResults = () => {
    navigate('/admin/results');
  };

  if (isLoading) {
    return <div className="loading">Loading exams...</div>;
  }

  return (
    <div className="admin-container">

      {/* ================= HEADER ================= */}
      <header className="admin-header">
        <div className="header-content">

          <h1>Admin Dashboard</h1>

          <div className="header-buttons">

            <button
              onClick={handleViewResults}
              className="results-button"
              title="View exam results"
            >
              📊 Results
            </button>

            <button
              onClick={handleLogout}
              className="logout-button"
            >
              Logout
            </button>

          </div>

        </div>
      </header>

      {/* ================= MAIN ================= */}
      <main className="admin-main">

        <section className="exams-section">

          <div className="section-header">

            <h2>Exams</h2>

            <button
              onClick={() =>
                setShowCreateForm(!showCreateForm)
              }
              className="create-button"
            >
              {showCreateForm
                ? 'Cancel'
                : 'Create New Exam'}
            </button>

          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <div className="admin-panels">

            {/* =====================================================
                STUDENTS PANEL
            ===================================================== */}

            <div className="panel-block">

              <div className="section-header compact">

                <h3>Students</h3>

                <button
                  onClick={() =>
                    setShowStudentForm(!showStudentForm)
                  }
                  className="create-button small"
                >
                  {showStudentForm
                    ? 'Cancel'
                    : 'Create Student'}
                </button>

              </div>

              {/* ================= STUDENT FORM ================= */}

              {showStudentForm && (

                <form
                  onSubmit={handleCreateStudent}
                  className="exam-form compact-form"
                >

                  <h3>Create Student</h3>

                  {/* Full Name */}
                  <div className="form-group">

                    <label htmlFor="student-full-name">
                      Full Name:
                    </label>

                    <input
                      id="student-full-name"
                      type="text"
                      value={studentForm.full_name}
                      onChange={(e) =>
                        setStudentForm({
                          ...studentForm,
                          full_name: e.target.value,
                        })
                      }
                    />

                  </div>

                  {/* Email */}
                  <div className="form-group">

                    <label htmlFor="student-email">
                      Email:
                    </label>

                    <input
                      id="student-email"
                      type="email"
                      value={studentForm.email}
                      onChange={(e) =>
                        setStudentForm({
                          ...studentForm,
                          email: e.target.value,
                        })
                      }
                      required
                    />

                  </div>

                  {/* Username */}
                  <div className="form-group">

                    <label htmlFor="student-username">
                      Username:
                    </label>

                    <input
                      id="student-username"
                      type="text"
                      value={studentForm.username}
                      onChange={(e) =>
                        setStudentForm({
                          ...studentForm,
                          username: e.target.value,
                        })
                      }
                      required
                    />

                  </div>

                  {/* Password */}
                  <div className="form-group">

                    <label htmlFor="student-password">
                      Password:
                    </label>

                    <input
                      id="student-password"
                      type="password"
                      value={studentForm.password}
                      onChange={(e) =>
                        setStudentForm({
                          ...studentForm,
                          password: e.target.value,
                        })
                      }
                      required
                    />

                  </div>

                  {/* ================= CLASS DROPDOWN ================= */}

                  <div className="form-group">

                    <label htmlFor="student-class">
                      Student Class:
                    </label>

                    <select
                      id="student-class"
                      value={studentForm.student_class}
                      onChange={(e) =>
                        setStudentForm({
                          ...studentForm,
                          student_class: e.target.value,
                        })
                      }
                      required
                    >

                      <option value="7th">
                        7th Class
                      </option>

                      <option value="8th">
                        8th Class
                      </option>

                      <option value="10th">
                        10th Class
                      </option>

                    </select>

                  </div>

                  <button
                    type="submit"
                    className="submit-button"
                  >
                    Create Student
                  </button>

                </form>

              )}

              {/* ================= STUDENT LIST ================= */}

              <div className="student-list compact-list">

                {students.length === 0 ? (

                  <p className="no-exams">
                    No students yet.
                  </p>

                ) : (

                  students.map(student => (

                    <div
                      key={student.id}
                      className="student-card"
                    >

                      <div>

                        <strong>
                          {student.full_name ||
                            student.username}
                        </strong>

                        <div>
                          {student.username}
                        </div>

                        <div>
                          Class:{' '}
                          <strong>
                            {student.student_class ||
                              'Not Assigned'}
                          </strong>
                        </div>

                      </div>

                      <span
                        className={`exam-status ${
                          student.is_active
                            ? 'active'
                            : 'inactive'
                        }`}
                      >
                        {student.is_active
                          ? 'Active'
                          : 'Inactive'}
                      </span>

                    </div>

                  ))

                )}

              </div>

            </div>

            {/* =====================================================
                CREATE EXAM PANEL
            ===================================================== */}

            <div className="panel-block">

              {showCreateForm && (

                <form
                  onSubmit={handleCreateExam}
                  className="exam-form"
                >

                  <h3>Create New Exam</h3>

                  {/* Exam Name */}
                  <div className="form-group">

                    <label htmlFor="name">
                      Exam Name:
                    </label>

                    <input
                      type="text"
                      id="name"
                      name="name"
                      value={formData.name}
                      onChange={handleInputChange}
                      required
                    />

                  </div>

                  {/* Description */}
                  <div className="form-group">

                    <label htmlFor="description">
                      Description:
                    </label>

                    <textarea
                      id="description"
                      name="description"
                      value={formData.description}
                      onChange={handleInputChange}
                      rows="3"
                    />

                  </div>

                  {/* ================= CLASS DROPDOWN ================= */}

                  <div className="form-group">

                    <label htmlFor="exam-class">
                      Class:
                    </label>

                    <select
                      id="exam-class"
                      name="student_class"
                      value={formData.student_class}
                      onChange={handleInputChange}
                      required
                    >

                      <option value="7th">
                        7th Class
                      </option>

                      <option value="8th">
                        8th Class
                      </option>

                      <option value="10th">
                        10th Class
                      </option>

                    </select>

                  </div>

                  {/* Duration + Passing */}
                  <div className="form-row">

                    <div className="form-group">

                      <label htmlFor="duration">
                        Duration (minutes):
                      </label>

                      <input
                        type="number"
                        id="duration"
                        name="duration_minutes"
                        value={
                          formData.duration_minutes
                        }
                        onChange={handleInputChange}
                        min="1"
                        required
                      />

                    </div>

                    <div className="form-group">

                      <label htmlFor="passing">
                        Passing Percentage:
                      </label>

                      <input
                        type="number"
                        id="passing"
                        name="passing_percentage"
                        value={
                          formData.passing_percentage
                        }
                        onChange={handleInputChange}
                        min="0"
                        max="100"
                        required
                      />

                    </div>

                  </div>

                  <button
                    type="submit"
                    className="submit-button"
                  >
                    Create Exam
                  </button>

                </form>

              )}

            </div>

          </div>

          {/* =====================================================
              EXAMS LIST
          ===================================================== */}

          {exams.length === 0 ? (

            <p className="no-exams">
              No exams yet. Create your first exam!
            </p>

          ) : (

            <div className="exams-list">

              {exams.map(exam => (

                <div
                  key={exam.id}
                  className="exam-card"
                >

                  <div className="exam-info">

                    <h3>{exam.name}</h3>

                    {exam.description && (
                      <p>{exam.description}</p>
                    )}

                    <div className="exam-details">

                      <span>
                        Class:{' '}
                        <strong>
                          {exam.student_class ||
                            'Not Assigned'}
                        </strong>
                      </span>

                      <span>
                        Duration:{' '}
                        {exam.duration_minutes} min
                      </span>

                      <span>
                        Questions:{' '}
                        {exam.total_questions}
                      </span>

                      <span>
                        Passing:{' '}
                        {exam.passing_percentage}%
                      </span>

                    </div>

                  </div>

                  <div className="exam-actions">

                    <button
                      onClick={() =>
                        navigate(
                          `/admin/exam/${exam.id}/manage`
                        )
                      }
                      className="action-button manage"
                    >
                      Manage Questions
                    </button>

                    <button
                      onClick={() =>
                        navigate(
                          `/admin/exam/${exam.id}/results`
                        )
                      }
                      className="action-button results"
                    >
                      View Results
                    </button>

                    <button
                      onClick={() =>
                        handleToggleActive(
                          exam.id,
                          exam.is_active
                        )
                      }
                      className={`action-button ${
                        exam.is_active
                          ? 'deactivate'
                          : 'activate'
                      }`}
                    >
                      {exam.is_active
                        ? 'Deactivate'
                        : 'Activate'}
                    </button>

                    <button
                      onClick={() =>
                        navigate(
                          `/admin/exam/${exam.id}/edit`
                        )
                      }
                      className="action-button edit"
                    >
                      Edit
                    </button>

                    <button
                      onClick={() =>
                        handleDeleteExam(exam.id)
                      }
                      className="action-button delete"
                    >
                      Delete
                    </button>

                  </div>

                </div>

              ))}

            </div>

          )}

        </section>

      </main>

    </div>
  );
};

export default AdminDashboard;