import React from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate
} from 'react-router-dom';

import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

import LoginPage from './pages/LoginPage';

import AdminDashboard from './pages/AdminDashboard';
import ExamManagement from './pages/ExamManagement';
import AdminResultsDashboard from './pages/AdminResultsDashboard';
import ResultsDetailView from './pages/ResultsDetailView';

import StudentDashboard from './pages/StudentDashboard';
import ExamInterface from './pages/ExamInterface';
import ResultsPage from './pages/ResultsPage';
import StudentAnswerReview from './pages/StudentAnswerReview';

import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>

          {/* =====================================================
              ROOT
          ===================================================== */}

          <Route
            path="/"
            element={<Navigate to="/login" replace />}
          />


          {/* =====================================================
              PUBLIC ROUTES
          ===================================================== */}

          <Route
            path="/login"
            element={<LoginPage />}
          />


          {/* =====================================================
              ADMIN ROUTES
          ===================================================== */}

          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute requiredRole="admin">
                <AdminDashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/exam/:examId/manage"
            element={
              <ProtectedRoute requiredRole="admin">
                <ExamManagement />
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/results"
            element={
              <ProtectedRoute requiredRole="admin">
                <AdminResultsDashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/results/:examId"
            element={
              <ProtectedRoute requiredRole="admin">
                <ResultsDetailView />
              </ProtectedRoute>
            }
          />


          {/* =====================================================
              STUDENT ROUTES
          ===================================================== */}

          {/* Student Dashboard */}
          <Route
            path="/student/dashboard"
            element={
              <ProtectedRoute requiredRole="student">
                <StudentDashboard />
              </ProtectedRoute>
            }
          />


          {/* Active Exam */}
          <Route
            path="/student/exam/:submissionId"
            element={
              <ProtectedRoute requiredRole="student">
                <ExamInterface />
              </ProtectedRoute>
            }
          />


          {/* Result Page */}
          <Route
            path="/student/results/:submissionId"
            element={
              <ProtectedRoute requiredRole="student">
                <ResultsPage />
              </ProtectedRoute>
            }
          />


          {/* Answer Review */}
          <Route
            path="/student/result-review/:submissionId"
            element={
              <ProtectedRoute requiredRole="student">
                <StudentAnswerReview />
              </ProtectedRoute>
            }
          />


          {/* =====================================================
              FALLBACK
          ===================================================== */}

          <Route
            path="*"
            element={<Navigate to="/login" replace />}
          />

        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;