// CreateTimetable.jsx
import React, { useState, useEffect } from 'react';
import './CreateTimetable.css';

const CreateTimetable = ({ 
  onBack, 
  isDarkMode, 
  toggleTheme, 
  onGenerateTimetable // Add this new prop
}) => { 
  const [isTyping, setIsTyping] = useState(false);
  const [typedText, setTypedText] = useState('');
  const fullText = "Choose the departments required for timetable generation";

  useEffect(() => {
    setIsTyping(true);
    let currentText = '';
    let currentIndex = 0;

    const typingInterval = setInterval(() => {
      if (currentIndex < fullText.length) {
        currentText += fullText[currentIndex];
        setTypedText(currentText);
        currentIndex++;
      } else {
        clearInterval(typingInterval);
        setIsTyping(false);
      }
    }, 50);

    return () => clearInterval(typingInterval);
  }, []);

  // Handler for Generate Timetable button
  const handleGenerateTimetable = () => {
    // Call the onGenerateTimetable prop to navigate to GenerateTimetable page
    onGenerateTimetable();
  };

  return (
    <div className={`create-timetable-container ${isDarkMode ? 'dark' : 'light'}`}>
      {/* Header remains the same */}
      <header className="header">
        <div className="logo-section">
          <img src="/srmlogo.png" alt="SRM Logo" className="logo" />
        </div>
        
        <div className="theme-switch-wrapper">
          <div className="theme-switch" onClick={toggleTheme}>
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
        <button className="action-button back-button" onClick={onBack}>
          ← Back
          <div className="button-glow"></div>
        </button>

        <div className="title-section">
          <h1 className="title typing">
            {typedText}
            {isTyping && <span className="cursor">|</span>}
          </h1>
        </div>

        <div className="departments-container">
          <div className="departments-list">
            <p className="no-departments">
              No departments available. Please create one to generate the timetable.
            </p>
          </div>
        </div>

        <div className="buttons-container">
          <button className="action-button create-dept">
            Create a new department
            <div className="button-glow"></div>
          </button>

          <button 
            className="action-button generate"
            onClick={handleGenerateTimetable} // Add onClick handler
          >
            Generate Timetable
            <div className="button-glow"></div>
          </button>
        </div>
      </main>
    </div>
  );
};

export default CreateTimetable;