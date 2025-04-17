import React, { useState, useEffect } from 'react';
import './LandingPage.css';

const LandingPage = ({ 
  onCreateTimetable, 
  onViewTimetables,  // Add this prop
  isDarkMode, 
  toggleTheme 
}) => {
  const [isTyping, setIsTyping] = useState(false);
  const [typedText, setTypedText] = useState('');
  const [typedSecondLine, setTypedSecondLine] = useState('');
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

  return (
    <div className={`landing-container ${isDarkMode ? 'dark' : 'light'}`}>
      {/* Header Section */}
      <header className="header">
        <div className="logo-section">
          <img 
            src="/srmlogo.png" 
            alt="SRM Logo" 
            className="logo"
          />
        </div>
        
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
      </header>

      <div className="divider"></div>

      {/* Main Content */}
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
              onClick={onViewTimetables}  // Add onClick handler
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
    </div>
  );
};

export default LandingPage;