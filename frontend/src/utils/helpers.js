// Storage utilities
export const storage = {
  setItem: (key, value) => {
    localStorage.setItem(key, JSON.stringify(value));
  },

  getItem: (key) => {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : null;
  },

  removeItem: (key) => {
    localStorage.removeItem(key);
  },

  clear: () => {
    localStorage.clear();
  },
};

// Validation utilities
export const validators = {
  isValidEmail: (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  },

  isValidUsername: (username) => {
    return username.length >= 3 && username.length <= 20 && /^[a-zA-Z0-9_]+$/.test(username);
  },

  isValidPassword: (password) => {
    return (
      password.length >= 6 &&
      /[A-Z]/.test(password) &&
      /[a-z]/.test(password) &&
      /\d/.test(password)
    );
  },
};

// Format utilities
export const formatters = {
  formatTime: (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  },

  formatDate: (date) => {
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  },

  getGradeColor: (percentage) => {
    if (percentage >= 80) return '#28a745'; // Green
    if (percentage >= 70) return '#ffc107'; // Yellow
    if (percentage >= 60) return '#fd7e14'; // Orange
    return '#dc3545'; // Red
  },
};

// Notification utilities
export const notify = {
  success: (message) => {
    console.log('✓ ', message);
  },

  error: (message) => {
    console.error('✗ ', message);
  },

  warning: (message) => {
    console.warn('⚠ ', message);
  },
};
