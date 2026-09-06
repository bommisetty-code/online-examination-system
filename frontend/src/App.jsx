import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
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
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />

          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />

          {/* Admin routes */}
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

          {/* Student routes */}
          <Route
            path="/student/dashboard"
            element={
              <ProtectedRoute requiredRole="student">
                <StudentDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/exam/:submissionId"
            element={
              <ProtectedRoute requiredRole="student">
                <ExamInterface />
              </ProtectedRoute>
            }
          />
          <Route
            path="/student/results/:submissionId"
            element={
              <ProtectedRoute requiredRole="student">
                <ResultsPage />
              </ProtectedRoute>
            }
          />

        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
