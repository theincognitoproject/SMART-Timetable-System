// services/timetableService.js

import axiosInstance from '../utils/axiosConfig';

/**
 * Fetch timetable data - either from a specific schema or using the default endpoints
 * @param {string|null} schemaName - Optional schema name to fetch from
 * @returns {Promise<Object>} - Timetable data
 */
export const fetchTimetables = async (schemaName = null) => {
  try {
    if (schemaName) {
      // For specific timetable schema
      const response = await axiosInstance.get(`/timetable/${schemaName}`);
      
      if (response.data && response.data.success) {
        return response.data.timetable_data;
      } else {
        throw new Error(response.data?.error || 'Failed to fetch timetable data');
      }
    } else {
      // For latest timetable data using separate endpoints
      const [classesResponse, teachersResponse, venuesResponse] = await Promise.all([
        axiosInstance.get('/timetables/classes'),
        axiosInstance.get('/timetables/teachers'),
        axiosInstance.get('/timetables/venues')
      ]);
      
      return {
        classes: classesResponse.data || [],
        teachers: teachersResponse.data || [],
        venues: venuesResponse.data || []
      };
    }
  } catch (error) {
    console.error('Error fetching timetables:', error);
    throw new Error(error.response?.data?.detail || 'Failed to fetch timetable data');
  }
};

/**
 * Fetch all available timetable schemas
 * @returns {Promise<Array>} - List of timetable schemas
 */
export const fetchTimetableSchemas = async () => {
  try {
    const response = await axiosInstance.get('/timetable-schemas');
    
    if (response.data && response.data.success) {
      return response.data.schemas;
    } else {
      throw new Error(response.data?.error || 'Failed to fetch timetable schemas');
    }
  } catch (error) {
    console.error('Error fetching timetable schemas:', error);
    throw new Error(error.response?.data?.detail || 'Failed to fetch timetable schemas');
  }
};

/**
 * Delete a timetable schema
 * @param {string} schemaName - Name of schema to delete
 * @returns {Promise<Object>} - Result of delete operation
 */
export const deleteTimetableSchema = async (schemaName) => {
  try {
    const response = await axiosInstance.delete(`/timetable-schema/${schemaName}`);
    
    if (response.data && response.data.success) {
      return { success: true, message: response.data.message };
    } else {
      throw new Error(response.data?.error || 'Failed to delete timetable schema');
    }
  } catch (error) {
    console.error('Error deleting timetable schema:', error);
    throw new Error(error.response?.data?.detail || 'Failed to delete timetable schema');
  }
};