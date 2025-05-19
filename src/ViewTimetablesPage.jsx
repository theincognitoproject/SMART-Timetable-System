import React, { useState, useEffect } from 'react';
import { fetchTimetables } from './services/timetableService';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import './ViewTimetablesPage.css';

const PREDEFINED_SLOTS = [
  "8:00-8:50", "8:50-9:40", 
  "BREAK",
  "9:50-10:40", "10:40-11:30", 
  "LUNCH",
  "12:20-1:10", "1:10-2:00", "2:00-2:50", "2:50-3:40"
];

const PREDEFINED_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

const ViewTimetablesPage = ({ onBack, isDarkMode, toggleTheme }) => {
  const [viewType, setViewType] = useState('Class Timetables');
  const [timetableData, setTimetableData] = useState({
    classes: [],
    teachers: [],
    venues: []
  });
  const [selectedTimetables, setSelectedTimetables] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isViewingAll, setIsViewingAll] = useState(false);

  // Fetch timetable data
  const loadTimetableData = async () => {
    try {
      setIsLoading(true);
      const data = await fetchTimetables();
      setTimetableData(data);
      setError(null);
    } catch (err) {
      console.error('Timetable fetch error:', err);
      setError(`Failed to fetch timetables: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTimetableData();
  }, []);

  // Handle View All functionality
  const handleViewAll = () => {
    setIsViewingAll(!isViewingAll);
    
    if (!isViewingAll) {
      let allItems = [];
      switch (viewType) {
        case 'Class Timetables':
          allItems = timetableData.classes.map(cls => ({
            ...cls,
            type: 'section'
          }));
          break;
        case 'Venue Timetables':
          allItems = timetableData.venues.map(venue => ({
            ...venue,
            type: 'venue'
          }));
          break;
        case 'Teacher Timetables':
          allItems = timetableData.teachers.map(teacher => ({
            ...teacher,
            type: 'teacher'
          }));
          break;
        default:
          break;
      }
      setSelectedTimetables(allItems);
    } else {
      setSelectedTimetables([]);
    }
  };

  // Format cell content for display
  const formatCellContent = (cellData, type) => {
    if (!cellData || typeof cellData !== 'object') {
      return cellData || 'FREE';
    }

    switch (type) {
      case 'section':
        return cellData.venue 
          ? `${cellData.code}\n${cellData.teacher}\n${cellData.venue}`
          : `${cellData.code}\n${cellData.teacher}`;
      
      case 'venue':
        return `${cellData.code}\n${cellData.teacher}\n${cellData.year}-${cellData.section}`;
      
      case 'teacher':
        return cellData.venue 
          ? `${cellData.code}\n${cellData.year}-${cellData.section}\n${cellData.venue}`
          : `${cellData.code}\n${cellData.year}-${cellData.section}`;
      
      default:
        return 'FREE';
    }
  };

  // Download timetable as PDF
  const downloadTimetable = (timetableData) => {
    try {
      const { type, ...data } = timetableData;
      
      const timetableTitle = 
        type === 'section' ? `Year ${data.year} - Section ${data.section}` :
        type === 'venue' ? data.venue_name :
        type === 'teacher' ? data.teacher_name : 
        'Timetable';

      const printContainer = document.createElement('div');
      printContainer.style.position = 'absolute';
      printContainer.style.left = '-9999px';
      printContainer.style.width = '100%';
      
      const table = document.createElement('table');
      table.style.width = '100%';
      table.style.borderCollapse = 'collapse';
      table.style.fontSize = '12px';
      table.style.color = '#000000';
      
      // Add title
      const titleRow = table.insertRow();
      const titleCell = titleRow.insertCell();
      titleCell.colSpan = PREDEFINED_DAYS.length + 1;
      titleCell.style.textAlign = 'center';
      titleCell.style.fontWeight = 'bold';
      titleCell.style.fontSize = '16px';
      titleCell.style.color = '#000000';
      titleCell.style.padding = '10px';
      titleCell.textContent = timetableTitle;
      
      // Add header row
      const headerRow = table.insertRow();
      const headerCells = ['Time', ...PREDEFINED_DAYS];
      headerCells.forEach(headerText => {
        const th = document.createElement('th');
        th.textContent = headerText;
        th.style.border = '1px solid #000000';
        th.style.padding = '8px';
        th.style.backgroundColor = '#f0f0f0';
        th.style.color = '#000000';
        th.style.fontWeight = 'bold';
        headerRow.appendChild(th);
      });

      // Add data rows
      PREDEFINED_SLOTS.forEach(slot => {
        const row = table.insertRow();
        
        const timeCell = row.insertCell();
        timeCell.textContent = slot;
        timeCell.style.border = '1px solid #000000';
        timeCell.style.padding = '8px';
        timeCell.style.fontWeight = 'bold';
        timeCell.style.color = '#000000';
        timeCell.style.backgroundColor = '#f8f8f8';

        PREDEFINED_DAYS.forEach(day => {
          const cell = row.insertCell();
          const cellData = data.timetable?.[day]?.[slot];

          cell.textContent = formatCellContent(cellData, type);
          cell.style.border = '1px solid #000000';
          cell.style.padding = '8px';
          cell.style.textAlign = 'center';
          cell.style.color = '#000000';
          cell.style.whiteSpace = 'pre-line';
          cell.style.verticalAlign = 'middle';
      
          if (slot === 'BREAK' || slot === 'LUNCH') {
            cell.style.backgroundColor = '#f0f0f0';
          } else if (cellData) {
            cell.style.backgroundColor = '#ffffff';
          } else {
            cell.style.backgroundColor = '#f8f8f8';
          }
        });
      });

      printContainer.appendChild(table);
      document.body.appendChild(printContainer);

      html2canvas(printContainer, { 
        scale: 3,
        useCORS: true,
        logging: false
      }).then(canvas => {
        const imgData = canvas.toDataURL('image/png');
        const pdf = new jsPDF('landscape');
        
        const imgProps = pdf.getImageProperties(imgData);
        const pdfWidth = pdf.internal.pageSize.getWidth();
        const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;

        pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight, '', 'FAST');
        pdf.save(`${timetableTitle}_Timetable.pdf`);

        document.body.removeChild(printContainer);
      }).catch(error => {
        console.error('HTML to Canvas Error:', error);
        alert('Failed to generate PDF');
      });
    } catch (error) {
      console.error('PDF Download Error:', error);
      alert(`Failed to download PDF: ${error.message}`);
    }
  };

  // Toggle timetable selection
  const toggleTimetableSelection = (type, item) => {
    const newItem = { ...item, type };
    
    const identifier = 
      type === 'section' ? `section-${item.year}-${item.section}` :
      type === 'venue' ? `venue-${item.venue_name}` :
      `teacher-${item.teacher_name}`;

    const isSelected = selectedTimetables.some(
      t => 
        (t.type === 'section' && `section-${t.year}-${t.section}` === identifier) ||
        (t.type === 'venue' && `venue-${t.venue_name}` === identifier) ||
        (t.type === 'teacher' && `teacher-${t.teacher_name}` === identifier)
    );

    if (isSelected) {
      setSelectedTimetables(prev => 
        prev.filter(t => 
          (t.type === 'section' ? `section-${t.year}-${t.section}` : 
           t.type === 'venue' ? `venue-${t.venue_name}` : 
           `teacher-${t.teacher_name}`) !== identifier
        )
      );
    } else {
      setSelectedTimetables(prev => [...prev, newItem]);
    }
  };

  // Render Specific Timetable
  const renderTimetable = (timetableData) => {
    const { type, ...data } = timetableData;
    
    const timetableTitle = 
      type === 'section' ? `Year ${data.year} - Section ${data.section}` :
      type === 'venue' ? data.venue_name :
      type === 'teacher' ? data.teacher_name : 
      'Timetable';

    return (
      <div key={timetableTitle} className="selected-timetable-container">
        <div className="timetable-header">
          <h2>{timetableTitle}</h2>
          <button 
            className="download-btn" 
            onClick={() => downloadTimetable(timetableData)}
          >
            Download PDF
          </button>
        </div>
        <table className="timetable">
          <thead>
            <tr>
              <th>Time</th>
              {PREDEFINED_DAYS.map(day => <th key={day}>{day}</th>)}
            </tr>
          </thead>
          <tbody>
            {PREDEFINED_SLOTS.map((slot, index) => (
              <tr key={index} className={slot === 'BREAK' || slot === 'LUNCH' ? 'special-row' : ''}>
                <td className="time-slot">{slot}</td>
                {PREDEFINED_DAYS.map(day => {
                  const cellData = data.timetable?.[day]?.[slot];
                  return (
                    <td 
                      key={day} 
                      className={
                        slot === 'BREAK' || slot === 'LUNCH' ? 'break-slot' : 
                        cellData ? 'filled-slot' : 'empty-slot'
                      }
                    >
                      {formatCellContent(cellData, type)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // Render Sidebar
  const renderSidebar = () => (
    <div className="sidebar">
      <div className="view-options">
        <h3>View Timetables</h3>
        <div className="view-type-selector">
          {['Class Timetables', 'Venue Timetables', 'Teacher Timetables'].map(type => (
            <button 
              key={type}
              onClick={() => {
                setViewType(type);
                setSelectedTimetables([]);
                setIsViewingAll(false);
              }}
              className={viewType === type ? 'active' : ''}
            >
              {type}
            </button>
          ))}
          <button 
            className={`view-all-button ${isViewingAll ? 'active' : ''}`}
            onClick={handleViewAll}
          >
            {isViewingAll ? 'Clear All' : 'View All'}
          </button>
        </div>

        <div className="timetable-items-container">
          {viewType === 'Class Timetables' && (
            <div className="class-sections">
              <h4>Sections</h4>
              {timetableData.classes.map(cls => (
                <div 
                  key={`${cls.year}-${cls.section}`} 
                  className={`timetable-item ${
                    selectedTimetables.some(
                      t => t.type === 'section' && 
                      t.year === cls.year && 
                      t.section === cls.section
                    ) ? 'selected' : ''
                  }`}
                  onClick={() => toggleTimetableSelection('section', cls)}
                >
                  Year {cls.year} - Section {cls.section}
                </div>
              ))}
            </div>
          )}

          {viewType === 'Venue Timetables' && (
            <div className="venues">
              <h4>Venues</h4>
              {timetableData.venues.map(venue => (
                <div 
                  key={venue.venue_name} 
                  className={`timetable-item ${
                    selectedTimetables.some(
                      t => t.type === 'venue' && 
                      t.venue_name === venue.venue_name
                    ) ? 'selected' : ''
                  }`}
                  onClick={() => toggleTimetableSelection('venue', venue)}
                >
                  {venue.venue_name}
                </div>
              ))}
            </div>
          )}

          {viewType === 'Teacher Timetables' && (
            <div className="teachers">
              <h4>Teachers</h4>
              {timetableData.teachers.map(teacher => (
                <div 
                  key={teacher.teacher_name} 
                  className={`timetable-item ${
                    selectedTimetables.some(
                      t => t.type === 'teacher' && 
                      t.teacher_name === teacher.teacher_name
                    ) ? 'selected' : ''
                  }`}
                  onClick={() => toggleTimetableSelection('teacher', teacher)}
                >
                  {teacher.teacher_name}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // Main Render
  return (
    <div className={`view-timetables-page ${isDarkMode ? 'dark' : 'light'}`}>
      <div className="header">
        <div className="logo-section">
          <img src="/srmlogo.png" alt="RSKM Logo" className="logo" />
        </div>
        <div className="theme-switch" onClick={toggleTheme}>
          <div className="switch-track">
            <div className="switch-thumb">
              {isDarkMode ? '🌙' : '☀️'}
            </div>
          </div>
        </div>
      </div>

      <button onClick={onBack} className="back-button">← Back</button>

      <div className="timetable-layout">
        {renderSidebar()}
        
        <div className="timetable-content">
          {isLoading ? (
            <div className="loading">Loading...</div>
          ) : error ? (
            <div className="error">{error}</div>
          ) : selectedTimetables.length > 0 ? (
            <div className="multiple-timetables">
              {selectedTimetables.map(renderTimetable)}
            </div>
          ) : (
            <div className="placeholder">Select timetables to view</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ViewTimetablesPage;