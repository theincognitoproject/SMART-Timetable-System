import React, { useState, useEffect } from 'react';
import './CreateTimetable.css';
import DepartmentPopup from './DepartmentPopup';
import TablePopup from './TablePopup';
import Toast from './Toast';
import ConfirmationDialog from './ConfirmationDialog';
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
  const [isDownloading, setIsDownloading] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [departmentToDelete, setDepartmentToDelete] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

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

  const handleDeleteClick = (departmentName) => {
    setDepartmentToDelete(departmentName);
    setShowConfirmDialog(true);
  };

  const handleConfirmDelete = async () => {
    try {
      setIsDeleting(true);
      setShowConfirmDialog(false);
      
      const response = await axiosInstance.delete(`/department/${departmentToDelete}`);
      
      if (response.data.success) {
        // Remove the department from selected departments if it was selected
        setSelectedDepartments(prev => prev.filter(dep => dep !== departmentToDelete));
        
        // Show success toast
        setToastMessage(`Department "${departmentToDelete}" deleted successfully!`);
        setToastType('success');
        setShowToast(true);
        
        // Refresh departments list
        fetchDepartments();
      } else {
        throw new Error(response.data.message || 'Failed to delete department');
      }
    } catch (error) {
      console.error('Error deleting department:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to delete department';
      setToastMessage(`Error: ${errorMessage}`);
      setToastType('error');
      setShowToast(true);
    } finally {
      setIsDeleting(false);
      setDepartmentToDelete('');
    }
  };

  const handleCancelDelete = () => {
    setShowConfirmDialog(false);
    setDepartmentToDelete('');
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

  // Helper function to remove duplicates from UniqueSubjects data
  const removeDuplicateSubjects = (data) => {
    if (!data || !Array.isArray(data) || data.length === 0) {
      return [];
    }
    
    const uniqueMap = new Map();
    
    // Process each row to extract subject code
    data.forEach(row => {
      // If data is an array of objects (from API response)
      if (typeof row === 'object' && !Array.isArray(row)) {
        const values = Object.values(row);
        // Assuming subject code is in the second column
        if (values.length > 1 && values[1]) {
          const subjectCode = values[1];
          if (!uniqueMap.has(subjectCode)) {
            uniqueMap.set(subjectCode, row);
          }
        }
      } 
      // If data is an array of arrays (manually constructed)
      else if (Array.isArray(row)) {
        if (row.length > 1 && row[1]) {
          const subjectCode = row[1];
          if (!uniqueMap.has(subjectCode)) {
            uniqueMap.set(subjectCode, row);
          }
        }
      }
    });
    
    return Array.from(uniqueMap.values());
  };

  // Helper function to convert JSON data to CSV and download
  const downloadCSV = (data, filename) => {
    try {
      // Handle empty data
      if (!data || data.length === 0) {
        console.warn('No data to download');
        return false;
      }

      // Determine headers and format data
      let csvContent = '';
      
      // If data is an array of objects
      if (typeof data[0] === 'object' && !Array.isArray(data[0])) {
        const headers = Object.keys(data[0]);
        
        // Add header row
        csvContent += headers.join(',') + '\n';
        
        // Add data rows
        csvContent += data.map(row => {
          return headers.map(header => {
            const value = row[header];
            if (value === null || value === undefined) return '';
            
            // Handle special characters to maintain CSV format
            if (typeof value === 'string') {
              // Escape quotes and wrap fields containing commas or newlines in quotes
              if (value.includes('"') || value.includes(',') || value.includes('\n')) {
                return `"${value.replace(/"/g, '""')}"`;
              }
              return value;
            }
            return value;
          }).join(',');
        }).join('\n');
      } 
      // If data is an array of arrays
      else if (Array.isArray(data[0])) {
        // Convert each row to CSV format
        csvContent = data.map(row => {
          return row.map(value => {
            if (value === null || value === undefined) return '';
            
            // Handle special characters
            if (typeof value === 'string') {
              if (value.includes('"') || value.includes(',') || value.includes('\n')) {
                return `"${value.replace(/"/g, '""')}"`;
              }
              return value;
            }
            return value;
          }).join(',');
        }).join('\n');
      }
      
      // Create blob and trigger download
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      return true;
    } catch (error) {
      console.error('Error creating CSV file:', error);
      return false;
    }
  };

  // Use a different approach to handle the download
  const fetchTableData = async (department, tableName) => {
    try {
      // Make the API endpoint all lowercase to match the backend
      const endpoint = `/schema/${department}/${tableName.toLowerCase()}`;
      console.log(`Fetching data from: ${endpoint}`);
      
      const response = await axiosInstance.get(endpoint);
      
      if (response.data.success && response.data.data) {
        return { success: true, data: response.data.data };
      } else {
        console.warn(`No data from ${endpoint}`);
        return { success: false, error: response.data.error || 'No data returned' };
      }
    } catch (error) {
      console.error(`Error fetching ${tableName} for ${department}:`, error);
      return { 
        success: false, 
        error: error.response?.data?.detail || error.message 
      };
    }
  };

    const handleDownload = async () => {
    // Check if any departments are selected
    if (selectedDepartments.length === 0) {
      setToastMessage("Please select at least one department to download.");
      setToastType('error');
      setShowToast(true);
      return;
    }

    setIsDownloading(true);

    try {
      // Arrays to store merged data
      let allSortedTableFormattedData = [];
      let allUniqueSubjectsData = [];
      let errorDepartments = [];
      let successCount = 0;
      
      // Process each selected department
      for (const department of selectedDepartments) {
        try {
          console.log(`Processing department: ${department}`);
          
          // Try to fetch SortedTableFormatted data
          const formattedResult = await fetchTableData(department, 'sortedtableformatted');
          
          // Try to fetch UniqueSubjects data
          const uniqueResult = await fetchTableData(department, 'uniquesubjects');
          
          // If either request was successful, count as success
          let departmentSuccess = false;
          
          if (formattedResult.success) {
            allSortedTableFormattedData = [...allSortedTableFormattedData, ...formattedResult.data];
            departmentSuccess = true;
          }
          
          if (uniqueResult.success) {
            allUniqueSubjectsData = [...allUniqueSubjectsData, ...uniqueResult.data];
            departmentSuccess = true;
          }
          
          if (departmentSuccess) {
            successCount++;
          } else {
            // If both requests failed, add to error list
            errorDepartments.push(department);
          }
          
        } catch (error) {
          console.error(`Error processing department ${department}:`, error);
          errorDepartments.push(department);
        }
      }
      
      // Remove duplicates from UniqueSubjects data
      const uniqueSubjectsWithoutDuplicates = removeDuplicateSubjects(allUniqueSubjectsData);
      
      // Download files if we have data
      let downloadSuccess = false;
      
      if (allSortedTableFormattedData.length > 0) {
        const success = downloadCSV(
          allSortedTableFormattedData, 
          `SortedTableFormatted_${selectedDepartments.join('_')}.csv`
        );
        downloadSuccess = success;
      }
      
      if (uniqueSubjectsWithoutDuplicates.length > 0) {
        const success = downloadCSV(
          uniqueSubjectsWithoutDuplicates, 
          `UniqueSubjects_${selectedDepartments.join('_')}.csv`
        );
        downloadSuccess = downloadSuccess || success;
      }
      
      // Show appropriate toast message
      if (errorDepartments.length === 0 && downloadSuccess) {
        setToastMessage(`Successfully downloaded files for ${selectedDepartments.length} department(s).`);
        setToastType('success');
      } else if (errorDepartments.length === selectedDepartments.length || !downloadSuccess) {
        setToastMessage(`Failed to download files. Please try again.`);
        setToastType('error');
      } else {
        setToastMessage(
          `Downloaded data for ${successCount} out of ${selectedDepartments.length} department(s). ` +
          `Failed for: ${errorDepartments.join(', ')}`
        );
        setToastType('info');
      }
    } catch (error) {
      console.error('Error during download process:', error);
      setToastMessage('An error occurred during the download process.');
      setToastType('error');
    } finally {
      setIsDownloading(false);
      setShowToast(true);
    }
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
                        <div className="action-buttons">
                          <button 
                            className="view-table-button"
                            onClick={() => handleViewTable(department)}
                            disabled={loadingTable || isDeleting}
                            title="View table"
                          >
                            {loadingTable && selectedDepartment === department ? (
                              <span className="button-spinner"></span>
                            ) : (
                              <span className="view-icon">👁️</span>
                            )}
                          </button>
                          <button 
                            className="delete-button"
                            onClick={() => handleDeleteClick(department)}
                            disabled={isDeleting || isDownloading}
                            title="Delete department"
                          >
                            {isDeleting && departmentToDelete === department ? (
                              <span className="button-spinner"></span>
                            ) : (
                              <span className="delete-icon">🗑️</span>
                            )}
                          </button>
                        </div>
                      </td>
                      <td>
                        <input 
                          type="checkbox" 
                          className="department-checkbox"
                          checked={selectedDepartments.includes(department)}
                          onChange={() => handleCheckboxChange(department)}
                          disabled={isDownloading || isDeleting}
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
            disabled={isDownloading || isDeleting}
          >
            Create a new department
            <div className="button-glow"></div>
          </button>

          <button 
            className="action-button download"
            onClick={handleDownload}
            disabled={isDownloading || selectedDepartments.length === 0 || isDeleting}
          >
            {isDownloading ? (
              <>
                <span className="button-spinner"></span> Downloading...
              </>
            ) : (
              <>
                Download
                <div className="button-glow"></div>
              </>
            )}
          </button>

          <button 
            className="action-button generate"
            onClick={onGenerateTimetable}
            disabled={isDownloading || isDeleting}
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
          duration={3000} 
          onClose={() => setShowToast(false)} 
        />
      )}

      {showConfirmDialog && (
        <ConfirmationDialog
          title="Confirm Delete"
          message={`Are you sure you want to delete the department "${departmentToDelete}"? This action cannot be undone.`}
          onConfirm={handleConfirmDelete}
          onCancel={handleCancelDelete}
          confirmText="Delete"
          cancelText="Cancel"
          isDarkMode={isDarkMode}
        />
      )}
    </div>
  );
};

export default CreateTimetable;