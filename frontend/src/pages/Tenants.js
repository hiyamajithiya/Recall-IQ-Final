import React, { useState, useEffect } from 'react';
import { tenantsAPI } from '../utils/api';
import { useAuth } from '../context/AuthContext';
import { PlusIcon, PencilIcon, BuildingOfficeIcon, EnvelopeIcon, TrashIcon, ExclamationTriangleIcon, BellIcon } from '@heroicons/react/24/outline';
import ProviderListModal from '../components/Email/ProviderListModal';
import TenantModal from '../components/Tenants/TenantModal';
import toast from 'react-hot-toast';

export default function Tenants() {
  const { user: currentUser } = useAuth();
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showProviderModal, setShowProviderModal] = useState(false);
  const [showTenantModal, setShowTenantModal] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState(null);
  const [modalMode, setModalMode] = useState('create');
  const [sendingNotifications, setSendingNotifications] = useState({});
  const [statusFilter, setStatusFilter] = useState('all');
  const [planFilter, setPlanFilter] = useState('all');

  useEffect(() => {
    fetchTenants();
  }, []);

  const fetchTenants = async () => {
    try {
      const response = await tenantsAPI.getTenants();
      setTenants(response.data.results || response.data);
    } catch (error) {
      toast.error('Failed to load tenants');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTenant = () => {
    setSelectedTenant(null);
    setModalMode('create');
    setShowTenantModal(true);
  };

  const handleEditTenant = (tenant) => {
    setSelectedTenant(tenant);
    setModalMode('edit');
    setShowTenantModal(true);
  };

  const handleDeleteTenant = async (tenant) => {
    if (window.confirm(`Are you sure you want to delete ${tenant.name}? This action cannot be undone.`)) {
      try {
        await tenantsAPI.deleteTenant(tenant.id);
        toast.success('Tenant deleted successfully');
        fetchTenants();
      } catch (error) {
        toast.error('Failed to delete tenant');
      }
    }
  };

  const handleModalSuccess = () => {
    setShowTenantModal(false);
    fetchTenants();
  };

  const sendNotification = async (tenant, notificationType) => {
    const notificationKey = `${tenant.id}-${notificationType}`;
    setSendingNotifications(prev => ({ ...prev, [notificationKey]: true }));
    
    try {
      let response;
      const api = `http://localhost:8000/api/tenants/${tenant.id}`;
      
      switch (notificationType) {
        case 'trial_expiry':
          response = await fetch(`${api}/send_trial_expiry_notification/`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
              'Content-Type': 'application/json',
            },
          });
          break;
        case 'renewal':
          response = await fetch(`${api}/send_renewal_notification/`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
              'Content-Type': 'application/json',
            },
          });
          break;
        case 'custom':
          response = await fetch(`${api}/send_custom_notification/`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              type: 'generic_update',
              changes: {
                'account_info': { 'old': 'previous', 'new': 'updated' }
              }
            }),
          });
          break;
        default:
          throw new Error('Invalid notification type');
      }
      
      if (response.ok) {
        const data = await response.json();
        toast.success(data.message || `${notificationType} notification sent successfully`);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to send notification');
      }
    } catch (error) {
      console.error('Notification error:', error);
      toast.error(error.message || 'Failed to send notification');
    } finally {
      setSendingNotifications(prev => {
        const newState = { ...prev };
        delete newState[notificationKey];
        return newState;
      });
    }
  };

  const showNotificationMenu = (tenant) => {
    // First ask if user wants to send a notification at all
    const wantToSend = window.confirm(
      `Send a notification to ${tenant.name}?\n\n` +
      `Note: Automatic notifications are already sent when you make changes to tenant settings.\n` +
      `This is for manual notifications only.\n\n` +
      `Click OK to choose notification type, or Cancel to go back.`
    );
    
    if (!wantToSend) {
      return; // User cancelled, exit without sending
    }

    // Show notification type selection
    const notificationType = prompt(
      `Choose notification type for ${tenant.name}:\n\n` +
      `1 - Trial Expiry Notice\n` +
      `2 - Subscription Renewal\n` +
      `3 - Account Update\n\n` +
      `Enter 1, 2, or 3 (or press Cancel to go back):`
    );
    
    if (!notificationType) {
      return; // User cancelled
    }

    let typeKey;
    switch (notificationType.trim()) {
      case '1':
        typeKey = 'trial_expiry';
        break;
      case '2':
        typeKey = 'renewal';
        break;
      case '3':
        typeKey = 'custom';
        break;
      default:
        alert('Invalid selection. Please try again.');
        return;
    }

    // Send the selected notification
    sendNotification(tenant, typeKey);
  };

  const filterTenants = (tenants) => {
    return tenants.filter(tenant => {
      const statusMatch = statusFilter === 'all' || tenant.status === statusFilter;
      const planMatch = planFilter === 'all' || tenant.plan === planFilter;
      return statusMatch && planMatch;
    });
  };

  const getStatusBadge = (status, isExpired = false, expiresSoon = false) => {
    const statusClasses = {
      trial: 'badge-yellow',
      active: 'badge-green',
      suspended: 'badge-orange',
      cancelled: 'badge-red',
      expired: 'badge-red border-red-500 bg-red-100 text-red-800 font-bold',
    };
    
    if (isExpired) {
      return 'badge-red border-red-500 bg-red-100 text-red-800 font-bold animate-pulse';
    }
    if (expiresSoon) {
      return 'badge-orange border-orange-500 bg-orange-100 text-orange-800 font-bold';
    }
    
    return statusClasses[status] || 'badge-gray';
  };

  const getPlanBadge = (plan) => {
    const planClasses = {
      starter: 'badge-blue',
      professional: 'badge-purple',
      enterprise: 'badge-indigo',
      custom: 'badge-gray',
    };
    return planClasses[plan] || 'badge-gray';
  };

  const getTenantCardClass = (tenant) => {
    let baseClass = 'card overflow-hidden';
    
    if (tenant.is_expired) {
      baseClass += ' border-red-500 bg-red-50 shadow-red-200';
    } else if (tenant.expires_soon) {
      baseClass += ' border-orange-500 bg-orange-50 shadow-orange-200';
    }
    
    return baseClass;
  };

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
            SaaS Tenant Management
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage customer subscriptions, billing, and tenant organizations.
          </p>
        </div>
        <div className="mt-4 flex space-x-3 md:mt-0 md:ml-4">
          <button 
            onClick={() => setShowProviderModal(true)}
            className="btn-secondary flex items-center"
          >
            <EnvelopeIcon className="h-5 w-5 mr-2" />
            Email Providers
          </button>
          {(currentUser?.role === 'super_admin' || currentUser?.role === 'support_team') && (
            <button onClick={handleCreateTenant} className="btn-primary flex items-center">
              <PlusIcon className="h-5 w-5 mr-2" />
              Add Tenant
            </button>
          )}
        </div>
      </div>

      {/* Filter Controls */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
        <div className="flex flex-wrap gap-4 items-center">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status Filter</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="form-select"
            >
              <option value="all">All Statuses</option>
              <option value="trial">Trial</option>
              <option value="active">Active</option>
              <option value="suspended">Suspended</option>
              <option value="cancelled">Cancelled</option>
              <option value="expired">Expired</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Plan Filter</label>
            <select
              value={planFilter}
              onChange={(e) => setPlanFilter(e.target.value)}
              className="form-select"
            >
              <option value="all">All Plans</option>
              <option value="starter">Starter</option>
              <option value="professional">Professional</option>
              <option value="enterprise">Enterprise</option>
              <option value="custom">Custom</option>
            </select>
          </div>
        </div>
      </div>

      {tenants.length === 0 ? (
        <div className="text-center py-12">
          <BuildingOfficeIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No tenants</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by adding a new tenant.</p>
          <div className="mt-6">
            {(currentUser?.role === 'super_admin' || currentUser?.role === 'support_team') && (
              <button onClick={handleCreateTenant} className="btn-primary">
                <PlusIcon className="h-5 w-5 mr-2" />
                Add Tenant
              </button>
            )}
          </div>
        </div>
      ) : (
        <>
          {/* Results Summary */}
          <div className="text-sm text-gray-600">
            Showing {filterTenants(tenants).length} of {tenants.length} tenants
          </div>
          
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {filterTenants(tenants).map((tenant) => (
              <div key={tenant.id} className={getTenantCardClass(tenant)}>
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    {tenant.logo ? (
                      <img
                        className="h-10 w-10 rounded-lg object-cover"
                        src={tenant.logo}
                        alt={tenant.name}
                      />
                    ) : (
                      <div className="h-10 w-10 rounded-lg bg-primary-100 flex items-center justify-center">
                        <BuildingOfficeIcon className="h-6 w-6 text-primary-600" />
                      </div>
                    )}
                    <div className="ml-3">
                      <h3 className="text-lg font-medium text-gray-900 truncate">
                        {tenant.name}
                      </h3>
                      <p className="text-sm text-gray-500">{tenant.contact_email}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button 
                      onClick={() => showNotificationMenu(tenant)}
                      className="text-gray-400 hover:text-blue-600"
                      title="Send notification"
                      disabled={Object.keys(sendingNotifications).some(key => key.startsWith(`${tenant.id}-`))}
                    >
                      <BellIcon className="h-5 w-5" />
                    </button>
                    <button 
                      onClick={() => handleEditTenant(tenant)}
                      className="text-gray-400 hover:text-primary-600"
                      title="Edit tenant"
                    >
                      <PencilIcon className="h-5 w-5" />
                    </button>
                    {currentUser?.role !== 'support_team' && (
                      <button 
                        onClick={() => handleDeleteTenant(tenant)}
                        className="text-gray-400 hover:text-red-600"
                        title="Delete tenant"
                      >
                        <TrashIcon className="h-5 w-5" />
                      </button>
                    )}
                  </div>
                </div>
                
                {/* Plan and Status Badges */}
                <div className="flex items-center justify-between mb-3">
                  <span className={`badge ${getPlanBadge(tenant.plan)}`}>
                    {tenant.plan?.replace('_', ' ').toUpperCase() || 'STARTER'}
                  </span>
                  <span className={getStatusBadge(tenant.status, tenant.is_expired, tenant.expires_soon)}>
                    {tenant.is_expired ? 'EXPIRED' : (tenant.status?.toUpperCase() || 'TRIAL')}
                    {tenant.is_expired && ' ⚠️'}
                    {tenant.expires_soon && !tenant.is_expired && ' ⏰'}
                  </span>
                </div>

                {/* Email Usage */}
                <div className="mb-3">
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Email Usage</span>
                    <span>{tenant.emails_sent_this_month_countable || 0} / {tenant.monthly_email_limit || 1000}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        (tenant.email_usage_percentage || 0) > 80 ? 'bg-red-500' : 
                        (tenant.email_usage_percentage || 0) > 60 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      style={{width: `${Math.min(tenant.email_usage_percentage || 0, 100)}%`}}
                    ></div>
                  </div>
                </div>

                {/* Days until expiry */}
                {tenant.days_until_expiry !== undefined && tenant.days_until_expiry < 30 && (
                  <div className="flex items-center text-sm text-orange-600 mb-3">
                    <ExclamationTriangleIcon className="h-4 w-4 mr-1" />
                    <span>{tenant.days_until_expiry} days until expiry</span>
                  </div>
                )}
                
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>Created: {new Date(tenant.created_at).toLocaleDateString()}</span>
                  <span className="font-medium">{tenant.contact_person || 'No contact'}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
        </>
      )}

      {/* Email Provider Modal */}
      {showProviderModal && (
        <ProviderListModal
          onClose={() => setShowProviderModal(false)}
        />
      )}

      {/* Tenant Modal */}
      {showTenantModal && (
        <TenantModal
          tenant={selectedTenant}
          mode={modalMode}
          onClose={() => setShowTenantModal(false)}
          onSuccess={handleModalSuccess}
        />
      )}
    </div>
  );
}