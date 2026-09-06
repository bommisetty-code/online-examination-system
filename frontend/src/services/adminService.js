import apiClient from './apiClient';

export const adminService = {
  // Exam Management
  getExams: async () => {
    const response = await apiClient.get('/admin/exams');
    return response.data.exams;
  },

  createExam: async (examData) => {
    const response = await apiClient.post('/admin/exams', examData);
    return response.data;
  },

  getExam: async (examId) => {
    const response = await apiClient.get(`/admin/exams/${examId}`);
    return response.data.exam;
  },

  updateExam: async (examId, examData) => {
    const response = await apiClient.put(`/admin/exams/${examId}`, examData);
    return response.data;
  },

  deleteExam: async (examId) => {
    const response = await apiClient.delete(`/admin/exams/${examId}`);
    return response.data;
  },

  activateExam: async (examId, isActive) => {
    const response = await apiClient.patch(`/admin/exams/${examId}/activate`, {
      is_active: isActive,
    });
    return response.data;
  },

  // Question Management
  getQuestions: async (examId) => {
    const response = await apiClient.get(`/admin/exams/${examId}/questions`);
    return response.data.questions;
  },

  createQuestion: async (examId, questionData) => {
    const response = await apiClient.post(`/admin/exams/${examId}/questions`, questionData);
    return response.data;
  },

  getQuestion: async (examId, questionId) => {
    const response = await apiClient.get(`/admin/exams/${examId}/questions/${questionId}`);
    return response.data.question;
  },

  updateQuestion: async (examId, questionId, questionData) => {
    const response = await apiClient.put(`/admin/exams/${examId}/questions/${questionId}`, questionData);
    return response.data;
  },

  deleteQuestion: async (examId, questionId) => {
    const response = await apiClient.delete(`/admin/exams/${examId}/questions/${questionId}`);
    return response.data;
  },

  // Students
  getStudents: async () => {
    const response = await apiClient.get('/admin/students');
    return response.data.students;
  },

  createStudent: async (studentData) => {
    const response = await apiClient.post('/admin/students', studentData);
    return response.data;
  },

  // Results
  getExamResults: async (examId) => {
    const response = await apiClient.get(`/admin/exams/${examId}/results`);
    return response.data.results;
  },

  getStudentResult: async (examId, studentId) => {
    const response = await apiClient.get(`/admin/exams/${examId}/results/${studentId}`);
    return response.data;
  },
};

export default adminService;
