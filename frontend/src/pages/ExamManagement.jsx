import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import adminService from '../services/adminService';
import '../styles/ExamManagement.css';

export const ExamManagement = () => {
  const { examId } = useParams();
  const navigate = useNavigate();
  
  const [exam, setExam] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showQuestionForm, setShowQuestionForm] = useState(false);
  const [editingQuestionId, setEditingQuestionId] = useState(null);
  const [formData, setFormData] = useState({
    question_text: '',
    marks: 1,
    options: [
      { option_text: '', is_correct: false },
      { option_text: '', is_correct: false },
      { option_text: '', is_correct: false },
      { option_text: '', is_correct: false },
    ],
  });

  useEffect(() => {
    loadExamAndQuestions();
  }, [examId]);

  const loadExamAndQuestions = async () => {
    try {
      setIsLoading(true);
      const examData = await adminService.getExam(examId);
      const questionsData = await adminService.getQuestions(examId);
      
      setExam(examData);
      setQuestions(questionsData);
    } catch (err) {
      setError('Failed to load exam data');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuestionInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'marks' ? parseInt(value) : value,
    }));
  };

  const handleOptionChange = (index, field, value) => {
    const updatedOptions = [...formData.options];
    if (field === 'option_text') {
      updatedOptions[index].option_text = value;
    } else if (field === 'is_correct') {
      // Only one option can be correct
      updatedOptions.forEach((opt, i) => {
        opt.is_correct = i === index ? value : false;
      });
    }
    setFormData(prev => ({
      ...prev,
      options: updatedOptions,
    }));
  };

  const handleCreateQuestion = async (e) => {
    e.preventDefault();
    
    // Validate
    if (!formData.question_text.trim()) {
      setError('Question text is required');
      return;
    }
    
    const filledOptions = formData.options.filter(opt => opt.option_text.trim());
    if (filledOptions.length < 2) {
      setError('At least 2 options are required');
      return;
    }

    const hasCorrectOption = formData.options.some(opt => opt.is_correct);
    if (!hasCorrectOption) {
      setError('Please select a correct option');
      return;
    }

    try {
      const payload = {
        question_text: formData.question_text,
        marks: formData.marks,
        options: formData.options.filter(opt => opt.option_text.trim()),
      };

      if (editingQuestionId) {
        await adminService.updateQuestion(examId, editingQuestionId, payload);
      } else {
        await adminService.createQuestion(examId, payload);
      }

      // Reset form
      setFormData({
        question_text: '',
        marks: 1,
        options: [
          { option_text: '', is_correct: false },
          { option_text: '', is_correct: false },
          { option_text: '', is_correct: false },
          { option_text: '', is_correct: false },
        ],
      });
      setEditingQuestionId(null);
      setShowQuestionForm(false);
      setError('');
      
      await loadExamAndQuestions();
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to save question');
    }
  };

  const handleEditQuestion = (question) => {
    setEditingQuestionId(question.id);
    setFormData({
      question_text: question.question_text,
      marks: question.marks,
      options: question.options.map(opt => ({
        option_text: opt.option_text,
        is_correct: opt.is_correct,
      })),
    });
    setShowQuestionForm(true);
  };

  const handleDeleteQuestion = async (questionId) => {
    if (window.confirm('Are you sure you want to delete this question?')) {
      try {
        await adminService.deleteQuestion(examId, questionId);
        await loadExamAndQuestions();
      } catch (err) {
        setError('Failed to delete question');
      }
    }
  };

  if (isLoading) {
    return <div className="loading">Loading exam data...</div>;
  }

  return (
    <div className="exam-management-container">
      <header className="management-header">
        <button onClick={() => navigate('/admin/dashboard')} className="back-button">
          ← Back to Dashboard
        </button>
        <h1>{exam?.name}</h1>
      </header>

      <main className="management-main">
        <section className="exam-info">
          <div className="info-card">
            <p><strong>Duration:</strong> {exam?.duration_minutes} minutes</p>
            <p><strong>Total Questions:</strong> {questions.length}</p>
            <p><strong>Passing Percentage:</strong> {exam?.passing_percentage}%</p>
            <p><strong>Status:</strong> {exam?.is_active ? 'Active' : 'Inactive'}</p>
          </div>
        </section>

        {error && <div className="error-message">{error}</div>}

        <section className="questions-section">
          <div className="section-header">
            <h2>Questions</h2>
            <button 
              onClick={() => {
                setShowQuestionForm(!showQuestionForm);
                setEditingQuestionId(null);
                if (showQuestionForm) {
                  setFormData({
                    question_text: '',
                    marks: 1,
                    options: [
                      { option_text: '', is_correct: false },
                      { option_text: '', is_correct: false },
                      { option_text: '', is_correct: false },
                      { option_text: '', is_correct: false },
                    ],
                  });
                }
              }}
              className="create-button"
            >
              {showQuestionForm ? 'Cancel' : 'Add Question'}
            </button>
          </div>

          {showQuestionForm && (
            <form onSubmit={handleCreateQuestion} className="question-form">
              <h3>{editingQuestionId ? 'Edit Question' : 'Create New Question'}</h3>
              
              <div className="form-group">
                <label htmlFor="question_text">Question:</label>
                <textarea
                  id="question_text"
                  name="question_text"
                  value={formData.question_text}
                  onChange={handleQuestionInputChange}
                  rows="3"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="marks">Marks:</label>
                <input
                  type="number"
                  id="marks"
                  name="marks"
                  value={formData.marks}
                  onChange={handleQuestionInputChange}
                  min="1"
                  required
                />
              </div>

              <div className="options-section">
                <h4>Options (Select one as correct):</h4>
                {formData.options.map((option, index) => (
                  <div key={index} className="option-group">
                    <input
                      type="radio"
                      name="correct_option"
                      checked={option.is_correct}
                      onChange={() => handleOptionChange(index, 'is_correct', true)}
                      title="Mark as correct answer"
                    />
                    <input
                      type="text"
                      value={option.option_text}
                      onChange={(e) => handleOptionChange(index, 'option_text', e.target.value)}
                      placeholder={`Option ${String.fromCharCode(65 + index)}`}
                    />
                  </div>
                ))}
              </div>

              <button type="submit" className="submit-button">
                {editingQuestionId ? 'Update Question' : 'Create Question'}
              </button>
            </form>
          )}

          {questions.length === 0 ? (
            <p className="no-questions">No questions added yet. Add your first question!</p>
          ) : (
            <div className="questions-list">
              {questions.map((question, index) => (
                <div key={question.id} className="question-card">
                  <div className="question-header">
                    <span className="question-number">Q{index + 1}</span>
                    <div className="question-actions">
                      <button
                        onClick={() => handleEditQuestion(question)}
                        className="action-button edit"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeleteQuestion(question.id)}
                        className="action-button delete"
                      >
                        Delete
                      </button>
                    </div>
                  </div>

                  <p className="question-text">{question.question_text}</p>
                  
                  <div className="question-meta">
                    <span>Marks: {question.marks}</span>
                  </div>

                  <div className="options-list">
                    {question.options.map((option, optIdx) => (
                      <div 
                        key={option.id} 
                        className={`option-item ${option.is_correct ? 'correct' : ''}`}
                      >
                        <span className="option-letter">{String.fromCharCode(65 + optIdx)}</span>
                        <span className="option-text">{option.option_text}</span>
                        {option.is_correct && <span className="correct-badge">✓ Correct</span>}
                      </div>
                    ))}
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

export default ExamManagement;
