import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { authAPI } from '../utils/api';
import { PlusIcon, PencilIcon, UserIcon, XMarkIcon, TrashIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const formatDate = (dateString) => {
  const date = new Date(dateString);
  const day = date.getDate().toString().padStart(2, '0');
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const year = date.getFullYear();
  return `${day}/${month}/${year}`;
};

const getRoleBadge = (role) => {
  const roleClasses = {
    tenant_admin: 'badge-blue',
    staff_admin: 'badge-purple',
    staff: 'badge-green',
    user: 'badge-gray',
  };
  return roleClasses[role] || 'badge-gray';
};

const getRoleDisplayName = (role) => {
  const roleNames = {
    tenant_admin: 'Tenant Admin',
    staff_admin: 'Staff Admin',
    staff: 'Staff',
    user: 'User',
  };
  return roleNames[role] || role;
};

export default function TenantUsers() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [availableRoles, setAvailableRoles] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    role: 'staff', // Default to staff instead of user
    password: '',
    confirm_password: ''
  });

  useEffect(() => {
    fetchUsers();
    fetchAvailableRoles();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await authAPI.getUsers();
      setUsers(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableRoles = async () => {
    try {
      const response = await authAPI.getAvailableUserRoles();
      setAvailableRoles(response.data.available_roles || []);
      
      // Set default role to the first available role or staff
      if (response.data.available_roles && response.data.available_roles.length > 0) {
        const hasStaff = response.data.available_roles.some(role => role.value === 'staff');
        setFormData(prev => ({
          ...prev,
          role: hasStaff ? 'staff' : response.data.available_roles[0].value
        }));
      }
    } catch (error) {
      console.error('Error fetching available roles:', error);
      // Fallback to default roles if API fails
      setAvailableRoles([
        { value: 'staff_admin', label: 'Staff Admin' },
        { value: 'staff', label: 'Staff' }
      ]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!editingUser && formData.password !== formData.confirm_password) {
      toast.error('Passwords do not match');
      return;
    }

    if (!editingUser && formData.password.length < 8) {
      toast.error('Password must be at least 8 characters long');
      return;
    }

    setSubmitting(true);
    
    try {
      if (editingUser) {
        // Update user - only send fields that can be updated
        const updateData = {
          email: formData.email,
          first_name: formData.first_name,
          last_name: formData.last_name,
          role: formData.role
        };
        
        const response = await authAPI.updateUser(editingUser.id, updateData);
        
        // Update the user in the local state
        const updatedUsers = users.map(u => 
          u.id === editingUser.id ? { ...u, ...response.data } : u
        );
        setUsers(updatedUsers);
        toast.success('User updated successfully');
      } else {
        // Create new user - tenant is automatically assigned by backend for tenant_admin
        const createData = {
          username: formData.username,
          email: formData.email,
          first_name: formData.first_name || '',
          last_name: formData.last_name || '',
          role: formData.role,
          password: formData.password,
          is_active: true
        };

        // Log the request data for debugging
        console.log('Creating user with data:', { ...createData, password: '[REDACTED]' });
        
        const response = await authAPI.createUser(createData);
        
        // Add the new user to the local state
        setUsers([...users, response.data]);
        toast.success('User created successfully');
      }
      
      handleCloseModal();
    } catch (error) {
      console.error('Error saving user:', error.response?.data || error.message);
      
      // Handle specific error messages from the backend
      if (error.response?.data) {
        const errorData = error.response.data;
        
        // Log the full error response for debugging
        console.log('Full error response:', errorData);

        if (typeof errorData === 'object') {
          // Extract field-specific errors
          const errorMessages = [];
          Object.keys(errorData).forEach(field => {
            if (Array.isArray(errorData[field])) {
              errorMessages.push(`${field}: ${errorData[field].join(', ')}`);
            } else if (typeof errorData[field] === 'string') {
              errorMessages.push(`${field}: ${errorData[field]}`);
            }
          });
          if (errorMessages.length > 0) {
            toast.error(errorMessages[0]);
          } else {
            toast.error('Failed to save user');
          }
        } else {
          toast.error(errorData || 'Failed to save user');
        }
      } else {
        toast.error('Failed to save user');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (user) => {
    setEditingUser(user);
    setFormData({
      username: user.username,
      email: user.email,
      first_name: user.first_name,
      last_name: user.last_name,
      role: user.role,
      password: '',
      confirm_password: ''
    });
    setShowModal(true);
  };

  const handleDelete = async (userId) => {
    if (!window.confirm('Are you sure you want to delete this user?')) {
      return;
    }

    try {
      await authAPI.deleteUser(userId);
      const updatedUsers = users.filter(u => u.id !== userId);
      setUsers(updatedUsers);
      toast.success('User deleted successfully');
    } catch (error) {
      console.error('Error deleting user:', error);
      
      // Handle specific error messages from the backend
      if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else if (error.response?.data) {
        const errorData = error.response.data;
        if (typeof errorData === 'object') {
          const errorMessages = [];
          Object.keys(errorData).forEach(field => {
            if (Array.isArray(errorData[field])) {
              errorMessages.push(...errorData[field]);
            } else if (typeof errorData[field] === 'string') {
              errorMessages.push(errorData[field]);
            }
          });
          if (errorMessages.length > 0) {
            toast.error(errorMessages[0]);
          } else {
            toast.error('Failed to delete user');
          }
        } else {
          toast.error(errorData || 'Failed to delete user');
        }
      } else {
        toast.error('Failed to delete user');
      }
    }
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingUser(null);
    
    // Reset form data with default role from available roles
    const defaultRole = availableRoles.length > 0 
      ? (availableRoles.find(r => r.value === 'staff')?.value || availableRoles[0].value)
      : 'staff';
      
    setFormData({
      username: '',
      email: '',
      first_name: '',
      last_name: '',
      role: defaultRole,
      password: '',
      confirm_password: ''
    });
  };

  if (loading && users.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Organization Users
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage users within your organization ({currentUser?.tenant?.name || 'Your Organization'}).
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button 
            onClick={() => setShowModal(true)}
            className="btn-primary flex items-center"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Add User
          </button>
        </div>
      </div>

      {users.length === 0 ? (
        <div className="text-center py-12">
          <UserIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No users</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by adding a new user to your organization.</p>
          <div className="mt-6">
            <button 
              onClick={() => setShowModal(true)}
              className="btn-primary"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Add User
            </button>
          </div>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10">
                          <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center">
                            <span className="text-sm font-medium text-primary-700">
                              {user.first_name?.charAt(0) || user.username?.charAt(0)}
                            </span>
                          </div>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {user.first_name && user.last_name 
                              ? `${user.first_name} ${user.last_name}`
                              : user.username}
                          </div>
                          <div className="text-sm text-gray-500">{user.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`badge ${getRoleBadge(user.role)}`}>
                        {getRoleDisplayName(user.role)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`badge ${user.is_active ? 'badge-green' : 'badge-red'}`}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(user.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button 
                        onClick={() => handleEdit(user)} 
                        className="text-primary-600 hover:text-primary-900 mr-3"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      {(() => {
                        // Hide delete button if current user cannot delete users
                        const cannotDelete = 
                          // Secondary tenant admin (created by tenant admin) cannot delete
                          (currentUser?.role === 'tenant_admin' && 
                           currentUser?.created_by && 
                           currentUser?.created_by?.role === 'tenant_admin') ||
                          // Staff admin cannot delete any users
                          currentUser?.role === 'staff_admin';
                        
                        // Show delete button if current user can delete
                        return !cannotDelete && (
                          <button 
                            onClick={() => handleDelete(user.id)} 
                            className="text-red-600 hover:text-red-900"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        );
                      })()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* User Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  {editingUser ? 'Edit User' : 'Add New User'}
                </h3>
                <button
                  onClick={handleCloseModal}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="form-label">Username</label>
                  <input
                    type="text"
                    className="form-input"
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                    required
                    disabled={!!editingUser}
                  />
                  {editingUser && (
                    <p className="mt-1 text-xs text-gray-500">Username cannot be changed</p>
                  )}
                </div>

                <div>
                  <label className="form-label">Email</label>
                  <input
                    type="email"
                    className="form-input"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">First Name</label>
                    <input
                      type="text"
                      className="form-input"
                      value={formData.first_name}
                      onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                    />
                  </div>
                  
                  <div>
                    <label className="form-label">Last Name</label>
                    <input
                      type="text"
                      className="form-input"
                      value={formData.last_name}
                      onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                    />
                  </div>
                </div>

                <div>
                  <label className="form-label">Role</label>
                  <select
                    className="form-input"
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    required
                  >
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
                </div>

                {!editingUser && (
                  <>
                    <div>
                      <label className="form-label">Password</label>
                      <div className="relative">
                        <input
                          type={showPassword ? 'text' : 'password'}
                          className="form-input pr-12"
                          value={formData.password}
                          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                          required
                          minLength="6"
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
                    </div>

                    <div>
                      <label className="form-label">Confirm Password</label>
                      <div className="relative">
                        <input
                          type={showConfirmPassword ? 'text' : 'password'}
                          className="form-input pr-12"
                          value={formData.confirm_password}
                          onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                          required
                          autoComplete="off"
                          data-lpignore="true"
                          data-1p-ignore="true"
                        />
                        <button
                          type="button"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-400 hover:text-blue-500 transition-colors duration-200"
                          tabIndex={-1}
                        >
                          {showConfirmPassword ? (
                            <EyeSlashIcon className="h-5 w-5" />
                          ) : (
                            <EyeIcon className="h-5 w-5" />
                          )}
                        </button>
                      </div>
                    </div>
                  </>
                )}

                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={handleCloseModal}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="btn-primary"
                  >
                    {submitting ? 'Saving...' : (editingUser ? 'Update' : 'Create')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}