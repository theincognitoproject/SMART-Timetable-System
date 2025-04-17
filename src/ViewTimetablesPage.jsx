import React, { useState, useEffect } from 'react';
import { fetchTimetables } from './services/timetableService';
import './ViewTimetablesPage.css';

const PREDEFINED_SLOTS = [
  "8:00-8:50", "8:50-9:40", 
  "BREAK",
  "9:50-10:40", "10:40-11:30", 
  "LUNCH",
  "12:20-1:10", "1:10-2:00", "2:00-2:50", "2:50-3:40"
];

const PREDEFINED_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

const ViewTimetablesPage = ({ 
  onBack, 
  isDarkMode, 
  toggleTheme 
}) => {
  const [viewType, setViewType] = useState('Class Timetables');
  const [selectedYear, setSelectedYear] = useState(1);
  const [selectedSections, setSelectedSections] = useState([]);
  const [selectedVenues, setSelectedVenues] = useState([]);
  const [selectedTeachers, setSelectedTeachers] = useState([]);
  const [viewAllSections, setViewAllSections] = useState(false);
  const [timetableData, setTimetableData] = useState({
    classes: [],
    teachers: [],
    venues: []
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch timetable data
  const loadTimetableData = async () => {
    try {
      setIsLoading(true);
      const data = await fetchTimetables();
      setTimetableData(data);
      
      // Initialize selections
      const allClassSections = data.classes.map(cls => cls.section);
      const allVenues = data.venues.map(venue => venue.venue_name);
      const allTeachers = data.teachers.map(teacher => teacher.teacher_name);

      setSelectedSections(allClassSections);
      setSelectedVenues(allVenues);
      setSelectedTeachers(allTeachers);

      setError(null);
    } catch (err) {
      console.error('Timetable fetch error:', err);
      setError('Failed to fetch timetables. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadTimetableData();
  }, []);

  // Handle View All Sections
  const handleViewAllSections = () => {
    setViewAllSections(true);
    const allSections = timetableData.classes.map(cls => cls.section);
    setSelectedSections(allSections);
  };

  // Sidebar rendering
  const renderSidebar = () => {
    return (
      <div className="sidebar">
        <div className="view-options">
          <h3>View Options</h3>
          <div className="radio-group">
            {['Class Timetables', 'Venue Timetables', 'Teacher Timetables'].map(type => (
              <label key={type} className="radio-label">
                <input
                  type="radio"
                  name="viewType"
                  value={type}
                  checked={viewType === type}
                  onChange={() => {
                    setViewType(type);
                    setViewAllSections(false);
                  }}
                />
                <span className="custom-radio"></span>
                {type}
              </label>
            ))}
          </div>

          {viewType === 'Class Timetables' && (
            <>
              <div className="year-sections">
                <h4>Sections</h4>
                {[1, 2, 3].map(year => (
                  <div key={year}>
                    <h5>Year {year}</h5>
                    {timetableData.classes
                      .filter(cls => cls.year === year)
                      .map(cls => (
                        <div key={`${year}-${cls.section}`} className="section-item">
                          <input
                            type="checkbox"
                            id={`section-${year}-${cls.section}`}
                            checked={selectedSections.includes(cls.section)}
                            onChange={() => {
                              setViewAllSections(false);
                              setSelectedSections(prev => 
                                prev.includes(cls.section)
                                  ? prev.filter(s => s !== cls.section)
                                  : [...prev, cls.section]
                              );
                            }}
                          />
                          <label htmlFor={`section-${year}-${cls.section}`}>
                            Section {cls.section}
                          </label>
                        </div>
                      ))}
                  </div>
                ))}
              </div>

              <button 
                className="view-all-btn" 
                onClick={handleViewAllSections}
              >
                View All Sections
              </button>
            </>
          )}

          {viewType === 'Venue Timetables' && (
            <div className="venues-list">
              {timetableData.venues.map(venue => (
                <div key={venue.venue_id} className="venue-item">
                  <input
                    type="checkbox"
                    id={`venue-${venue.venue_id}`}
                    checked={selectedVenues.includes(venue.venue_name)}
                    onChange={() => {
                      setSelectedVenues(prev => 
                        prev.includes(venue.venue_name)
                          ? prev.filter(v => v !== venue.venue_name)
                          : [...prev, venue.venue_name]
                      );
                    }}
                  />
                  <label htmlFor={`venue-${venue.venue_id}`}>
                    {venue.venue_name}
                  </label>
                </div>
              ))}
            </div>
          )}

          {viewType === 'Teacher Timetables' && (
            <div className="teachers-list">
              {timetableData.teachers.map(teacher => (
                <div key={teacher.employee_id} className="teacher-item">
                  <input
                    type="checkbox"
                    id={`teacher-${teacher.employee_id}`}
                    checked={selectedTeachers.includes(teacher.teacher_name)}
                    onChange={() => {
                      setSelectedTeachers(prev => 
                        prev.includes(teacher.teacher_name)
                          ? prev.filter(t => t !== teacher.teacher_name)
                          : [...prev, teacher.teacher_name]
                      );
                    }}
                  />
                  <label htmlFor={`teacher-${teacher.employee_id}`}>
                    {teacher.teacher_name}
                  </label>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  // Render class timetables
  const renderClassTimetables = () => {
    const classesToRender = viewAllSections
      ? timetableData.classes.filter(cls => selectedSections.includes(cls.section))
      : timetableData.classes.filter(
          cls => cls.year === selectedYear && selectedSections.includes(cls.section)
        );

    return (
      <div className="timetables-container">
        {classesToRender.map((classData, index) => (
          <div key={index} className="timetable-card">
            <h3>Year {classData.year} - Section {classData.section}</h3>
            <table className="timetable">
              <thead>
                <tr>
                  <th>Time</th>
                  {PREDEFINED_DAYS.map(day => (
                    <th key={day}>{day}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {PREDEFINED_SLOTS.map((slot, slotIndex) => (
                  <tr key={slotIndex}>
                    <td className={slot === 'BREAK' || slot === 'LUNCH' ? 'break-slot' : ''}>
                      {slot}
                    </td>
                    {PREDEFINED_DAYS.map(day => {
                      const cellData = classData.timetable[day]?.[slot];
                      return (
                        <td 
                          key={day} 
                          className={
                            slot === 'BREAK' || slot === 'LUNCH' 
                              ? 'break-slot' 
                              : cellData 
                                ? 'filled-slot' 
                                : 'empty-slot'
                          }
                        >
                          {typeof cellData === 'object' 
                            ? `${cellData.code}\n${cellData.teacher}` 
                            : cellData || '-'}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>
    );
  };

  // Render venue timetables
  const renderVenueTimetables = () => {
    const venuesToRender = timetableData.venues.filter(
      venue => selectedVenues.includes(venue.venue_name)
    );

    return (
      <div className="timetables-container">
        {venuesToRender.map((venue, index) => (
          <div key={index} className="timetable-card">
            <h3>{venue.venue_name}</h3>
            <table className="timetable">
              <thead>
                <tr>
                  <th>Time</th>
                  {PREDEFINED_DAYS.map(day => (
                    <th key={day}>{day}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {PREDEFINED_SLOTS.map((slot, slotIndex) => (
                  <tr key={slotIndex}>
                    <td className={slot === 'BREAK' || slot === 'LUNCH' ? 'break-slot' : ''}>
                      {slot}
                    </td>
                    {PREDEFINED_DAYS.map(day => {
                      const cellData = venue.timetable[day]?.[slot];
                      return (
                        <td 
                          key={day} 
                          className={
                            slot === 'BREAK' || slot === 'LUNCH' 
                              ? 'break-slot' 
                              : cellData 
                                ? 'filled-slot' 
                                : 'empty-slot'
                          }
                        >
                          {typeof cellData === 'object' 
                            ? `${cellData.year}-${cellData.section}\n${cellData.code}` 
                            : cellData || '-'}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>
    );
  };

  // Render teacher timetables
  const renderTeacherTimetables = () => {
    const teachersToRender = timetableData.teachers.filter(
      teacher => selectedTeachers.includes(teacher.teacher_name)
    );

    return (
      <div className="timetables-container">
        {teachersToRender.map((teacher, index) => (
          <div key={index} className="timetable-card">
            <h3>{teacher.teacher_name}</h3>
            <table className="timetable">
              <thead>
                <tr>
                  <th>Time</th>
                  {PREDEFINED_DAYS.map(day => (
                    <th key={day}>{day}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {PREDEFINED_SLOTS.map((slot, slotIndex) => (
                  <tr key={slotIndex}>
                    <td className={slot === 'BREAK' || slot === 'LUNCH' ? 'break-slot' : ''}>
                      {slot}
                    </td>
                    {PREDEFINED_DAYS.map(day => {
                      const cellData = teacher.timetable[day]?.[slot];
                      return (
                        <td 
                          key={day} 
                          className={
                            slot === 'BREAK' || slot === 'LUNCH' 
                              ? 'break-slot' 
                              : cellData 
                                ? 'filled-slot' 
                                : 'empty-slot'
                          }
                        >
                          {typeof cellData === 'object' 
                            ? `${cellData.year}-${cellData.section}\n${cellData.code}` 
                            : cellData || '-'}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className={`view-timetables-page ${isDarkMode ? 'dark' : 'light'}`}>
      <div className="timetables-header">
        <button onClick={onBack} className="back-button">← Back</button>
        <div className="theme-toggle" onClick={toggleTheme}>
          {isDarkMode ? '☀️' : '🌙'}
        </div>
      </div>

      <div className="timetable-layout">
        {(viewType === 'Class Timetables' || 
          viewType === 'Venue Timetables' || 
          viewType === 'Teacher Timetables') && renderSidebar()}
        
        <div className="timetable-content">
          {isLoading ? (
            <div className="loading">Loading...</div>
          ) : error ? (
            <div className="error">{error}</div>
          ) : (
            viewType === 'Class Timetables' ? renderClassTimetables() : 
            viewType === 'Venue Timetables' ? renderVenueTimetables() : 
            renderTeacherTimetables()
          )}
        </div>
      </div>
    </div>
  );
};

export default ViewTimetablesPage;