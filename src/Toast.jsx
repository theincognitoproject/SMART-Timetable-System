import React, { useEffect, useState } from 'react';
import './Toast.css';

const Toast = ({ message, type = 'success', duration = 2000, onClose }) => {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      setTimeout(() => {
        if (onClose) onClose();
      }, 300); // Wait for fade-out animation
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  return (
    <div className={`toast ${type} ${visible ? 'visible' : 'hidden'}`}>
      <div className="toast-content">
        {type === 'success' && <span className="toast-icon">✓</span>}
        {type === 'error' && <span className="toast-icon">✗</span>}
        {type === 'info' && <span className="toast-icon">ℹ</span>}
        <span className="toast-message">{message}</span>
      </div>
    </div>
  );
};

export default Toast;