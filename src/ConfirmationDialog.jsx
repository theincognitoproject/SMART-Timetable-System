import React from 'react';
import './ConfirmationDialog.css';

const ConfirmationDialog = ({ 
  title, 
  message, 
  onConfirm, 
  onCancel, 
  confirmText = 'Confirm', 
  cancelText = 'Cancel',
  isDarkMode = false
}) => {
  return (
    <div className="confirmation-dialog-overlay">
      <div className={`confirmation-dialog ${isDarkMode ? 'dark' : ''}`}>
        <h3 className="confirmation-title">{title}</h3>
        <p className="confirmation-message">{message}</p>
        <div className="confirmation-buttons">
          <button 
            className="confirmation-button cancel-button" 
            onClick={onCancel}
          >
            {cancelText}
          </button>
          <button 
            className="confirmation-button confirm-button" 
            onClick={onConfirm}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmationDialog;