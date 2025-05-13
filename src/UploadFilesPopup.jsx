import React, { useState, useRef } from 'react';
import './UploadFilesPopup.css';
import { AllocationService } from './utils/axiosConfig';
import Toast from './Toast';

const UploadFilesPopup = ({ onClose, isDarkMode, departmentName }) => {
  const [uploadedFiles, setUploadedFiles] = useState({
    'faculty-pref': null,
    'faculty-list': null,
    'first-year': null,
    'second-year': null,
    'third-year': null,
    'fourth-year': null
  });

  const [errorMessage, setErrorMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState('');
  const [processingStatus, setProcessingStatus] = useState('');
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastType, setToastType] = useState('success');

  const fileInputRefs = {
    'faculty-pref': useRef(),
    'faculty-list': useRef(),
    'first-year': useRef(),
    'second-year': useRef(),
    'third-year': useRef(),
    'fourth-year': useRef()
  };

  const uploadBoxes = [
    { id: 'faculty-pref', label: 'Faculty Preferences' },
    { id: 'faculty-list', label: 'Faculty List' },
    { id: 'first-year', label: 'First Year' },
    { id: 'second-year', label: 'Second Year' },
    { id: 'third-year', label: 'Third Year' },
    { id: 'fourth-year', label: 'Fourth Year' },
  ];

  const handleBoxClick = (id) => {
    fileInputRefs[id].current.click();
  };

  const handleFileUpload = (id, event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.type !== 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' && 
          file.type !== 'application/vnd.ms-excel' &&
          file.type !== 'text/csv') {
        alert('Please upload only Excel or CSV files');
        return;
      }
      setUploadedFiles(prev => ({
        ...prev,
        [id]: file
      }));
      setErrorMessage(''); // Clear error message when a file is uploaded
    }
  };

  const handleRemoveFile = (id, event) => {
    event.stopPropagation();
    setUploadedFiles(prev => ({
      ...prev,
      [id]: null
    }));
    fileInputRefs[id].current.value = '';
  };

  const validateFiles = () => {
    // Check if both faculty files are uploaded
    const hasFacultyFiles = uploadedFiles['faculty-pref'] && uploadedFiles['faculty-list'];
    
    // Check if at least one year file is uploaded (first, second, or third year)
    const hasYearFile = uploadedFiles['first-year'] || 
                       uploadedFiles['second-year'] || 
                       uploadedFiles['third-year'];
  
    if (!hasFacultyFiles || !hasYearFile) {
      setErrorMessage('⚠️ Please ensure you have uploaded both faculty files and at least one year file (first, second, or third year) to proceed.');
      return false;
    }
    
    setErrorMessage('');
    return true;
  };
  
  const handleCreate = async () => {
    if (!validateFiles()) {
      return;
    }
    
    setIsProcessing(true);
    setErrorMessage('');
    
    try {
      // First process year files (bottom row)
      const yearFilesSuccess = await processYearFiles();
      
      if (!yearFilesSuccess) {
        setIsProcessing(false);
        setToastType('error');
        setToastMessage('Failed to process year files');
        setShowToast(true);
        return;
      }
      
      // Then process faculty files (top row)
      const facultyFilesSuccess = await processFacultyFiles();
      
      if (!facultyFilesSuccess) {
        setIsProcessing(false);
        setToastType('error');
        setToastMessage('Failed to process faculty files');
        setShowToast(true);
        return;
      }
      
      // Both processes completed successfully
      setProcessingStep('Complete');
      setProcessingStatus('Timetable allocation completed successfully!');
      
      // Show success toast and close popup
      setToastType('success');
      setToastMessage(`Department "${departmentName}" created successfully!`);
      setShowToast(true);
      
      // Close the popup after a delay
      setTimeout(() => {
        onClose();
      }, 2000);
      
    } catch (error) {
      console.error('Error during processing:', error);
      setErrorMessage('An unexpected error occurred. Please try again.');
      setIsProcessing(false);
      setToastType('error');
      setToastMessage('An unexpected error occurred');
      setShowToast(true);
    }
  };
  
  const processFacultyFiles = async () => {
    try {
      const formData = new FormData();
      formData.append('department_name', departmentName);
      
      // Ensure both faculty files are added
      if (!uploadedFiles['faculty-list']) {
        setErrorMessage('Faculty List file is required');
        return false;
      }
      
      if (!uploadedFiles['faculty-pref']) {
        setErrorMessage('Faculty Preferences file is required');
        return false;
      }
      
      // Append faculty files
      formData.append('faculty_list', uploadedFiles['faculty-list']);
      formData.append('faculty_preferences', uploadedFiles['faculty-pref']);
      
      // Send request to process faculty files
      const response = await AllocationService.processFacultyFiles(formData);
      
      if (response.data.success) {
        setProcessingStatus('Faculty files processed successfully');
        
        // Log additional details
        console.log('Faculty Processing Details:', response.data.details);
        
        return true;
      } else {
        // Processing failed
        const errorMessage = response.data.details?.stderr || 
                             response.data.details?.stdout || 
                             'Failed to process faculty files';
        
        setProcessingStatus('Error processing faculty files');
        setErrorMessage(errorMessage);
        
        // Log detailed error information
        console.error('Faculty Files Processing Error:', response.data);
        
        return false;
      }
    } catch (error) {
      console.error('Error processing faculty files:', error);
      setProcessingStatus('Error processing faculty files');
      
      // More detailed error logging
      if (error.response) {
        console.error('Response data:', error.response.data);
        console.error('Response status:', error.response.status);
        console.error('Response headers:', error.response.headers);
      }
      
      setErrorMessage(error.response?.data?.detail || 'An unexpected error occurred');
      return false;
    }
  };
  
  const processYearFiles = async () => {
    try {
      const formData = new FormData();
      formData.append('department_name', departmentName);
      
      // Add year files
      const yearFiles = [
        { id: 'first-year', file: uploadedFiles['first-year'] },
        { id: 'second-year', file: uploadedFiles['second-year'] },
        { id: 'third-year', file: uploadedFiles['third-year'] },
        { id: 'fourth-year', file: uploadedFiles['fourth-year'] }
      ].filter(item => item.file !== null);
      
      // Validate at least one year file is uploaded
      if (yearFiles.length === 0) {
        setErrorMessage('Please upload at least one year file (first, second, or third year)');
        return false;
      }
      
      // Append files to FormData
      yearFiles.forEach(item => {
        formData.append('files', item.file);
      });
      
      // Send request to process year files
      const response = await AllocationService.processYearFiles(formData);
      
      if (response.data.success) {
        setProcessingStatus('Year files processed successfully');
        
        // Log additional details if available
        if (response.data.details) {
          console.log('Year Processing Details:', response.data.details);
        }
        
        return true;
      } else {
        // Processing failed
        const errorMessage = 'Failed to process year files';
        
        setProcessingStatus('Error processing year files');
        setErrorMessage(errorMessage);
        
        // Log detailed error information
        console.error('Year Files Processing Error:', response.data);
        
        return false;
      }
    } catch (error) {
      console.error('Error processing year files:', error);
      setProcessingStatus('Error processing year files');
      
      // More detailed error logging
      if (error.response) {
        console.error('Response data:', error.response.data);
        console.error('Response status:', error.response.status);
        console.error('Response headers:', error.response.headers);
      }
      
      setErrorMessage(error.response?.data?.detail || 'An unexpected error occurred');
      return false;
    }
  };

  return (
    <>
      <div className="upload-popup-overlay">
        <div className={`upload-popup-content ${isDarkMode ? 'dark' : 'light'}`}>
          <button className="close-button" onClick={onClose} disabled={isProcessing}>
            ×
          </button>
          
          <h2 className="upload-popup-title">
            {isProcessing ? processingStep : 'Upload Files'}
          </h2>
          
          {isProcessing ? (
            <div className="processing-container">
              <div className="loading-spinner"></div>
              <p className="processing-status">{processingStatus}</p>
            </div>
          ) : (
            <>
              <div className="upload-boxes-container">
                <div className="upload-boxes-row">
                  {uploadBoxes.slice(0, 2).map(box => (
                    <div key={box.id} className="upload-box-wrapper">
                      <div 
                        className={`upload-box ${uploadedFiles[box.id] ? 'uploaded' : ''}`}
                        onClick={() => handleBoxClick(box.id)}
                      >
                        {uploadedFiles[box.id] ? (
                          <>
                            <span className="tick-sign">✓</span>
                            <button 
                              className="remove-file"
                              onClick={(e) => handleRemoveFile(box.id, e)}
                            >
                              ×
                            </button>
                          </>
                        ) : (
                          <span className="plus-sign">+</span>
                        )}
                        <input
                          type="file"
                          ref={fileInputRefs[box.id]}
                          accept=".xlsx,.xls,.csv"
                          onChange={(e) => handleFileUpload(box.id, e)}
                          style={{ display: 'none' }}
                        />
                      </div>
                      <span className="box-label">{box.label}</span>
                      {uploadedFiles[box.id] && (
                        <span className="file-name">{uploadedFiles[box.id].name}</span>
                      )}
                    </div>
                  ))}
                </div>
                
                <div className="upload-boxes-row">
                  {uploadBoxes.slice(2).map(box => (
                    <div key={box.id} className="upload-box-wrapper">
                      <div 
                        className={`upload-box ${uploadedFiles[box.id] ? 'uploaded' : ''}`}
                        onClick={() => handleBoxClick(box.id)}
                      >
                        {uploadedFiles[box.id] ? (
                          <>
                            <span className="tick-sign">✓</span>
                            <button 
                              className="remove-file"
                              onClick={(e) => handleRemoveFile(box.id, e)}
                            >
                              ×
                            </button>
                          </>
                        ) : (
                          <span className="plus-sign">+</span>
                        )}
                        <input
                          type="file"
                          ref={fileInputRefs[box.id]}
                          accept=".xlsx,.xls,.csv"
                          onChange={(e) => handleFileUpload(box.id, e)}
                          style={{ display: 'none' }}
                        />
                      </div>
                      <span className="box-label">{box.label}</span>
                      {uploadedFiles[box.id] && (
                        <span className="file-name">{uploadedFiles[box.id].name}</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {errorMessage && (
                <div className="error-message">
                  {errorMessage}
                </div>
              )}

              <button 
                className="create-button"
                onClick={handleCreate}
                disabled={isProcessing}
              >
                Create
              </button>
            </>
          )}
        </div>
      </div>
      
      {showToast && (
        <Toast 
          message={toastMessage} 
          type={toastType} 
          duration={2000} 
          onClose={() => setShowToast(false)} 
        />
      )}
    </>
  );
};

export default UploadFilesPopup;