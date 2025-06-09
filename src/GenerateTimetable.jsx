import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './GenerateTimetable.css';

const GenerateTimetable = ({ onBack, isDarkMode, toggleTheme }) => {
  // State for file uploads
  const [files, setFiles] = useState({
    faculty: null,
    subjects: null,
    venues: null,
    cdc: null
  });

  // State for section configuration
  const [sectionCounts, setSectionCounts] = useState({
    1: 26, // Default values
    2: 26,
    3: 26
  });

  // State for upload status and validation
  const [uploadStatus, setUploadStatus] = useState({
    faculty: false,
    subjects: false,
    venues: false,
    cdc: false
  });

  // State for timetable generation
  const [generationStatus, setGenerationStatus] = useState(null);
  const [isGenerateButtonEnabled, setIsGenerateButtonEnabled] = useState(false);
  const [timetableData, setTimetableData] = useState(null);
  const [validationResults, setValidationResults] = useState(null);

  // Typing effect for title
  const [isTyping, setIsTyping] = useState(false);
  const [typedText, setTypedText] = useState('');
  const fullText = "Upload Files to Generate Timetable";

  // Backend URL (adjust as needed)
  const BACKEND_URL = 'https://timetable-backend-tz59.onrender.com'; // Assuming FastAPI runs on port 8000

  // Typing effect hook
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

  // Handle file upload
  const handleFileUpload = (event, fileType) => {
    const file = event.target.files[0];
    
    // Validate file type
    const allowedTypes = [
      'text/csv', 
      'application/vnd.ms-excel', 
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ];
    
    if (!allowedTypes.includes(file.type)) {
      alert('Please upload a valid CSV or Excel file');
      return;
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      alert('File size should not exceed 10MB');
      return;
    }

    // Update files state
    setFiles(prevFiles => ({
      ...prevFiles,
      [fileType]: file
    }));

    // Update upload status
    setUploadStatus(prevStatus => ({
      ...prevStatus,
      [fileType]: true
    }));

    // Check if all files are uploaded
    const allFilesUploaded = Object.values({
      ...files,
      [fileType]: file
    }).every(f => f !== null);

    setIsGenerateButtonEnabled(allFilesUploaded);
  };
  // Handle timetable generation
  const handleGenerateTimetable = async () => {
  // Validate all files are uploaded
  const allFilesUploaded = Object.values(files).every(file => file !== null);
  
  if (!allFilesUploaded) {
    alert('Please upload all required files');
    return;
  }

  // Convert section counts to letter arrays
  const sectionConfig = Object.entries(sectionCounts).reduce((acc, [year, count]) => {
    acc[year] = Array.from({ length: count }, (_, i) => 
      String.fromCharCode(65 + i)
    );
    return acc;
  }, {});

  // Prepare form data for upload
  const formData = new FormData();
  Object.keys(files).forEach(fileType => {
    formData.append(fileType, files[fileType]);
  });
  
  // Add section configuration to formData
  formData.append('sectionConfig', JSON.stringify(sectionConfig));
  
  try {
    setGenerationStatus('Generating timetables...');

    // Update endpoint path to the FastAPI generate endpoint
    const response = await axios.post(`${BACKEND_URL}/api/generate-timetable`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setGenerationStatus(`Uploading: ${percentCompleted}%`);
      },
      timeout: 600000 // Increased timeout for generation and save (10 minutes)
    });

      // Handle successful generation and saving (as backend does both now)
      if (response.data.status === 'success') {
        setGenerationStatus(response.data.message || 'Timetables generated and saved successfully!');
        // The backend response structure might change, adjust these lines if needed
        // based on what your FastAPI /api/generate-timetable endpoint returns.
        // If it returns timetable data and validation results, you can set them here.
        setTimetableData(response.data.timetables);
        setValidationResults(response.data.validation);
      } else {
        setGenerationStatus('Timetable generation and saving failed');
        alert(response.data.message || 'Failed to generate and save timetables');
        setTimetableData(null);
        setValidationResults(null);
      }
    } catch (error) {
      if (error.response) {
        setGenerationStatus(`Error: ${error.response.data.message || 'Server error'}`);
        alert(`Generation Error: ${error.response.data.message}`);
      } else if (error.request) {
        setGenerationStatus('No response from server. Please check your connection.');
        alert('No response from server. Check your connection and try again.');
      } else {
        setGenerationStatus('Error setting up the request');
        alert('Error setting up the timetable generation request');
      }
      console.error('Timetable generation error:', error);
 setTimetableData(null);
    }
  };

  // Render file upload section
  const renderFileUploader = (fileType, label) => (
    <div className="file-upload-container">
      <input 
        type="file" 
        id={`${fileType}-upload`}
        accept=".csv,.xlsx,.xls"
        onChange={(e) => handleFileUpload(e, fileType)}
        className="file-input"
      />
      <label 
        htmlFor={`${fileType}-upload`} 
        className={`file-upload-label ${uploadStatus[fileType] ? 'uploaded' : ''}`}
      >
        {uploadStatus[fileType] ? '✓ ' : ''}
        Upload {label} File
      </label>
      {files[fileType] && (
        <span className="file-name">{files[fileType].name}</span>
      )}
    </div>
  );

  // Render section configuration
  const renderSectionConfig = () => (
    <div className="section-config">
      <h2>Configure Sections</h2>
      <div className="section-inputs">
        {[1, 2, 3].map(year => (
          <div key={year} className="year-section">
            <label htmlFor={`year-${year}-sections`}>
              Year {year} Sections
            </label>
            <div className="input-with-controls">
              <button 
                className="control-button"
                onClick={() => setSectionCounts(prev => ({
                  ...prev,
                  [year]: Math.max(1, prev[year] - 1)
                }))}
                disabled={sectionCounts[year] <= 1}
              >
                -
              </button>
              <input
                type="number"
                id={`year-${year}-sections`}
                min="1"
                max="26"
                value={sectionCounts[year]}
                onChange={(e) => {
                  const value = Math.min(26, Math.max(1, parseInt(e.target.value) || 1));
                  setSectionCounts(prev => ({
                    ...prev,
                    [year]: value
                  }));
                }}
              />
              <button 
                className="control-button"
                onClick={() => setSectionCounts(prev => ({
                  ...prev,
                  [year]: Math.min(26, prev[year] + 1)
                }))}
                disabled={sectionCounts[year] >= 26}
              >
                +
              </button>
            </div>
            <span className="section-preview">
              Sections: {Array.from({ length: sectionCounts[year] }, (_, i) => 
                String.fromCharCode(65 + i)
              ).join(', ')}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
    // Render validation results
  const renderValidationResults = () => {
    if (!validationResults) return null;

    return (
      <div className="validation-results">
        <h2>Validation Results</h2>
        
        {/* Venue Clashes */}
        <div className="venue-clashes">
          <h3>Venue Clashes</h3>
          {validationResults.venue_clashes.has_clashes ? (
            <div className="clash-details">
              <p className="error">Venue Clashes Detected!</p>
              {validationResults.venue_clashes.clash_details.map((clash, index) => (
                <div key={index} className="clash-item">
                  <p>Venue: {clash.venue}</p>
                  <p>Day: {clash.day}</p>
                  <p>Slot: {clash.slot}</p>
                  <p>Conflicting Classes: {clash.classes.join(', ')}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="success">No Venue Clashes Detected</p>
          )}
        </div>

        {/* Subject Hours Validation */}
        <div className="subject-hours">
          <h3>Subject Hours Validation</h3>
          {Object.entries(validationResults.subject_hours).map(([sectionKey, subjects]) => (
            <div key={sectionKey} className="section-validation">
              <h4>{sectionKey}</h4>
              {Object.entries(subjects).map(([subjectCode, details]) => (
                <div key={subjectCode} className="subject-validation">
                  <p>
                    Subject: {subjectCode}
                    {details.is_valid ? (
                      <span className="success"> ✓ Valid</span>
                    ) : (
                      <span className="error"> ✗ Invalid</span>
                    )}
                  </p>
                  <p>Required Hours: {details.required_hours}</p>
                  <p>Allocated Hours: {details.allocated_hours}</p>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Render timetable preview
  const renderTimetablePreview = () => {
    if (!timetableData) return null;

    return (
      <div className="timetable-preview">
        <h2>Timetable Preview</h2>
        {Object.entries(timetableData).map(([sectionKey, timetable]) => (
          <div key={sectionKey} className="section-timetable">
            <h3>{sectionKey}</h3>
            <pre>{JSON.stringify(timetable, null, 2)}</pre>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className={`generate-timetable-container ${isDarkMode ? 'dark' : 'light'}`}>
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

        {/* Section Configuration */}
        {renderSectionConfig()}

        {/* File Upload Section */}
        <div className="file-upload-section">
          {renderFileUploader('faculty', 'Faculty')}
          {renderFileUploader('subjects', 'Subjects')}
          {renderFileUploader('venues', 'Venues')}
          {renderFileUploader('cdc', 'CDC')}
        </div>

        {/* Generation Status */}
        {generationStatus && (
          <div className="generation-status">
            <p className={`status-message ${generationStatus.includes('failed') ? 'error' : 'success'}`}>
              {generationStatus}
            </p>
          </div>
        )}

        {/* Generate Button */}
        <div className="buttons-container">
          <button 
            className="action-button generate"
            onClick={handleGenerateTimetable}
            disabled={!isGenerateButtonEnabled}
          >
            Create Timetable
            <div className="button-glow"></div>
          </button>
        </div>

        {/* Validation Results */}
        {validationResults && renderValidationResults()}

        {/* Timetable Preview */}
        {timetableData && renderTimetablePreview()}
      </main>
    </div>
  );
};

export default GenerateTimetable;