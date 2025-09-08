import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Helper function to get user role from localStorage
const getUserRole = () => {
  const userInfo = localStorage.getItem('user_info');
  if (userInfo) {
    const user = JSON.parse(userInfo);
    return user.role;
  }
  return null;
};

// Helper function to get the correct endpoint path based on user role
const getRoleBasedPath = (baseResource, path = '') => {
  const role = getUserRole();
  
  // Super admin and support team get global access to all tenant resources
  if (role === 'super_admin' || role === 'support_team') {
    return `/admin/${baseResource}${path}`;
  } else if (role === 'tenant_admin' || role === 'staff_admin' || role === 'sales_team') {
    // Handle batches specially - they have their own role-based structure
    if (baseResource === 'batches') {
      return `/batches/admin${path}`;
    }
    return `/tenants/admin/${baseResource}${path}`;
  } else if (role === 'staff') {
    // Handle batches specially for staff users
    if (baseResource === 'batches') {
      return `/batches/staff${path}`;
    }
    return `/tenants/staff/${baseResource}${path}`;
  }
  
  // Fallback to legacy endpoint
  return `/tenants/${baseResource}${path}`;
};

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken,
          });

          const { access } = response.data;
          localStorage.setItem('access_token', access);

          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Enhanced error logging for debugging
    console.error('[API ERROR]:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      data: error.response?.data,
      message: error.message,
      stack: error.stack
    });

    // Store error in localStorage for debugging
    try {
      const errorLog = {
        timestamp: new Date().toISOString(),
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        error: error.response?.data || error.message
      };
      
      const recentErrors = JSON.parse(localStorage.getItem('recalliq_api_errors') || '[]');
      recentErrors.push(errorLog);
      
      // Keep only last 20 errors
      if (recentErrors.length > 20) {
        recentErrors.shift();
      }
      
      localStorage.setItem('recalliq_api_errors', JSON.stringify(recentErrors));
    } catch (e) {
      console.warn('Could not log API error:', e);
    }

    // Show toast for common errors (but detailed popup will be handled by error handler)
    if (error.response?.status !== 404) { // Don't show toast for 404s as they'll be handled by popup
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else if (error.response?.data?.message) {
        toast.error(error.response.data.message);
      } else if (error.message && !error.response) {
        toast.error('Network error - please check your connection');
      }
    }

    return Promise.reject(error);
  }
);

console.log('[CONFIG] API Configuration:', { 
  API_BASE_URL 
});

export const authAPI = {
  login: (credentials) => api.post('/auth/login/', credentials),
  register: (userData) => api.post('/auth/register/', userData),
  tenantAdminRegister: (userData) => api.post('/auth/tenant-admin-register/', userData),
  googleOAuthSignup: (data) => api.post('/auth/google-oauth-signup/', data),
  passwordResetRequest: (data) => api.post('/auth/password-reset-request/', data),
  passwordResetConfirm: (data) => api.post('/auth/password-reset-confirm/', data),
  requestSignupOTP: (data) => api.post('/auth/request-signup-otp/', data),
  verifySignupOTP: (data) => api.post('/auth/verify-signup-otp/', data),
  refreshToken: (refresh) => api.post('/auth/refresh/', { refresh }),
  getProfile: () => api.get('/auth/profile/'),
  updateProfile: (userData) => api.put('/auth/profile/', userData),
  changePassword: (passwordData) => api.post('/auth/change-password/', passwordData),
  getDashboard: () => api.get('/auth/dashboard/'),
  getTenantDashboard: () => api.get('/auth/tenant-dashboard/'),
  getUsers: (params = {}) => api.get('/auth/users/', { params }),
  createUser: (userData) => api.post('/auth/users/', userData),
  updateUser: (id, userData) => api.put(`/auth/users/${id}/`, userData),
  deleteUser: (id) => api.delete(`/auth/users/${id}/`),
  getUser: (id) => api.get(`/auth/users/${id}/`),
  getUserFilterOptions: () => api.get('/auth/users/filter-options/'),
  getAvailableUserRoles: () => api.get('/auth/users/available-roles/'),
  
  // Email Configuration APIs
  getEmailConfigurations: () => api.get('/auth/email-configurations/'),
  createEmailConfiguration: (configData) => api.post('/auth/email-configurations/', configData),
  updateEmailConfiguration: (id, configData) => api.put(`/auth/email-configurations/${id}/`, configData),
  deleteEmailConfiguration: (id) => api.delete(`/auth/email-configurations/${id}/`),
  testEmailConfiguration: (id) => api.post(`/auth/email-configurations/${id}/test/`),
  testEmailSettings: (settings) => api.post('/auth/email-configurations/test-settings/', settings),
  getDefaultEmailConfiguration: () => api.get('/auth/email-configurations/default/'),
  getTenantEmailConfigurations: () => api.get('/auth/tenant-email-configurations/'),
};

export const tenantsAPI = {
  getTenants: () => api.get('/tenants/'),
  createTenant: (data) => api.post('/tenants/', data),
  getTenant: (id) => api.get(`/tenants/${id}/`),
  updateTenant: (id, data) => api.put(`/tenants/${id}/`, data),
  deleteTenant: (id) => api.delete(`/tenants/${id}/`),
  
  getTenantEmails: () => api.get('/tenants/emails/'),
  createTenantEmail: (data) => api.post('/tenants/emails/', data),
  updateTenantEmail: (id, data) => api.put(`/tenants/emails/${id}/`, data),
  deleteTenantEmail: (id) => api.delete(`/tenants/emails/${id}/`),
  
  // Role-based Groups API
  getGroups: () => api.get(getRoleBasedPath('groups', '/')),
  createGroup: (data) => api.post(getRoleBasedPath('groups', '/'), data),
  getGroup: (id) => api.get(getRoleBasedPath('groups', `/${id}/`)),
  updateGroup: (id, data) => api.put(getRoleBasedPath('groups', `/${id}/`), data),
  deleteGroup: (id) => api.delete(getRoleBasedPath('groups', `/${id}/`)),
  bulkAddEmails: (id, data) => api.post(getRoleBasedPath('groups', `/${id}/bulk_add_emails/`), data),
  uploadExcel: (id, formData) => api.post(getRoleBasedPath('groups', `/${id}/upload_excel/`), formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  downloadTemplate: () => api.get(getRoleBasedPath('groups', '/download_excel_template/'), { 
    responseType: 'blob' 
  }),
  bulkRemoveEmails: (id, data) => api.delete(getRoleBasedPath('groups', `/${id}/bulk_remove_emails/`), { data }),
  
  // Role-based Group Emails API
  getGroupEmails: (params = {}) => api.get(getRoleBasedPath('group-emails', '/'), { params }),
  createGroupEmail: (data) => api.post(getRoleBasedPath('group-emails', '/'), data),
  updateGroupEmail: (id, data) => api.put(getRoleBasedPath('group-emails', `/${id}/`), data),
  deleteGroupEmail: (id) => api.delete(getRoleBasedPath('group-emails', `/${id}/`)),
};

export const emailsAPI = {
  getTemplates: () => api.get('/emails/templates/'),
  createTemplate: (data) => api.post('/emails/templates/', data),
  getTemplate: (id) => api.get(`/emails/templates/${id}/`),
  updateTemplate: (id, data) => api.put(`/emails/templates/${id}/`, data),
  deleteTemplate: (id) => api.delete(`/emails/templates/${id}/`),
  previewTemplate: (id, data) => api.post(`/emails/templates/${id}/preview/`, data),
  sendTestEmail: (id, data) => api.post(`/emails/templates/${id}/send_test/`, data),
  getTemplateVariables: (id) => api.get(`/emails/templates/${id}/variables/`),
  getProviderConfigs: (provider = null) => api.get(`/emails/templates/provider_configs/${provider ? `?provider=${provider}` : ''}`),
};

export const batchesAPI = {
  getBatches: (params = {}) => api.get(getRoleBasedPath('batches', '/'), { params }),
  createBatch: (data) => api.post(getRoleBasedPath('batches', '/'), data),
  getBatch: (id) => api.get(getRoleBasedPath('batches', `/${id}/`)),
  updateBatch: (id, data) => api.put(getRoleBasedPath('batches', `/${id}/`), data),
  deleteBatch: (id) => api.delete(getRoleBasedPath('batches', `/${id}/`)),
  executeAction: (id, action) => api.post(getRoleBasedPath('batches', `/${id}/execute_action/`), { action }),
  getRecipients: (id) => api.get(getRoleBasedPath('batches', `/${id}/recipients/`)),
  updateRecipients: (id, data) => api.post(getRoleBasedPath('batches', `/${id}/update_recipients/`), data),
  markDocumentsReceived: (id, data) => api.post(getRoleBasedPath('batches', `/${id}/mark_documents_received/`), data),
  markDocumentsNotReceived: (id, data) => api.post(getRoleBasedPath('batches', `/${id}/mark_documents_not_received/`), data),
  generateRecipients: (id) => api.post(getRoleBasedPath('batches', `/${id}/generate_recipients/`)),
  getStatistics: (id) => api.get(getRoleBasedPath('batches', `/${id}/statistics/`)),
  getDashboardStats: () => api.get(getRoleBasedPath('batches', '/dashboard_stats/')),
  resetDocuments: (id, data) => api.post(getRoleBasedPath('batches', `/${id}/reset_documents/`), data),
};

export const logsAPI = {
  getEmailLogs: (params = {}) => api.get('/logs/emails/', { params }),
  getEmailLogStats: (params = {}) => api.get('/logs/emails/statistics/', { params }),
  exportEmailLogs: () => {
    const timestamp = new Date().toISOString().split('T')[0];
    return api.get('/logs/emails/export/', { 
      responseType: 'blob',
      headers: { 'Content-Disposition': `attachment; filename="email_logs_${timestamp}.csv"` }
    });
  },
  getDailyStats: (days = 30) => api.get(`/logs/emails/daily_stats/?days=${days}`),
  getBatchExecutionLogs: (params = {}) => api.get('/logs/batch-executions/', { params }),
  getTenantUsage: () => api.get('/logs/emails/tenant_usage/'),
  markDocumentsReceived: (id, data) => api.post(`/logs/emails/${id}/mark_documents_received/`, data),
  bulkMarkDocumentsReceived: (data) => api.post('/logs/emails/bulk_mark_documents_received/', data),
  bulkMarkDocumentsNotReceived: (data) => api.post('/logs/emails/bulk_mark_documents_not_received/', data),
  // Date-based bulk operations as requested
  bulkMarkDocumentsByDateRange: (dateFrom, dateTo, documentsReceived = true) => {
    const endpoint = documentsReceived ? 
      '/logs/emails/bulk_mark_documents_received/' : 
      '/logs/emails/bulk_mark_documents_not_received/';
    return api.post(endpoint, { 
      date_from: dateFrom, 
      date_to: dateTo,
      bulk_by_date: true 
    });
  },
};

export const recipientsAPI = {
  list: (params = '') => api.get(getRoleBasedPath('recipients', `/${params ? '?' + params : ''}`)),
  create: (data) => api.post(getRoleBasedPath('recipients', '/'), data),
  get: (id) => api.get(getRoleBasedPath('recipients', `/${id}/`)),
  update: (id, data) => api.put(getRoleBasedPath('recipients', `/${id}/`), data),
  delete: (id) => api.delete(getRoleBasedPath('recipients', `/${id}/`)),
  bulkCreate: (data) => api.post(getRoleBasedPath('recipients', '/bulk_create/'), data),
  downloadTemplate: () => api.get(getRoleBasedPath('recipients', '/download_template/'), { responseType: 'blob' }),
  uploadExcel: (formData) => api.post(getRoleBasedPath('recipients', '/upload_excel/'), formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  exportExcel: (params = '') => api.get(getRoleBasedPath('recipients', `/export_excel/${params ? '?' + params : ''}`), { 
    responseType: 'blob' 
  }),
  bulkUpdateGroups: (data) => api.post(getRoleBasedPath('recipients', '/bulk_update_groups/'), data),
};

export const contactGroupsAPI = {
  list: (params = '') => api.get(getRoleBasedPath('contact-groups', `/${params ? '?' + params : ''}`)),
  create: (data) => api.post(getRoleBasedPath('contact-groups', '/'), data),
  get: (id) => api.get(getRoleBasedPath('contact-groups', `/${id}/`)),
  update: (id, data) => api.put(getRoleBasedPath('contact-groups', `/${id}/`), data),
  delete: (id) => api.delete(getRoleBasedPath('contact-groups', `/${id}/`)),
  getRecipients: (id) => api.get(getRoleBasedPath('contact-groups', `/${id}/recipients/`)),
};

// Add the new APIs to the main api object
api.recipients = recipientsAPI;
api.contactGroups = contactGroupsAPI;

export default api;