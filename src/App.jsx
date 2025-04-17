import React, { useState, useEffect, Suspense, lazy } from 'react';
import './App.css';

// Lazy load components for better performance
const LoginPage = lazy(() => import('./LoginPage'));
const LandingPage = lazy(() => import('./LandingPage'));
const CreateTimetable = lazy(() => import('./CreateTimetable'));
const GenerateTimetable = lazy(() => import('./GenerateTimetable'));
const ViewTimetablesPage = lazy(() => import('./ViewTimetablesPage'));

// Error Boundary Component
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

  useEffect(() => {
    // Initial loading screen
    const loadingTimer = setTimeout(() => {
      setIsLoading(false);
      setCurrentScreen('login');
    }, 4000);

    // Load theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      setIsDarkMode(savedTheme === 'dark');
    }

    return () => clearTimeout(loadingTimer);
  }, []);

  // Handle theme changes
  useEffect(() => {
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
    document.body.className = isDarkMode ? 'dark' : 'light';
  }, [isDarkMode]);

  // Error handling method
  const handleError = (error) => {
    console.error('Unhandled error:', error);
    setError(error);
  };

  const handleLoginSuccess = () => {
    setIsLoggedIn(true);
    setCurrentScreen('landing');
  };

  const handleCreateTimetable = () => {
    setCurrentScreen('create-timetable');
  };

  const handleGenerateTimetable = () => {
    setCurrentScreen('generate-timetable');
  };

  const handleViewTimetables = () => {
    setCurrentScreen('view-timetables');
  };

  const handleBack = () => {
    setCurrentScreen('landing');
  };

  const toggleTheme = () => {
    setIsDarkMode(prevMode => {
      const newMode = !prevMode;
      localStorage.setItem('theme', newMode ? 'dark' : 'light');
      return newMode;
    });
  };

  // Reset error state
  const resetError = () => {
    setError(null);
  };

  // Loading Screen
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

  // Error Handling
  if (error) {
    return (
      <ErrorFallback 
        error={error} 
        resetErrorBoundary={resetError} 
      />
    );
  }

  // Screen Navigation
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

        {currentScreen === 'view-timetables' && (
          <ViewTimetablesPage 
            onBack={handleBack}
            isDarkMode={isDarkMode}
            toggleTheme={toggleTheme}
            onError={handleError}
          />
        )}
      </Suspense>
    </div>
  );
}

export default App;