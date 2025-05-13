import axios from 'axios';
import { API_CONFIG } from '../config';

const axiosInstance = axios.create({
  baseURL: API_CONFIG.BASE_URL || 'http://localhost:8000/api',
  timeout: 300000, // 5 minutes
  headers: {
    'Content-Type': 'application/json'
  },
  auth: {
    username: API_CONFIG.AUTH.username,
    password: API_CONFIG.AUTH.password
  }
});

// Add a request interceptor to handle file uploads
axiosInstance.interceptors.request.use(
  config => {
    // If the request contains FormData (file uploads), remove the Content-Type header
    // to let the browser set it with the correct boundary
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Add a response interceptor for better error handling
axiosInstance.interceptors.response.use(
  response => response,
  error => {
    // Check if the error is a timeout error
    if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
      console.error('Request timed out. The operation might still be processing on the server.');
    } else {
      console.error('API Error:', error.response?.data || error.message);
    }
    return Promise.reject(error);
  }
);

// Service methods for specific endpoints
export const TimetableService = {
  /**
   * Fetch class timetables
   * @returns {Promise} Promise resolving to class timetables
   */
  getClassTimetables: () => {
    return axiosInstance.get('/timetables/classes');
  },

  /**
   * Fetch teacher timetables
   * @returns {Promise} Promise resolving to teacher timetables
   */
  getTeacherTimetables: () => {
    return axiosInstance.get('/timetables/teachers');
  },

  /**
   * Fetch venue timetables
   * @returns {Promise} Promise resolving to venue timetables
   */
  getVenueTimetables: () => {
    return axiosInstance.get('/timetables/venues');
  }
};

export const SchemaService = {
  /**
   * Fetch available schemas
   * @returns {Promise} Promise resolving to list of schemas
   */
  getSchemas: () => {
    return axiosInstance.get('/schemas');
  },

  /**
   * Fetch sorted table for a specific schema
   * @param {string} schemaName - Name of the schema
   * @param {Object} [params] - Optional query parameters
   * @returns {Promise} Promise resolving to sorted table data
   */
  getSortedTable: (schemaName, params = {}) => {
    return axiosInstance.get(`/schema/${schemaName}/sortedtable`, {
      params: {
        limit: 100,
        offset: 0,
        ...params
      }
    });
  }
};

export const AllocationService = {
  /**
   * Process year files
   * @param {FormData} formData - Form data containing year files
   * @returns {Promise} Promise resolving to processing result
   */
  processYearFiles: (formData) => {
    return axiosInstance.post('/process-year-files', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  /**
   * Process faculty files
   * @param {FormData} formData - Form data containing faculty files
   * @returns {Promise} Promise resolving to processing result
   */
  processFacultyFiles: (formData) => {
    return axiosInstance.post('/process-faculty-files', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  }
};

export default axiosInstance;