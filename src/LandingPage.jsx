import React, { useState, useEffect } from 'react';
import './LandingPage.css';

const LandingPage = ({ 
  onCreateTimetable, 
  onViewTimetables,
  isDarkMode, 
  toggleTheme,
  onLogout,
  onError 
}) => {
  const [isTyping, setIsTyping] = useState(false);
  const [typedText, setTypedText] = useState('');
  const [typedSecondLine, setTypedSecondLine] = useState('');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isChangePasswordOpen, setIsChangePasswordOpen] = useState(false);
  const [passwordData, setPasswordData] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [passwordError, setPasswordError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');

  const firstLine = "Welcome, ADMIN!";
  const secondLine = "Transform Months of Work into Minutes with our timetable scheduler!";

  useEffect(() => {
    setIsTyping(true);
    let currentText = '';
    let currentIndex = 0;
    let isFirstLineDone = false;

    const typingInterval = setInterval(() => {
      if (!isFirstLineDone) {
        if (currentIndex < firstLine.length) {
          currentText += firstLine[currentIndex];
          setTypedText(currentText);
          currentIndex++;
        } else {
          isFirstLineDone = true;
          currentText = '';
          currentIndex = 0;
        }
      } else {
        if (currentIndex < secondLine.length) {
          currentText += secondLine[currentIndex];
          setTypedSecondLine(currentText);
          currentIndex++;
        } else {
          clearInterval(typingInterval);
          setIsTyping(false);
        }
      }
    }, 50);

    return () => clearInterval(typingInterval);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isSettingsOpen && !event.target.closest('.settings-wrapper')) {
        setIsSettingsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isSettingsOpen]);

  const handleSettingsClick = () => {
    setIsSettingsOpen(!isSettingsOpen);
  };
  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');

    try {
      // Validate passwords match
      if (passwordData.newPassword !== passwordData.confirmPassword) {
        setPasswordError("New passwords don't match!");
        return;
      }

      // Validate password requirements
      const passwordRegex = /^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
      if (!passwordRegex.test(passwordData.newPassword)) {
        setPasswordError('Password must be at least 8 characters long and contain uppercase, lowercase, number and special character');
        return;
      }

      const response = await fetch('http://localhost:8000/api/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: 'SRM',  // or get from your auth context/state
          oldPassword: passwordData.oldPassword,
          newPassword: passwordData.newPassword
        })
      });

      const data = await response.json();

      if (response.ok) {
        setPasswordSuccess('Password changed successfully!');
        setTimeout(() => {
          setIsChangePasswordOpen(false);
          setPasswordData({ oldPassword: '', newPassword: '', confirmPassword: '' });
          setPasswordSuccess('');
        }, 2000);
      } else {
        throw new Error(data.message || 'Failed to change password');
      }

    } catch (error) {
      console.error('Password change error:', error);
      setPasswordError(error.message || 'An error occurred while changing password');
    }
  };
  return (
    <div className={`landing-container ${isDarkMode ? 'dark' : 'light'}`}>
      <header className="header">
        <div className="logo-section">
          <img 
            src="/srmlogo.png" 
            alt="SRM Logo" 
            className="logo"
          />
        </div>
        
        <div className="header-controls">
          <div className="theme-switch-wrapper">
            <div 
              className="theme-switch" 
              onClick={toggleTheme}
              aria-label="Toggle theme"
            >
              <div className={`switch-track ${isDarkMode ? 'dark' : 'light'}`}>
                <div className="switch-thumb">
                  {isDarkMode ? '🌙' : '☀️'}
                </div>
              </div>
            </div>
          </div>

          <div className="settings-wrapper">
            <button 
              className="settings-button" 
              onClick={handleSettingsClick}
              aria-label="Settings"
            >
              ⚙️
            </button>
            
            {isSettingsOpen && (
              <div className="settings-dropdown">
                <button onClick={() => {
                  setIsChangePasswordOpen(true);
                  setIsSettingsOpen(false);
                }}>
                  Change Password
                </button>
                <button onClick={onLogout}>
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="divider"></div>

      <main className="main-content">
        <div className="content-left">
          <div className="text-container">
            <h1 className="welcome-text typing">
              {typedText}
              {isTyping && !typedSecondLine && <span className="cursor">|</span>}
            </h1>
            <p className="subtitle typing">
              {typedSecondLine}
              {isTyping && typedSecondLine && <span className="cursor">|</span>}
            </p>
          </div>
          
          <div className="button-group">
            <button 
              className="action-button create"
              onClick={onCreateTimetable}
              aria-label="Create a new Timetable"
            >
              Create a new Timetable
              <div className="button-glow"></div>
            </button>
            <button 
              className="action-button view"
              onClick={onViewTimetables}
              aria-label="View existing Timetables"
            >
              View existing Timetables
              <div className="button-glow"></div>
            </button>
          </div>
        </div>

        <div className="content-right">
          <div className="device-container">
            <img 
              src="/ipad.png" 
              alt="iPad Preview" 
              className="ipad-preview" 
            />
          </div>
        </div>
      </main>

      {isChangePasswordOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h2>Change Password</h2>
            {passwordError && <div className="error-message">{passwordError}</div>}
            {passwordSuccess && <div className="success-message">{passwordSuccess}</div>}
            <form onSubmit={handleChangePassword}>
              <div className="modal-input-group">
                <input
                  type="password"
                  placeholder="Current Password"
                  value={passwordData.oldPassword}
                  onChange={(e) => setPasswordData({
                    ...passwordData,
                    oldPassword: e.target.value
                  })}
                  required
                />
              </div>
              <div className="modal-input-group">
                <input
                  type="password"
                  placeholder="New Password"
                  value={passwordData.newPassword}
                  onChange={(e) => setPasswordData({
                    ...passwordData,
                    newPassword: e.target.value
                  })}
                  required
                />
              </div>
              <div className="modal-input-group">
                <input
                  type="password"
                  placeholder="Confirm New Password"
                  value={passwordData.confirmPassword}
                  onChange={(e) => setPasswordData({
                    ...passwordData,
                    confirmPassword: e.target.value
                  })}
                  required
                />
              </div>
              <div className="modal-buttons">
                <button type="submit">Change Password</button>
                <button 
                  type="button" 
                  onClick={() => {
                    setIsChangePasswordOpen(false);
                    setPasswordError('');
                    setPasswordSuccess('');
                    setPasswordData({ oldPassword: '', newPassword: '', confirmPassword: '' });
                  }}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default LandingPage;