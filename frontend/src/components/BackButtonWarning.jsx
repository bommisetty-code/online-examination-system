import React from 'react';
import '../styles/BackButtonWarning.css';

export const BackButtonWarning = ({ onResponse }) => {
  return (
    <div className="warning-overlay">
      <div className="warning-modal">
        <div className="warning-icon">⚠️</div>
        <h3>Leave Exam?</h3>
        <p>
          You are about to leave the exam. If you proceed, your exam will be automatically submitted with your current answers.
        </p>
        <p className="warning-note">
          <strong>Note:</strong> This action cannot be undone.
        </p>
        <div className="warning-buttons">
          <button
            onClick={() => onResponse(false)}
            className="stay-button"
          >
            Stay in Exam
          </button>
          <button
            onClick={() => onResponse(true)}
            className="leave-button"
          >
            Submit & Leave
          </button>
        </div>
      </div>
    </div>
  );
};

export default BackButtonWarning;
