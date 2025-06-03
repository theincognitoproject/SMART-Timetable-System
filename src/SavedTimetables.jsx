import React, { useState, useEffect } from 'react';
import './SavedTimetables.css';
import Toast from './Toast';
import { fetchTimetableSchemas, deleteTimetableSchema } from './services/timetableService';

const SavedTimetables = ({ onBack, isDarkMode, toggleTheme, onViewTimetable, onError }) => {
  const [isTyping, setIsTyping] = useState(false);
  const [typedText, setTypedText] = useState('');
  const [timetables, setTimetables] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastType, setToastType] = useState('success');
  const [deletingTimetable, setDeletingTimetable] = useState(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const fullText = "Your saved timetables";

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

  // Fetch saved timetables on component mount
  useEffect(() => {
    fetchSavedTimetables();
  }, []);

  const fetchSavedTimetables = async () => {
    try {
      setLoading(true);
      setError('');
      
      const schemas = await fetchTimetableSchemas();
      
      // Sort timetables by creation date (newest first)
      // Assuming schema names are in format timetable_YYYY_MM_DD_HH_MM_SS
      const sortedTimetables = schemas.sort((a, b) => {
        // Extract date parts from schema names
        const getDateFromSchema = (schema) => {
          const parts = schema.split('_');
          if (parts.length >= 7) {
            // Reconstruct as a date string
            return new Date(
              `${parts[1]}-${parts[2]}-${parts[3]}T${parts[4]}:${parts[5]}:${parts[6]}`
            );
          }
          return new Date(0); // Fallback for invalid format
        };
        
        return getDateFromSchema(b) - getDateFromSchema(a);
      });
      
      setTimetables(sortedTimetables);
    } catch (error) {
      console.error('Error fetching saved timetables:', error);
      setError('Error fetching saved timetables. Please try again.');
      if (onError) onError(error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewTimetable = (schemaName) => {
    onViewTimetable(schemaName);
  };

  const handleDeleteTimetable = (schemaName) => {
    setDeletingTimetable(schemaName);
    setShowConfirmDialog(true);
  };

  const confirmDelete = async () => {
    if (!deletingTimetable) return;
    
    try {
      setIsDeleting(true);
      
      const result = await deleteTimetableSchema(deletingTimetable);
      
      setTimetables(prev => prev.filter(schema => schema !== deletingTimetable));
      setToastMessage(`Timetable "${formatTimetableName(deletingTimetable)}" deleted successfully`);
      setToastType('success');
    } catch (error) {
      console.error('Error deleting timetable:', error);
      setToastMessage(`Error deleting timetable: ${error.message}`);
      setToastType('error');
      if (onError) onError(error);
    } finally {
      setIsDeleting(false);
      setShowConfirmDialog(false);
      setShowToast(true);
      setDeletingTimetable(null);
    }
  };

  const cancelDelete = () => {
    setShowConfirmDialog(false);
    setDeletingTimetable(null);
  };

  // Helper function to format timetable schema name for display
  const formatTimetableName = (schemaName) => {
    // Remove 'timetable_' prefix
    let displayName = schemaName.replace('timetable_', '');
    
    // Replace underscores with spaces or better formatting
    const parts = displayName.split('_');
    if (parts.length >= 6) {
      // If it follows the expected date format
      const [year, month, day, hour, minute, second] = parts;
      const date = new Date(
        `${year}-${month}-${day}T${hour}:${minute}:${second}`
      );
      
      // Format as a readable date string
      return date.toLocaleString();
    }
    
    // Fallback for unexpected formats
    return displayName.replace(/_/g, ' ');
  };

  return (
    <div className={`saved-timetables-container ${isDarkMode ? 'dark' : 'light'}`}>
      {/* Header */}
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

        <div className="timetables-container">
          {loading ? (
            <div className="loading-indicator">Loading saved timetables...</div>
          ) : error ? (
            <div className="error-message">{error}</div>
          ) : timetables.length === 0 ? (
            <p className="no-timetables">
              No saved timetables available. Generate a timetable to get started.
            </p>
          ) : (
            <table className="timetables-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Timetable Name</th>
                  <th>Generated On</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {timetables.map((schema, index) => {
                  // Extract date information from schema name
                  const parts = schema.replace('timetable_', '').split('_');
                  let generatedDate = 'Unknown';
                  
                  if (parts.length >= 6) {
                    const [year, month, day, hour, minute, second] = parts;
                    const date = new Date(
                      `${year}-${month}-${day}T${hour}:${minute}:${second}`
                    );
                    generatedDate = date.toLocaleString();
                  }
                  
                  return (
                    <tr key={schema}>
                      <td>{index + 1}</td>
                      <td>{formatTimetableName(schema)}</td>
                      <td>{generatedDate}</td>
                      <td className="action-buttons">
                        <button 
                          className="view-button"
                          onClick={() => handleViewTimetable(schema)}
                        >
                          <span className="button-icon">👁️</span>
                          <span className="button-text">View</span>
                        </button>
                        <button 
                          className="delete-button"
                          onClick={() => handleDeleteTimetable(schema)}
                          disabled={isDeleting}
                        >
                          <span className="button-icon">🗑️</span>
                          <span className="button-text">Delete</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </main>

      {/* Confirmation Dialog */}
      {showConfirmDialog && (
        <div className="confirmation-dialog-overlay">
          <div className="confirmation-dialog">
            <h3>Confirm Deletion</h3>
            <p>Are you sure you want to delete this timetable?</p>
            <p className="warning-text">This action cannot be undone.</p>
            <div className="dialog-buttons">
              <button 
                className="cancel-button"
                onClick={cancelDelete}
                disabled={isDeleting}
              >
                Cancel
              </button>
              <button 
                className="confirm-button"
                onClick={confirmDelete}
                disabled={isDeleting}
              >
                {isDeleting ? (
                  <>
                    <span className="button-spinner"></span>
                    Deleting...
                  </>
                ) : (
                  "Yes, Delete"
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notification */}
      {showToast && (
        <Toast 
          message={toastMessage} 
          type={toastType} 
          duration={3000} 
          onClose={() => setShowToast(false)} 
        />
      )}
    </div>
  );
};

export default SavedTimetables;