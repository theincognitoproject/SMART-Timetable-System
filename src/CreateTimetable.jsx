import React, { useState, useEffect } from 'react';
import './CreateTimetable.css';
import DepartmentPopup from './DepartmentPopup';
import TablePopup from './TablePopup';
import Toast from './Toast';
import axiosInstance from './utils/axiosConfig';

const CreateTimetable = ({ 
  onBack, 
  isDarkMode, 
  toggleTheme, 
  onGenerateTimetable 
}) => {
  const [isTyping, setIsTyping] = useState(false);
  const [typedText, setTypedText] = useState('');
  const [showPopup, setShowPopup] = useState(false);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showTablePopup, setShowTablePopup] = useState(false);
  const [selectedDepartment, setSelectedDepartment] = useState('');
  const [tableData, setTableData] = useState([]);
  const [loadingTable, setLoadingTable] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [toastType, setToastType] = useState('success');
  const [selectedDepartments, setSelectedDepartments] = useState([]);

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

  // Fetch departments on component mount
  useEffect(() => {
    fetchDepartments();
  }, []);

  const fetchDepartments = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await axiosInstance.get('/schemas');
      
      if (response.data.success) {
        setDepartments(response.data.schemas);
      } else {
        setError('Failed to fetch departments');
      }
    } catch (error) {
      console.error('Error fetching departments:', error);
      setError('Error fetching departments. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDepartment = () => {
    setShowPopup(true);
  };

  const handleCloseDepartment = () => {
    setShowPopup(false);
  };

  const handleDepartmentCreated = (departmentName) => {
    // Show success toast
    setToastMessage(`Department "${departmentName}" created successfully!`);
    setToastType('success');
    setShowToast(true);
    
    // Refresh departments list
    fetchDepartments();
  };

  const handleViewTable = async (departmentName) => {
    try {
      setSelectedDepartment(departmentName);
      setLoadingTable(true);
      
      console.log(`Fetching table data for ${departmentName}`);
      const response = await axiosInstance.get(`/schema/${departmentName}/sortedtable`);
      
      if (response.data.success) {
        setTableData(response.data.data);
        setShowTablePopup(true);
      } else {
        console.error(`Failed to fetch table data: ${response.data.error}`);
        setToastMessage(`Failed to fetch table data for ${departmentName}: ${response.data.error}`);
        setToastType('error');
        setShowToast(true);
      }
    } catch (error) {
      console.error('Error fetching table data:', error);
      const errorMessage = error.response?.data?.error || error.response?.data?.details || error.message;
      setToastMessage(`Error fetching table data for ${departmentName}: ${errorMessage}`);
      setToastType('error');
      setShowToast(true);
    } finally {
      setLoadingTable(false);
    }
  };

  const handleCloseTablePopup = () => {
    setShowTablePopup(false);
    setTableData([]);
  };

  const handleCheckboxChange = (departmentName) => {
    setSelectedDepartments(prev => {
      if (prev.includes(departmentName)) {
        return prev.filter(dep => dep !== departmentName);
      } else {
        return [...prev, departmentName];
      }
    });
  };

  return (
    <div className={`create-timetable-container ${isDarkMode ? 'dark' : 'light'}`}>
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

        <div className="departments-container">
          <div className="departments-list">
            {loading ? (
              <div className="loading-indicator">Loading departments...</div>
            ) : error ? (
              <div className="error-message">{error}</div>
            ) : departments.length === 0 ? (
              <p className="no-departments">
                No departments available. Please create one to generate the timetable.
              </p>
            ) : (
              <table className="departments-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Department Name</th>
                    <th>Actions</th>
                    <th>Select</th>
                  </tr>
                </thead>
                <tbody>
                  {departments.map((department, index) => (
                    <tr key={department}>
                      <td>{index + 1}</td>
                      <td>{department}</td>
                      <td>
                        <button 
                          className="view-table-button"
                          onClick={() => handleViewTable(department)}
                          disabled={loadingTable}
                        >
                          {loadingTable && selectedDepartment === department ? (
                            <span className="button-spinner"></span>
                          ) : (
                            <span className="view-icon">👁️</span>
                          )}
                        </button>
                      </td>
                      <td>
                        <input 
                          type="checkbox" 
                          className="department-checkbox"
                          checked={selectedDepartments.includes(department)}
                          onChange={() => handleCheckboxChange(department)}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <div className="buttons-container">
          <button 
            className="action-button create-dept"
            onClick={handleCreateDepartment}
          >
            Create a new department
            <div className="button-glow"></div>
          </button>

          <button 
            className="action-button generate"
            onClick={onGenerateTimetable}
            disabled={selectedDepartments.length === 0}
          >
            Generate Timetable
            <div className="button-glow"></div>
          </button>
        </div>
      </main>

      {showPopup && (
        <DepartmentPopup
          onClose={handleCloseDepartment}
          onDepartmentCreated={handleDepartmentCreated}
          isDarkMode={isDarkMode}
        />
      )}

      {showTablePopup && (
        <TablePopup
          data={tableData}
          onClose={handleCloseTablePopup}
        />
      )}

      {showToast && (
        <Toast 
          message={toastMessage} 
          type={toastType} 
          duration={2000} 
          onClose={() => setShowToast(false)} 
        />
      )}
    </div>
  );
};

export default CreateTimetable;