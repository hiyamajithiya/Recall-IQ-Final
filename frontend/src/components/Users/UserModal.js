import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { authAPI, tenantsAPI } from '../../utils/api';
import { XMarkIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function UserModal({ user, mode, onClose, onSuccess }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [tenants, setTenants] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [availableRoles, setAvailableRoles] = useState([]);
  const [showPassword, setShowPassword] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm();

  const watchedRole = watch('role');
  const watchedTenant = watch('tenant');

  useEffect(() => {
    fetchTenants();
    fetchCurrentUser();
    fetchAvailableRoles();
    if (user && mode === 'edit') {
      setValue('username', user.username);
      setValue('email', user.email);
      setValue('first_name', user.first_name || '');
      setValue('last_name', user.last_name || '');
      setValue('role', user.role);
      setValue('tenant', user.tenant?.id || '');
      setValue('is_active', user.is_active);
    }
  }, [user, mode, setValue]);

  // Clear tenant field when role is changed to sales_team or support_team
  useEffect(() => {
    if (['sales_team', 'support_team'].includes(watchedRole)) {
      setValue('tenant', '');
    }
  }, [watchedRole, setValue]);

  // Track selected tenant to show user limits
  useEffect(() => {
    if (watchedTenant) {
      const tenant = tenants.find(t => t.id === parseInt(watchedTenant));
      setSelectedTenant(tenant);
    } else {
      setSelectedTenant(null);
    }
  }, [watchedTenant, tenants]);

  const fetchTenants = async () => {
    try {
      const response = await tenantsAPI.getTenants();
      setTenants(response.data.results || response.data);
    } catch (error) {
      console.error('Failed to load tenants:', error);
    }
  };

  const fetchCurrentUser = async () => {
    try {
      const response = await authAPI.getProfile();
      setCurrentUser(response.data);
    } catch (error) {
      console.error('Failed to load current user:', error);
    }
  };

  const fetchAvailableRoles = async () => {
    try {
      const response = await authAPI.getAvailableUserRoles();
      setAvailableRoles(response.data.available_roles || []);
    } catch (error) {
      console.error('Failed to load available roles:', error);
      // Fallback to default roles if API fails
      setAvailableRoles([
        { value: 'staff_admin', label: 'Staff Admin' },
        { value: 'staff', label: 'Staff' }
      ]);
    }
  };

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    try {
      console.log('🚀 Submitting user data:', data);
      
      // Handle tenant field based on role
      if (['sales_team', 'support_team'].includes(data.role)) {
        // Sales team and Support team don't have tenant assignments - explicitly set to null
        data.tenant = null;
      } else if (currentUser?.role !== 'super_admin') {
        // For non-super admin users, remove tenant field - backend automatically assigns it
        delete data.tenant;
      } else if (data.tenant === '') {
        // Convert empty string to null for proper handling
        data.tenant = null;
      }

      console.log('📝 Final data being sent:', data);

      if (mode === 'create') {
        await authAPI.createUser(data);
        toast.success('User created successfully');
      } else {
        await authAPI.updateUser(user.id, data);
        toast.success('User updated successfully');
      }
      onSuccess();
    } catch (error) {
      console.error('❌ User creation/update error:', error);
      console.error('Error response:', error.response?.data);
      
      let errorMsg = `Failed to ${mode} user`;
      
      // Try to extract meaningful error messages
      if (error.response?.data) {
        const errorData = error.response.data;
        if (errorData.detail) {
          errorMsg = errorData.detail;
        } else if (errorData.message) {
          errorMsg = errorData.message;
        } else if (typeof errorData === 'object') {
          // Handle validation errors
          const firstError = Object.values(errorData)[0];
          if (Array.isArray(firstError)) {
            errorMsg = firstError[0];
          } else if (typeof firstError === 'string') {
            errorMsg = firstError;
          }
        }
      }
      
      toast.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Use dynamic roles from API instead of hardcoded choices

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  {mode === 'create' ? 'Add New User' : 'Edit User'}
                </h3>
                <button
                  type="button"
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="form-label">Username</label>
                  <input
                    {...register('username', { required: 'Username is required' })}
                    type="text"
                    className="form-input"
                    placeholder="Enter username"
                  />
                  {errors.username && (
                    <p className="mt-1 text-sm text-red-600">{errors.username.message}</p>
                  )}
                </div>

                <div>
                  <label className="form-label">Email</label>
                  <input
                    {...register('email', { 
                      required: 'Email is required',
                      pattern: {
                        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                        message: 'Invalid email address'
                      }
                    })}
                    type="email"
                    className="form-input"
                    placeholder="Enter email"
                  />
                  {errors.email && (
                    <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">First Name</label>
                    <input
                      {...register('first_name')}
                      type="text"
                      className="form-input"
                      placeholder="First name"
                    />
                  </div>
                  <div>
                    <label className="form-label">Last Name</label>
                    <input
                      {...register('last_name')}
                      type="text"
                      className="form-input"
                      placeholder="Last name"
                    />
                  </div>
                </div>

                {mode === 'create' && (
                  <div>
                    <label className="form-label">Password</label>
                    <div className="relative">
                      <input
                        {...register('password', { 
                          required: 'Password is required',
                          minLength: {
                            value: 8,
                            message: 'Password must be at least 8 characters'
                          }
                        })}
                        type={showPassword ? 'text' : 'password'}
                        className="form-input pr-12"
                        placeholder="Enter password"
                        autoComplete="off"
                        data-lpignore="true"
                        data-1p-ignore="true"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-400 hover:text-blue-500 transition-colors duration-200"
                        tabIndex={-1}
                      >
                        {showPassword ? (
                          <EyeSlashIcon className="h-5 w-5" />
                        ) : (
                          <EyeIcon className="h-5 w-5" />
                        )}
                      </button>
                    </div>
                    {errors.password && (
                      <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
                    )}
                  </div>
                )}

                <div>
                  <label className="form-label">Role</label>
                  <select
                    {...register('role', { required: 'Role is required' })}
                    className="form-input"
                  >
                    <option value="">Select role</option>
                    {availableRoles.length > 0 ? (
                      availableRoles.map((role) => (
                        <option key={role.value} value={role.value}>
                          {role.label}
                        </option>
                      ))
                    ) : (
                      // Fallback options if API hasn't loaded yet
                      <>
                        <option value="staff_admin">Staff Admin</option>
                        <option value="staff">Staff</option>
                      </>
                    )}
                  </select>
                  {availableRoles.length === 0 && (
                    <p className="mt-1 text-xs text-gray-500">Loading available roles...</p>
                  )}
                  {errors.role && (
                    <p className="mt-1 text-sm text-red-600">{errors.role.message}</p>
                  )}
                </div>

                {/* Tenant selection - conditional based on role */}
                {currentUser && (
                  <div>
                    <label className="form-label">Tenant</label>
                    {currentUser.role === 'super_admin' ? (
                      // Sales team and Support team don't need tenant assignment
                      ['sales_team', 'support_team'].includes(watchedRole) ? (
                        <div>
                          <input
                            type="text"
                            value="System-wide role (no tenant assignment)"
                            disabled
                            className="form-input bg-gray-100 text-gray-500"
                            {...register('tenant')}
                          />
                          <p className="mt-1 text-xs text-gray-500">
                            {watchedRole === 'sales_team' ? 'Sales team members' : 'Support team'} operate across all tenants
                          </p>
                        </div>
                      ) : (
                        <select
                          {...register('tenant', { 
                            required: watchedRole && watchedRole === 'tenant_admin' ? 'Tenant is required for Tenant Admin role' : false
                          })}
                          className="form-input"
                          disabled={['sales_team', 'support_team'].includes(watchedRole)}
                        >
                          <option value="">Select tenant</option>
                          {tenants.map((tenant) => (
                            <option key={tenant.id} value={tenant.id}>
                              {tenant.name}
                            </option>
                          ))}
                        </select>
                      )
                    ) : (
                      <input
                        type="text"
                        value={currentUser.tenant_name || 'No Tenant'}
                        disabled
                        className="form-input bg-gray-100"
                        {...register('tenant', { 
                          value: currentUser.tenant 
                        })}
                      />
                    )}
                    {errors.tenant && (
                      <p className="mt-1 text-sm text-red-600">{errors.tenant.message}</p>
                    )}
                  </div>
                )}

                {/* User Limits Information */}
                {selectedTenant && watchedRole && mode === 'create' && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-blue-900 mb-2">
                      {selectedTenant.name} - User Limits
                    </h4>
                    <div className="space-y-2 text-xs">
                      {watchedRole === 'tenant_admin' && (
                        <div className="flex justify-between">
                          <span>Tenant Admins:</span>
                          <span className={`font-medium ${
                            selectedTenant.current_user_counts?.tenant_admin >= selectedTenant.max_tenant_admins 
                              ? 'text-red-600' : 'text-green-600'
                          }`}>
                            {selectedTenant.current_user_counts?.tenant_admin || 0}/{selectedTenant.max_tenant_admins}
                          </span>
                        </div>
                      )}
                      {watchedRole === 'staff_admin' && (
                        <div className="flex justify-between">
                          <span>Staff Admins:</span>
                          <span className={`font-medium ${
                            selectedTenant.current_user_counts?.staff_admin >= selectedTenant.max_staff_admins 
                              ? 'text-red-600' : 'text-green-600'
                          }`}>
                            {selectedTenant.current_user_counts?.staff_admin || 0}/{selectedTenant.max_staff_admins}
                          </span>
                        </div>
                      )}
                      {(watchedRole === 'staff' || watchedRole === 'sales_team') && (
                        <div className="flex justify-between">
                          <span>Staff Users:</span>
                          <span className={`font-medium ${
                            (selectedTenant.current_user_counts?.staff + selectedTenant.current_user_counts?.sales_team) >= selectedTenant.max_staff_users 
                              ? 'text-red-600' : 'text-green-600'
                          }`}>
                            {(selectedTenant.current_user_counts?.staff || 0) + (selectedTenant.current_user_counts?.sales_team || 0)}/{selectedTenant.max_staff_users}
                          </span>
                        </div>
                      )}
                      <div className="flex justify-between border-t pt-2">
                        <span className="font-medium">Total Users:</span>
                        <span className={`font-medium ${
                          selectedTenant.current_user_counts?.total >= selectedTenant.max_total_users 
                            ? 'text-red-600' : 'text-green-600'
                        }`}>
                          {selectedTenant.current_user_counts?.total || 0}/{selectedTenant.max_total_users}
                        </span>
                      </div>
                      {selectedTenant.users_remaining?.total === 0 && (
                        <div className="text-red-600 text-xs font-medium mt-2">
                          ⚠️ This tenant has reached its user limit
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <div className="flex items-center">
                  <input
                    {...register('is_active')}
                    type="checkbox"
                    defaultChecked={true}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Active User</span>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
              >
                {isSubmitting ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  mode === 'create' ? 'Create User' : 'Update User'
                )}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}