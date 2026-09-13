import apiClient from './apiClient';

export const studentService = {
  getAvailableExams: async () => {
    const response = await apiClient.get('/student/exams');
    return response.data.exams;
  },

  getExamDetails: async (examId) => {
    const response = await apiClient.get(
      `/student/exams/${examId}`
    );

    return response.data.exam;
  },

  startExam: async (examId) => {
    const response = await apiClient.post(
      `/student/exams/${examId}/start`
    );

    return response.data;
  },

  getExamQuestions: async (submissionId) => {
    const response = await apiClient.get(
      `/student/submissions/${submissionId}/questions`
    );

    return {
      questions: response.data.questions || [],
      submissionId: response.data.submission_id,
      examId: response.data.exam_id,
      remainingSeconds:
        response.data.remaining_seconds ?? null,
      durationMinutes:
        response.data.duration_minutes ?? null
    };
  },

  submitAnswer: async (
    submissionId,
    questionId,
    selectedOptionId
  ) => {
    const response = await apiClient.post(
      `/student/submissions/${submissionId}/answer`,
      {
        question_id: questionId,
        selected_option_id: selectedOptionId,
      }
    );

    return response.data;
  },

  getSubmissionStatus: async (submissionId) => {
    const response = await apiClient.get(
      `/student/submissions/${submissionId}/status`
    );

    return response.data;
  },

  submitExam: async (
    submissionId,
    autoSubmit = false
  ) => {
    const response = await apiClient.post(
      `/student/submissions/${submissionId}/submit`,
      {
        auto_submit: autoSubmit,
      }
    );

    return response.data;
  },

  // ========================================================
  // RESULT
  // ========================================================

  getResult: async (submissionId) => {
    const response = await apiClient.get(
      `/student/results/${submissionId}`
    );

    return response.data.result;
  },

  // ========================================================
  // RESULT HISTORY
  // ========================================================

  getResultHistory: async () => {
    const response = await apiClient.get(
      '/student/results/history'
    );

    return response.data.results;
  },

  // ========================================================
  // ANSWER REVIEW
  // ========================================================

  getResultReview: async (submissionId) => {
    const response = await apiClient.get(
      `/student/results/${submissionId}/review`
    );

    return response.data;
  },
};

export default studentService;