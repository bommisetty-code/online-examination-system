import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import '../styles/LoginPage.css';

export const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await login(username, password);

      // Redirect based on role
      if (response.user.role === 'admin') {
        navigate('/admin/dashboard');
      } else if (response.user.role === 'student') {
        navigate('/student/dashboard');
      }
    } catch (err) {
      setError(
        err.response?.data?.message ||
        'Login failed. Please try again.'
      );
      setPassword('');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">

        <h1>Online Examination System</h1>
        <h2>Login</h2>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>

          <div className="form-group">
            <label htmlFor="username">
              Username:
            </label>

            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              required
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">
              Password:
            </label>

            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              disabled={isLoading}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="login-button"
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>

        </form>

      </div>
    </div>
  );
};

export default LoginPage;