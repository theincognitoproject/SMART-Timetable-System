import axiosInstance from '../utils/axiosConfig';

export const fetchTimetables = async () => {
  try {
    const [classesResponse, teachersResponse, venuesResponse] = await Promise.all([
      axiosInstance.get('/timetables/classes'),
      axiosInstance.get('/timetables/teachers'),
      axiosInstance.get('/timetables/venues')
    ]);

    return {
      classes: classesResponse.data,
      teachers: teachersResponse.data,
      venues: venuesResponse.data
    };
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  }
};