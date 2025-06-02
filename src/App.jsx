import React, { useState, useEffect, Suspense, lazy } from 'react';
import './App.css';

// Lazy load components
const LoginPage = lazy(() => import('./LoginPage'));
const LandingPage = lazy(() => import('./LandingPage'));
const CreateTimetable = lazy(() => import('./CreateTimetable'));
const GenerateTimetable = lazy(() => import('./GenerateTimetable'));
const ViewTimetablesPage = lazy(() => import('./ViewTimetablesPage'));
const SavedTimetables = lazy(() => import('./SavedTimetables')); // Add the new component

const ErrorFallback = ({ error, resetErrorBoundary }) => {
  return (
    <div role="alert" className="error-container">
      <h1>Something went wrong</h1>
      <pre style={{ color: 'red' }}>{error.message}</pre>
      <button onClick={resetErrorBoundary}>Try again</button>
    </div>
  );
};

function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentScreen, setCurrentScreen] = useState('loading');
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTimetableSchema, setSelectedTimetableSchema] = useState(null);

  useEffect(() => {
    const loadingTimer = setTimeout(() => {
      setIsLoading(false);
      setCurrentScreen('login');
    }, 4000);

    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      setIsDarkMode(savedTheme === 'dark');
    }

    return () => clearTimeout(loadingTimer);
  }, []);

  useEffect(() => {
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
    document.body.className = isDarkMode ? 'dark' : 'light';
  }, [isDarkMode]);

  const handleError = (error) => {
    console.error('Unhandled error:', error);
    setError(error);
  };

  const handleLoginSuccess = () => {
    setIsLoggedIn(true);
    setCurrentScreen('landing');
  };

  // Add logout handler
  const handleLogout = () => {
    setIsLoggedIn(false);
    setCurrentScreen('login');
    // Optional: Clear any stored session data
    localStorage.removeItem('user');
  };

  // Add password change handler
  const handlePasswordChange = async (oldPassword, newPassword) => {
    try {
      // Here you would typically make an API call to change the password
      console.log('Password change requested', { oldPassword, newPassword });
      // If successful, you might want to show a success message
      return { success: true, message: 'Password changed successfully' };
    } catch (error) {
      handleError(error);
      return { success: false, message: error.message };
    }
  };

  const handleCreateTimetable = () => {
    setCurrentScreen('create-timetable');
  };

  const handleGenerateTimetable = () => {
    setCurrentScreen('generate-timetable');
  };

  const handleViewTimetables = () => {
    // First go to the saved timetables screen
    setCurrentScreen('saved-timetables');
  };

  const handleViewSpecificTimetable = (schemaName) => {
    // Set the selected schema and navigate to view-timetables
    setSelectedTimetableSchema(schemaName);
    setCurrentScreen('view-timetables');
  };

  const handleBack = () => {
    // Handle back navigation based on current screen
    switch (currentScreen) {
      case 'saved-timetables':
        setCurrentScreen('landing');
        break;
        
      case 'view-timetables':
        // Go back to saved timetables, not landing
        setCurrentScreen('saved-timetables');
        break;
        
      default:
        setCurrentScreen('landing');
        break;
    }
  };

  const toggleTheme = () => {
    setIsDarkMode(prevMode => {
      const newMode = !prevMode;
      localStorage.setItem('theme', newMode ? 'dark' : 'light');
      return newMode;
    });
  };

  const resetError = () => {
    setError(null);
  };

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="logo-wrapper">
          <img 
            src="/logobg.png"
            alt="background" 
            className="logo-image"
          />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <ErrorFallback 
        error={error} 
        resetErrorBoundary={resetError} 
      />
    );
  }

  return (
    <div className={`app-container ${isDarkMode ? 'dark' : 'light'}`}>
      <Suspense fallback={<div className="loading-spinner">Loading...</div>}>
        {currentScreen === 'login' && (
          <LoginPage 
            onLoginSuccess={handleLoginSuccess}
            isDarkMode={isDarkMode}
            toggleTheme={toggleTheme}
            onError={handleError}
          />
        )}
        
        {currentScreen === 'landing' && (
          <LandingPage 
            onCreateTimetable={handleCreateTimetable}
            onViewTimetables={handleViewTimetables}
            isDarkMode={isDarkMode}
            toggleTheme={toggleTheme}
            onError={handleError}
            onLogout={handleLogout}
            onPasswordChange={handlePasswordChange}
          />
        )}
        
        {currentScreen === 'create-timetable' && (
          <CreateTimetable 
            onBack={handleBack}
            isDarkMode={isDarkMode}
            toggleTheme={toggleTheme}
            onGenerateTimetable={handleGenerateTimetable}
            onError={handleError}
          />
        )}

        {currentScreen === 'generate-timetable' && (
          <GenerateTimetable 
            onBack={handleBack}
            isDarkMode={isDarkMode}
            toggleTheme={toggleTheme}
            onError={handleError}
          />
        )}

        {currentScreen === 'saved-timetables' && (
          <SavedTimetables
            onBack={handleBack}
            isDarkMode={isDarkMode}
            toggleTheme={toggleTheme}
            onViewTimetable={handleViewSpecificTimetable}
            onError={handleError}
          />
        )}

        {currentScreen === 'view-timetables' && (
          <ViewTimetablesPage 
            onBack={handleBack}
            isDarkMode={isDarkMode}
            toggleTheme={toggleTheme}
            timetableSchema={selectedTimetableSchema}
            onError={handleError}
          />
        )}
      </Suspense>
    </div>
  );
}

export default App;