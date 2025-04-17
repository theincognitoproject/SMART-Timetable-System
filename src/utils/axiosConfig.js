import axios from 'axios';
import { API_CONFIG } from '../config';

const axiosInstance = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: 10000,
  auth: {
    username: API_CONFIG.AUTH.username,
    password: API_CONFIG.AUTH.password
  }
});

export default axiosInstance;