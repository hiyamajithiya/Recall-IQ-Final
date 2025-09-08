import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { authAPI } from '../utils/api';
import { 
  UserIcon, 
  KeyIcon, 
  EnvelopeIcon, 
  EyeIcon, 
  EyeSlashIcon,
  CheckCircleIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  StarIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import EmailConfigurationModal from '../components/Profile/EmailConfigurationModal';
import toast from 'react-hot-toast';

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
    tenant_admin: 'Tenant Admin',
    staff: 'Staff',
    user: 'User',
  };
  return roleNames[role] || role;
};

export default function Profile() {
  const { user, updateUser } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  // Email configurations state
  const [emailConfigurations, setEmailConfigurations] = useState([]);
  const [showEmailConfigModal, setShowEmailConfigModal] = useState(false);
  const [selectedEmailConfig, setSelectedEmailConfig] = useState(null);
  const [emailConfigModalMode, setEmailConfigModalMode] = useState('create');
  
  // Profile form state
  const [profileData, setProfileData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    username: ''
  });

  // Password form state
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setProfileData({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        username: user.username || ''
      });
      
      // Only fetch email configurations for super_admin and tenant_admin
      if (user.role === 'super_admin' || user.role === 'tenant_admin') {
        fetchEmailConfigurations();
      }
    }
  }, [user]);

  const fetchEmailConfigurations = async () => {
    try {
      const response = await authAPI.getEmailConfigurations();
      setEmailConfigurations(response.data?.results || response.data || []);
    } catch (error) {
      console.error('Failed to load email configurations:', error);
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || 'Failed to load email configurations';
      toast.error(errorMsg);
      setEmailConfigurations([]);
    }
  };

  const handleCreateEmailConfig = () => {
    setSelectedEmailConfig(null);
    setEmailConfigModalMode('create');
    setShowEmailConfigModal(true);
  };

  const handleEditEmailConfig = (config) => {
    setSelectedEmailConfig(config);
    setEmailConfigModalMode('edit');
    setShowEmailConfigModal(true);
  };

  const handleDeleteEmailConfig = async (config) => {
    if (window.confirm(`Are you sure you want to delete "${config.name}"?`)) {
      try {
        await authAPI.deleteEmailConfiguration(config.id);
        toast.success('Email configuration deleted successfully');
        fetchEmailConfigurations();
      } catch (error) {
        toast.error('Failed to delete email configuration');
      }
    }
  };

  const handleEmailConfigModalClose = () => {
    setShowEmailConfigModal(false);
    setSelectedEmailConfig(null);
  };

  const handleEmailConfigModalSuccess = () => {
    fetchEmailConfigurations();
    handleEmailConfigModalClose();
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const updateData = {
        first_name: profileData.first_name || '',
        last_name: profileData.last_name || '',
        email: profileData.email
      };
      
      if (!updateData.email) {
        toast.error('Email is required');
        return;
      }
      
      const response = await authAPI.updateProfile(updateData);
      updateUser(response.data);
      toast.success('Profile updated successfully');
    } catch (error) {
      console.error('Profile update error:', error);
      const errorMsg = error.response?.data?.error || 
                      error.response?.data?.detail || 
                      error.response?.data?.message || 
                      'Failed to update profile';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    
    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error('New passwords do not match');
      return;
    }
    
    if (passwordData.new_password.length < 8) {
      toast.error('Password must be at least 8 characters long');
      return;
    }

    setLoading(true);
    
    try {
      await authAPI.changePassword({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      });
      toast.success('Password changed successfully');
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.response?.data?.detail || 'Failed to change password';
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };


  const tabs = [
    { id: 'profile', name: 'Profile Information', icon: UserIcon },
    { id: 'password', name: 'Change Password', icon: KeyIcon },
    // Only show email configuration for super_admin and tenant_admin
    ...(user?.role === 'super_admin' || user?.role === 'tenant_admin' 
      ? [{ id: 'email', name: 'Email Configuration', icon: EnvelopeIcon }] 
      : [])
  ];

  return (
    <div className="space-y-6">
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            My Profile
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your account settings and email configuration.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center`}
            >
              <tab.icon className="h-5 w-5 mr-2" />
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Profile Information Tab */}
      {activeTab === 'profile' && (
        <div className="card">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Profile Information</h3>
            <p className="mt-1 text-sm text-gray-500">
              Update your personal information and account details.
            </p>
          </div>
          
          <form onSubmit={handleProfileUpdate} className="px-6 py-4 space-y-6">
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <div>
                <label className="form-label">First Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={profileData.first_name}
                  onChange={(e) => setProfileData({ ...profileData, first_name: e.target.value })}
                />
              </div>
              
              <div>
                <label className="form-label">Last Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={profileData.last_name}
                  onChange={(e) => setProfileData({ ...profileData, last_name: e.target.value })}
                />
              </div>
              
              <div>
                <label className="form-label">Username</label>
                <input
                  type="text"
                  className="form-input bg-gray-50"
                  value={profileData.username}
                  disabled
                />
                <p className="mt-1 text-xs text-gray-500">Username cannot be changed</p>
              </div>
              
              <div>
                <label className="form-label">Email</label>
                <input
                  type="email"
                  className="form-input"
                  value={profileData.email}
                  onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                />
              </div>

              <div>
                <label className="form-label">Role</label>
                <input
                  type="text"
                  className="form-input bg-gray-50"
                  value={getRoleDisplayName(user?.role)}
                  disabled
                />
              </div>

              <div>
                <label className="form-label">Tenant</label>
                <input
                  type="text"
                  className="form-input bg-gray-50"
                  value={user?.tenant_data?.name || user?.tenant_name || 'No tenant assigned'}
                  disabled
                />
              </div>

              <div>
                <label className="form-label">Account Created</label>
                <input
                  type="text"
                  className="form-input bg-gray-50"
                  value={user?.created_at ? formatDate(user.created_at) : 'N/A'}
                  disabled
                />
              </div>
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={loading}
                className="btn-primary"
              >
                {loading ? 'Updating...' : 'Update Profile'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Change Password Tab */}
      {activeTab === 'password' && (
        <div className="card">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Change Password</h3>
            <p className="mt-1 text-sm text-gray-500">
              Update your password to keep your account secure.
            </p>
          </div>
          
          <form onSubmit={handlePasswordChange} className="px-6 py-4 space-y-6">
            <div>
              <label className="form-label">Current Password</label>
              <div className="relative">
                <input
                  type={showCurrentPassword ? 'text' : 'password'}
                  className="form-input pr-12"
                  value={passwordData.current_password}
                  onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                  required
                  autoComplete="off"
                  data-lpignore="true"
                  data-1p-ignore="true"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center hover:bg-gray-50 rounded-r-md transition-colors duration-200 group"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  tabIndex={-1}
                >
                  {showCurrentPassword ? (
                    <EyeSlashIcon className="h-5 w-5 text-gray-400 group-hover:text-primary-500 transition-colors duration-200" />
                  ) : (
                    <EyeIcon className="h-5 w-5 text-gray-400 group-hover:text-primary-500 transition-colors duration-200" />
                  )}
                </button>
              </div>
            </div>

            <div>
              <label className="form-label">New Password</label>
              <div className="relative">
                <input
                  type={showNewPassword ? 'text' : 'password'}
                  className="form-input pr-12"
                  value={passwordData.new_password}
                  onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                  required
                  autoComplete="off"
                  data-lpignore="true"
                  data-1p-ignore="true"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center hover:bg-gray-50 rounded-r-md transition-colors duration-200 group"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  tabIndex={-1}
                >
                  {showNewPassword ? (
                    <EyeSlashIcon className="h-5 w-5 text-gray-400 group-hover:text-primary-500 transition-colors duration-200" />
                  ) : (
                    <EyeIcon className="h-5 w-5 text-gray-400 group-hover:text-primary-500 transition-colors duration-200" />
                  )}
                </button>
              </div>
            </div>

            <div>
              <label className="form-label">Confirm New Password</label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  className="form-input pr-12"
                  value={passwordData.confirm_password}
                  onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                  required
                  autoComplete="off"
                  data-lpignore="true"
                  data-1p-ignore="true"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center hover:bg-gray-50 rounded-r-md transition-colors duration-200 group"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  tabIndex={-1}
                >
                  {showConfirmPassword ? (
                    <EyeSlashIcon className="h-5 w-5 text-gray-400 group-hover:text-primary-500 transition-colors duration-200" />
                  ) : (
                    <EyeIcon className="h-5 w-5 text-gray-400 group-hover:text-primary-500 transition-colors duration-200" />
                  )}
                </button>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={loading}
                className="btn-primary"
              >
                {loading ? 'Changing...' : 'Change Password'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Email Configuration Tab - Only for super_admin and tenant_admin */}
      {activeTab === 'email' && (user?.role === 'super_admin' || user?.role === 'tenant_admin') && (
        <div className="card">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <div>
              <h3 className="text-lg font-medium text-gray-900">Email Configurations</h3>
              <p className="mt-1 text-sm text-gray-500">
                Manage your SMTP configurations for sending emails.
              </p>
            </div>
            <button
              onClick={handleCreateEmailConfig}
              className="btn-primary flex items-center"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              Add Configuration
            </button>
          </div>
          
          <div className="px-6 py-4">
            {emailConfigurations.length === 0 ? (
              <div className="text-center py-8">
                <EnvelopeIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No email configurations</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Get started by creating your first email configuration.
                </p>
                <div className="mt-6">
                  <button
                    onClick={handleCreateEmailConfig}
                    className="btn-primary"
                  >
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Add Your First Configuration
                  </button>
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {emailConfigurations.map((config) => (
                  <div
                    key={config.id}
                    className={`relative rounded-lg border-2 p-4 ${
                      config.is_default
                        ? 'border-green-200 bg-green-50'
                        : 'border-gray-200 bg-white'
                    }`}
                  >
                    {config.is_default && (
                      <div className="absolute -top-2 -right-2">
                        <StarIconSolid className="h-6 w-6 text-green-500" />
                      </div>
                    )}
                    
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="text-sm font-medium text-gray-900">
                          {config.name}
                        </h4>
                        <p className="text-sm text-gray-500 capitalize">
                          {config.provider}
                        </p>
                      </div>
                      
                      <div className="flex items-center space-x-2 ml-4">
                        <button
                          onClick={() => handleEditEmailConfig(config)}
                          className="text-gray-400 hover:text-gray-600"
                          title="Edit configuration"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteEmailConfig(config)}
                          className="text-gray-400 hover:text-red-600"
                          title="Delete configuration"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                    
                    <div className="mt-3">
                      <div className="text-xs text-gray-500">
                        <div><strong>Host:</strong> {config.email_host}</div>
                        <div><strong>Port:</strong> {config.email_port}</div>
                        <div><strong>From:</strong> {config.from_email}</div>
                      </div>
                    </div>
                    
                    <div className="mt-3 flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {config.is_default && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            <StarIcon className="h-3 w-3 mr-1" />
                            Default
                          </span>
                        )}
                        {config.is_active ? (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            Inactive
                          </span>
                        )}
                      </div>
                      
                      <div className="text-xs text-gray-400">
                        {config.email_use_tls ? 'TLS' : config.email_use_ssl ? 'SSL' : 'No Encryption'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Email Configuration Modal */}
      {showEmailConfigModal && (
        <EmailConfigurationModal
          config={selectedEmailConfig}
          mode={emailConfigModalMode}
          onClose={handleEmailConfigModalClose}
          onSuccess={handleEmailConfigModalSuccess}
          currentUser={user}
        />
      )}
    </div>
  );
}