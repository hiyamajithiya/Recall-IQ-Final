import React, { useState, useEffect } from 'react';
import { authAPI } from '../utils/api';
import { useAuth } from '../context/AuthContext';
import { PlusIcon, PencilIcon, UserIcon, TrashIcon, FunnelIcon, XMarkIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import UserModal from '../components/Users/UserModal';
import toast from 'react-hot-toast';

const getRoleBadge = (role) => {
  const roleClasses = {
    super_admin: 'badge-red',
    sales_team: 'badge-orange',
    support_team: 'badge-yellow',
    tenant_admin: 'badge-blue',
    staff_admin: 'badge-purple',
    staff: 'badge-green',
    user: 'badge-gray',
  };
  return roleClasses[role] || 'badge-gray';
};

const formatDate = (dateString) => {
  const date = new Date(dateString);
  const day = date.getDate().toString().padStart(2, '0');
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const year = date.getFullYear();
  return `${day}/${month}/${year}`;
};

const getRoleDisplayName = (role) => {
  const roleNames = {
    super_admin: 'Super Admin',
    sales_team: 'Sales Team',
    support_team: 'Support Team',
    tenant_admin: 'Tenant Admin',
    staff_admin: 'Staff Admin',
    staff: 'Staff',
    user: 'User',
  };
  return roleNames[role] || role;
};

export default function Users() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const [selectedUser, setSelectedUser] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('create');

  // Filtering state
  const [filters, setFilters] = useState({
    tenant: '',
    role: '',
    created_by: '',
    search: ''
  });
  const [filterOptions, setFilterOptions] = useState({
    tenants: [],
    roles: [],
    creators: []
  });
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchUsers();
    fetchFilterOptions();
  }, []);

  // Re-fetch users when filters change
  useEffect(() => {
    fetchUsers();
  }, [filters]);

  const fetchFilterOptions = async () => {
    try {
      const response = await authAPI.getUserFilterOptions();
      setFilterOptions(response.data);
    } catch (error) {
      console.error('Failed to fetch filter options:', error);
      // Minimal fallback options if API fails
      setFilterOptions({
        tenants: [
          { value: 'null', label: 'No Tenant (System Users)' }
        ],
        roles: [
          { value: 'super_admin', label: 'Super Admin' },
          { value: 'sales_team', label: 'Sales Team' },
          { value: 'support_team', label: 'Support Team' },
          { value: 'tenant_admin', label: 'Tenant Admin' },
          { value: 'staff_admin', label: 'Staff Admin' },
          { value: 'staff', label: 'Staff' },
          { value: 'user', label: 'User' }
        ],
        creators: []
      });
    }
  };

  const fetchUsers = async () => {
    try {
      console.log('🔍 [DEBUG] Current user:', currentUser);
      console.log('🔍 [DEBUG] User role:', currentUser?.role);
      console.log('🔍 [DEBUG] Access token exists:', !!localStorage.getItem('access_token'));
      console.log('🔍 Fetching users with filters:', filters);

      // Build query parameters
      const params = {};
      if (filters.tenant) params.tenant = filters.tenant;
      if (filters.role) params.role = filters.role;
      if (filters.created_by) params.created_by = filters.created_by;
      if (filters.search) params.search = filters.search;

      console.log('🔍 [DEBUG] API call params:', params);

      // Use authAPI instead of direct fetch
      const response = await authAPI.getUsers(params);
      const userData = response.data.results || response.data;
      console.log('👥 Users fetched successfully:', userData.length);

      setUsers(userData);
    } catch (error) {
      console.error('❌ [DEBUG] Full error object:', error);
      console.error('❌ [DEBUG] Error response:', error.response);
      console.error('❌ [DEBUG] Error status:', error.response?.status);
      console.error('❌ [DEBUG] Error data:', error.response?.data);
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const filterUsersByTab = (users, tab) => {
    switch (tab) {
      case 'super_admin':
        return users.filter(user => user.role === 'super_admin');
      case 'sales_team':
        return users.filter(user => user.role === 'sales_team');
      case 'support_team':
        return users.filter(user => user.role === 'support_team');
      case 'tenant_admin':
        return users.filter(user => user.role === 'tenant_admin');
      case 'staff_admin':
        return users.filter(user => user.role === 'staff_admin');
      case 'staff':
        return users.filter(user => user.role === 'staff');
      case 'user':
        return users.filter(user => user.role === 'user');
      default:
        return users;
    }
  };

  const filteredUsers = filterUsersByTab(users, activeTab);

  // Debug logging for rendering
  console.log('🎯 Current activeTab:', activeTab);
  console.log('📋 All users state:', users);
  console.log('🔽 Filtered users for display:', filteredUsers);
  console.log('📊 Filtered users count:', filteredUsers ? filteredUsers.length : 0);

  const handleCreate = () => {
    setSelectedUser(null);
    setModalMode('create');
    setShowModal(true);
  };

  const handleEdit = (user) => {
    setSelectedUser(user);
    setModalMode('edit');
    setShowModal(true);
  };

  const handleDelete = async (user) => {
    if (window.confirm(`Are you sure you want to delete user "${user.username}"?`)) {
      try {
        await authAPI.deleteUser(user.id);
        toast.success('User deleted successfully');
        fetchUsers();
      } catch (error) {
        toast.error('Failed to delete user');
      }
    }
  };

  const handleModalClose = () => {
    setShowModal(false);
    setSelectedUser(null);
  };

  const handleModalSuccess = () => {
    fetchUsers();
    handleModalClose();
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const clearFilters = () => {
    setFilters({
      tenant: '',
      role: '',
      created_by: '',
      search: ''
    });
    setActiveTab('all');
  };

  const hasActiveFilters = () => {
    return Object.values(filters).some(value => value !== '') || activeTab !== 'all';
  };

  const tabs = [
    { id: 'all', name: 'All Users', count: users.length },
    { id: 'super_admin', name: 'Super Admins', count: users.filter(u => u.role === 'super_admin').length },
    { id: 'sales_team', name: 'Sales Team', count: users.filter(u => u.role === 'sales_team').length },
    { id: 'support_team', name: 'Support Team', count: users.filter(u => u.role === 'support_team').length },
    { id: 'tenant_admin', name: 'Tenant Admins', count: users.filter(u => u.role === 'tenant_admin').length },
    { id: 'staff_admin', name: 'Staff Admins', count: users.filter(u => u.role === 'staff_admin').length },
    { id: 'staff', name: 'Staff', count: users.filter(u => u.role === 'staff').length },
    { id: 'user', name: 'Users', count: users.filter(u => u.role === 'user').length },
  ];

  if (loading) {
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
            Users Management
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage system users and their permissions across different roles.
          </p>
        </div>
        <div className="mt-4 flex space-x-3 md:mt-0 md:ml-4">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`btn-secondary flex items-center ${hasActiveFilters() ? 'bg-blue-50 border-blue-300 text-blue-700' : ''}`}
          >
            <FunnelIcon className="h-5 w-5 mr-2" />
            Filters
            {hasActiveFilters() && (
              <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Active
              </span>
            )}
          </button>
          <button onClick={handleCreate} className="btn-primary flex items-center">
            <PlusIcon className="h-5 w-5 mr-2" />
            Add User
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`${activeTab === tab.id
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center`}
            >
              {tab.name}
              <span
                className={`${activeTab === tab.id
                  ? 'bg-primary-100 text-primary-600'
                  : 'bg-gray-100 text-gray-900'
                  } ml-2 py-0.5 px-2.5 rounded-full text-xs font-medium`}
              >
                {tab.count}
              </span>
            </button>
          ))}
        </nav>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex gap-4 items-end">
            <div>
              <div className="flex items-center space-x-1 mb-1">
                <label className="text-sm font-medium text-gray-700">Search Users</label>
                <span style={{ fontSize: '18px' }}>🔍</span>
              </div>

              <input
                type="text"
                placeholder="Search users..."
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                className="form-input w-64"
              />
            </div>
            
            {filterOptions.tenants && filterOptions.tenants.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tenant</label>
                <select
                  value={filters.tenant}
                  onChange={(e) => handleFilterChange('tenant', e.target.value)}
                  className="form-select"
                >
                  <option value="">All Tenants</option>
                  {filterOptions.tenants.map((tenant) => (
                    <option key={tenant.value} value={tenant.value}>
                      {tenant.label}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {filterOptions.roles && filterOptions.roles.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                <select
                  value={filters.role}
                  onChange={(e) => handleFilterChange('role', e.target.value)}
                  className="form-select"
                >
                  <option value="">All Roles</option>
                  {filterOptions.roles.map((role) => (
                    <option key={role.value} value={role.value}>
                      {role.label}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {filterOptions.creators && filterOptions.creators.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Created By</label>
                <select
                  value={filters.created_by}
                  onChange={(e) => handleFilterChange('created_by', e.target.value)}
                  className="form-select"
                >
                  <option value="">All Creators</option>
                  {filterOptions.creators.map((creator) => (
                    <option key={creator.value} value={creator.value}>
                      {creator.label}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {hasActiveFilters() && (
              <button
                onClick={clearFilters}
                className="flex items-center text-sm text-gray-600 hover:text-gray-800"
              >
                <XMarkIcon className="h-4 w-4 mr-1" />
                Clear Filters
              </button>
            )}
          </div>
          {hasActiveFilters() && (
            <div className="mt-3 flex flex-wrap gap-2">
              {filters.search && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  Search: "{filters.search}"
                  <button
                    onClick={() => handleFilterChange('search', '')}
                    className="ml-1 hover:bg-blue-200 rounded-full p-0.5"
                  >
                    <XMarkIcon className="h-3 w-3" />
                  </button>
                </span>
              )}
              {filters.tenant && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  Tenant: {filterOptions.tenants.find(t => t.value === filters.tenant)?.label}
                  <button
                    onClick={() => handleFilterChange('tenant', '')}
                    className="ml-1 hover:bg-green-200 rounded-full p-0.5"
                  >
                    <XMarkIcon className="h-3 w-3" />
                  </button>
                </span>
              )}
              {filters.role && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                  Role: {filterOptions.roles.find(r => r.value === filters.role)?.label}
                  <button
                    onClick={() => handleFilterChange('role', '')}
                    className="ml-1 hover:bg-purple-200 rounded-full p-0.5"
                  >
                    <XMarkIcon className="h-3 w-3" />
                  </button>
                </span>
              )}
              {filters.created_by && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                  Created by: {filterOptions.creators.find(c => c.value === filters.created_by)?.label}
                  <button
                    onClick={() => handleFilterChange('created_by', '')}
                    className="ml-1 hover:bg-orange-200 rounded-full p-0.5"
                  >
                    <XMarkIcon className="h-3 w-3" />
                  </button>
                </span>
              )}
              {activeTab !== 'all' && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                  Tab: {tabs.find(t => t.id === activeTab)?.name}
                  <button
                    onClick={() => setActiveTab('all')}
                    className="ml-1 hover:bg-yellow-200 rounded-full p-0.5"
                  >
                    <XMarkIcon className="h-3 w-3" />
                  </button>
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {/* Results Summary */}
      <div className="flex justify-between items-center text-sm text-gray-600">
        <span>
          Showing {filteredUsers.length} of {users.length} users
          {hasActiveFilters() && (
            <span className="text-blue-600 ml-1">(filtered)</span>
          )}
        </span>
      </div>

      {filteredUsers.length === 0 ? (
        <div className="text-center py-12">
          <UserIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            {users.length === 0 ? 'No users' : `No ${activeTab === 'all' ? '' : tabs.find(t => t.id === activeTab)?.name.toLowerCase() || ''} users`}
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            {users.length === 0 ? 'Get started by adding a new user.' : `No users found for the selected category.`}
          </p>
          {users.length === 0 && (
            <div className="mt-6">
              <button onClick={handleCreate} className="btn-primary">
                <PlusIcon className="h-5 w-5 mr-2" />
                Add User
              </button>
            </div>
          )}
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
                    Tenant
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created By
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
                {filteredUsers.map((user) => (
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {user.tenant_name || 'No tenant'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`badge ${user.is_active ? 'badge-green' : 'badge-red'}`}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {user.created_by_name || 'System'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(user.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleEdit(user)}
                        className="text-primary-600 hover:text-primary-900 mr-3"
                        title="Edit User"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      {currentUser?.role !== 'support_team' && (
                        <button
                          onClick={() => handleDelete(user)}
                          className="text-red-600 hover:text-red-900"
                          title="Delete User"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      )}
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
        <UserModal
          user={selectedUser}
          mode={modalMode}
          onClose={handleModalClose}
          onSuccess={handleModalSuccess}
        />
      )}
    </div>
  );
}