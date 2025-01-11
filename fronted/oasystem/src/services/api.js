// src/services/api.js
import axios from 'axios';

const BASE_URL = 'http://192.168.1.234:39200';

// 創建 axios 實例
const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 請求攔截器 - 添加 token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (email, password) => {
    return apiClient.post('/auth/login', 
      new URLSearchParams({
        email: email,
        password: password
      }), 
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      }
    );
  }
};

// Employee API
export const employeeAPI = {
  // 獲取所有員工
  getAllEmployees: () => {
    return apiClient.get('/base/employees');
  },

  // 獲取單個員工
  getEmployee: (id) => {
    return apiClient.get(`/base/employees/${id}`);
  },

  // 創建員工
  createEmployee: (employeeData) => {
    return apiClient.post('/base/employees',employeeData);
  },

  // 更新員工
  updateEmployee: (id, employeeData) => {
    return apiClient.put(`/base/employees/${id}`, employeeData);
  },

  // 刪除員工
  deleteEmployee: (id) => {
    return apiClient.delete(`/base/employees/${id}`);
  }
};

// WebSocket Service
export const createWebSocket = (path) => {
  return new WebSocket(`ws://${BASE_URL.replace('http://', '')}${path}`);
};




export const leaveAPI = {
  // 查詢所有請假記錄
  getLeaveRecords: (startDate, endDate) => {
    return apiClient.get(`/leave/leave-records/time-range`, {
      params: {
        start_date: startDate,
        end_date: endDate
      }
    });
  },

  // 查詢特定員工的請假記錄
  getEmployeeLeaveRecords: (empId, startDate, endDate) => {
    return apiClient.get(`/leave/leave-records/${empId}/time-range`, {
      params: {
        start_date: startDate,
        end_date: endDate
      }
    });
  },
   // 獲取所有員工
  getAllEmployees: () => {
    return apiClient.get('/base/employees');
  }
}


export default {
  authAPI,
  employeeAPI,
  createWebSocket
};
