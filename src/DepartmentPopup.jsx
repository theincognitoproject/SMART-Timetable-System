import React, { useState } from 'react';
import './DepartmentPopup.css';
import UploadFilesPopup from './UploadFilesPopup';
import { SchemaService } from './utils/axiosConfig';
import Toast from './Toast'; // Assuming you have a Toast component

const DepartmentPopup = ({ onClose, isDarkMode, onDepartmentCreated }) => {
  const [departmentName, setDepartmentName] = useState('');
  const [showUploadPopup, setShowUploadPopup] = useState(false);
  const [error, setError] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  
  // Toast state
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastType, setToastType] = useState('success');

  const validateDepartmentName = async () => {
    try {
      setIsValidating(true);
      
      // Fetch available schemas to check for duplicate
      const { data } = await SchemaService.getSchemas();
      
      // Check if department name already exists
      const existingSchemas = data.schemas || [];
      if (existingSchemas.some(schema => 
        schema.toLowerCase() === departmentName.trim().toLowerCase()
      )) {
        setError('Department name already exists');
        return false;
      }
      
      return true;
    } catch (error) {
      console.error('Department validation error:', error);
      
      // Show error toast
      setToastMessage('Unable to validate department name. Please try again.');
      setToastType('error');
      setShowToast(true);
      
      return false;
    } finally {
      setIsValidating(false);
    }
  };

  const handleSubmit = async () => {
    // Reset previous errors
    setError('');
    setShowToast(false);

    // Trim the department name
    const trimmedName = departmentName.trim();

    // Basic client-side validations
    if (!trimmedName) {
      setError('Please enter a department name');
      return;
    }
    
    // Validate department name (alphanumeric and underscores only)
    const departmentNameRegex = /^[a-zA-Z0-9_]+$/;
    if (!departmentNameRegex.test(trimmedName)) {
      setError('Department name can only contain letters, numbers, and underscores');
      return;
    }

    // Validate department name uniqueness
    const isValid = await validateDepartmentName();
    if (!isValid) {
      return;
    }
    
    // Proceed to upload popup
    setShowUploadPopup(true);
  };

  const handleUploadComplete = () => {
    // Notify parent component that a department was created
    if (onDepartmentCreated) {
      onDepartmentCreated(departmentName);
    }
    
    // Show success toast
    setToastMessage(`Department "${departmentName}" created successfully`);
    setToastType('success');
    setShowToast(true);
    
    // Close popup after a short delay
    setTimeout(onClose, 2000);
  };

  const handleKeyPress = (e) => {
    // Allow submission on Enter key
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <>
      <div className="popup-overlay">
        <div className={`popup-content ${isDarkMode ? 'dark' : 'light'}`}>
          <button 
            className="close-button" 
            onClick={onClose}
            disabled={isValidating}
          >
            ×
          </button>
          
          <h2 className="popup-title">Enter Department Name</h2>
          
          <input
            type="text"
            value={departmentName}
            onChange={(e) => {
              setDepartmentName(e.target.value);
              setError(''); // Clear error when typing
            }}
            onKeyPress={handleKeyPress}
            className="department-input"
            placeholder="Department Name"
            autoFocus
            disabled={isValidating}
            maxLength={50}
          />
          
          {error && <p className="error-message">{error}</p>}
          
          <button 
            className="proceed-button"
            onClick={handleSubmit}
            disabled={isValidating}
          >
            {isValidating ? 'Validating...' : 'Proceed'}
          </button>
        </div>
      </div>

      {showUploadPopup && (
        <UploadFilesPopup
          onClose={handleUploadComplete}
          isDarkMode={isDarkMode}
          departmentName={departmentName}
        />
      )}

      {showToast && (
        <Toast
          message={toastMessage}
          type={toastType}
          duration={3000}
          onClose={() => setShowToast(false)}
        />
      )}
    </>
  );
};

export default DepartmentPopup;