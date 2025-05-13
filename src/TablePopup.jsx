import React from 'react';
import './TablePopup.css';

const TablePopup = ({ data, onClose }) => {
  // Check if data exists and has rows
  if (!data || data.length === 0) {
    return (
      <div className="table-popup-overlay">
        <div className="table-popup-content">
          <button className="close-button" onClick={onClose}>×</button>
          <h2 className="table-popup-title">SortedTable Data</h2>
          <p className="no-data-message">No data available</p>
        </div>
      </div>
    );
  }

  // Get column headers from the first row
  const columns = Object.keys(data[0]);

  return (
    <div className="table-popup-overlay">
      <div className="table-popup-content">
        <button className="close-button" onClick={onClose}>×</button>
        <h2 className="table-popup-title">SortedTable Data</h2>
        
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                {columns.map((column, index) => (
                  <th key={index}>{column}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {columns.map((column, colIndex) => (
                    <td key={colIndex}>{row[column] !== null ? String(row[column]) : '-'}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TablePopup;