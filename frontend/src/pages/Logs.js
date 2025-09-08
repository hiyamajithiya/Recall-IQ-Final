import React, { useState, useEffect } from 'react';
import { logsAPI } from '../utils/api';
import { useAuth } from '../context/AuthContext';
import { DocumentArrowDownIcon, FunnelIcon, BuildingOfficeIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const getStatusBadge = (status) => {
  const statusClasses = {
    sent: 'badge-green',
    failed: 'badge-red',
    queued: 'badge-yellow',
    delivered: 'badge-blue',
    opened: 'badge-blue',
    bounced: 'badge-red',
    spam: 'badge-red',
  };
  return statusClasses[status] || 'badge-gray';
};

const getTypeIcon = (type) => {
  const icons = {
    batch: '📧',
    test: '🧪',
    manual: '✋',
    welcome: '👋',
    notification: '🔔',
  };
  return icons[type] || '📧';
};

const getDirectionBadge = (direction) => {
  const directionClasses = {
    outgoing: 'bg-green-100 text-green-800',  // Green for "Sent"
    incoming: 'bg-blue-100 text-blue-800',   // Blue for "Received"
  };
  const directionLabels = {
    outgoing: 'Sent',
    incoming: 'Received',
  };
  return {
    className: directionClasses[direction] || 'bg-gray-100 text-gray-800',
    label: directionLabels[direction] || direction
  };
};

export default function Logs() {
  const { user } = useAuth();
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [tenantUsage, setTenantUsage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showTenantUsage, setShowTenantUsage] = useState(false);
  const [filters, setFilters] = useState({
    email_type: '',
    status: '',
    search: '',
  });

  useEffect(() => {
    fetchLogs();
    fetchStats();
    if (user?.role === 'super_admin' || user?.role === 'support_team') {
      fetchTenantUsage();
    }
  }, [filters, user?.role]);

  const fetchLogs = async () => {
    try {
      const params = Object.fromEntries(
        Object.entries(filters).filter(([_, value]) => value !== '')
      );
      const response = await logsAPI.getEmailLogs(params);
      setLogs(response.data.results || response.data);
    } catch (error) {
      toast.error('Failed to load email logs');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await logsAPI.getEmailLogStats();
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats');
    }
  };

  const fetchTenantUsage = async () => {
    try {
      const response = await logsAPI.getTenantUsage();
      setTenantUsage(response.data);
    } catch (error) {
      console.error('Failed to load tenant usage stats');
    }
  };

  const handleDocumentsReceivedChange = async (logId, documentsReceived) => {
    try {
      await logsAPI.markDocumentsReceived(logId, { documents_received: documentsReceived });
      
      // Update the local logs state
      setLogs(prevLogs => 
        prevLogs.map(log => 
          log.id === logId 
            ? { 
                ...log, 
                documents_received: documentsReceived,
                documents_received_by_email: documentsReceived ? user.email : null,
                documents_received_at: documentsReceived ? new Date().toISOString() : null
              }
            : log
        )
      );
      
      toast.success(
        documentsReceived 
          ? 'Documents marked as received' 
          : 'Documents unmarked as received'
      );
    } catch (error) {
      console.error('Error updating documents received status:', error);
      toast.error('Failed to update documents received status');
    }
  };

  const handleExport = async () => {
    try {
      const response = await logsAPI.exportEmailLogs();
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'email_logs.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Email logs exported successfully');
    } catch (error) {
      toast.error('Failed to export logs');
    }
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
            Email Logs
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            {(user?.role === 'super_admin' || user?.role === 'support_team') 
              ? 'Monitor all tenant email activity and subscription usage tracking'
              : 'Monitor all email activity and delivery status'}
          </p>
        </div>
        <div className="mt-4 flex space-x-2 md:mt-0 md:ml-4">
          {(user?.role === 'super_admin' || user?.role === 'support_team') && (
            <button
              onClick={() => setShowTenantUsage(!showTenantUsage)}
              className={`btn-secondary flex items-center ${showTenantUsage ? 'bg-primary-100 text-primary-700' : ''}`}
            >
              <BuildingOfficeIcon className="h-5 w-5 mr-2" />
              Tenant Usage
            </button>
          )}
          <button
            onClick={handleExport}
            className="btn-secondary flex items-center"
          >
            <DocumentArrowDownIcon className="h-5 w-5 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div className="card p-6">
            <div className="text-2xl font-semibold text-gray-900">{stats.total_emails}</div>
            <div className="text-sm text-gray-500">Total Emails</div>
          </div>
          <div className="card p-6">
            <div className="text-2xl font-semibold text-green-600">{stats.sent_emails}</div>
            <div className="text-sm text-gray-500">
              {(user?.role === 'super_admin' || user?.role === 'support_team') ? 'Sent Successfully' : 'Sent by You'}
            </div>
          </div>
          {(user?.role !== 'super_admin' && user?.role !== 'support_team') && stats.received_emails !== undefined && (
            <div className="card p-6">
              <div className="text-2xl font-semibold text-blue-600">{stats.received_emails}</div>
              <div className="text-sm text-gray-500">Received</div>
            </div>
          )}
          <div className="card p-6">
            <div className="text-2xl font-semibold text-red-600">{stats.failed_emails}</div>
            <div className="text-sm text-gray-500">Failed</div>
          </div>
          <div className="card p-6">
            <div className="text-2xl font-semibold text-primary-600">{stats.success_rate}%</div>
            <div className="text-sm text-gray-500">Success Rate</div>
          </div>
        </div>
      )}

      {/* Tenant Usage Statistics - Super Admin Only */}
      {(user?.role === 'super_admin' || user?.role === 'support_team') && showTenantUsage && tenantUsage && (
        <div className="card overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Tenant Email Usage Statistics</h3>
            <p className="mt-1 text-sm text-gray-500">
              Monitor tenant subscription usage and email limits
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tenant
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Plan
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Monthly Usage
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Usage %
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Emails Received
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Success Rate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {tenantUsage.tenant_statistics.map((tenant) => (
                  <tr key={tenant.tenant_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <BuildingOfficeIcon className="h-5 w-5 text-gray-400 mr-3" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">{tenant.tenant_name}</div>
                          <div className="text-sm text-gray-500">ID: {tenant.tenant_id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`badge ${
                        tenant.plan === 'starter' ? 'badge-blue' :
                        tenant.plan === 'professional' ? 'badge-purple' :
                        tenant.plan === 'enterprise' ? 'badge-indigo' : 'badge-gray'
                      }`}>
                        {tenant.plan.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {tenant.current_month_usage} / {tenant.monthly_limit === 0 ? '∞' : tenant.monthly_limit}
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                        <div 
                          className={`h-2 rounded-full ${
                            tenant.usage_percentage > 90 ? 'bg-red-500' :
                            tenant.usage_percentage > 75 ? 'bg-yellow-500' : 'bg-green-500'
                          }`}
                          style={{width: `${Math.min(tenant.usage_percentage, 100)}%`}}
                        />
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`text-sm font-medium ${
                        tenant.usage_percentage > 90 ? 'text-red-600' :
                        tenant.usage_percentage > 75 ? 'text-yellow-600' : 'text-green-600'
                      }`}>
                        {tenant.usage_percentage}%
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {tenant.total_emails_received || 0}
                      </div>
                      <div className="text-xs text-gray-500">Notifications & Welcome</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900">{tenant.success_rate}%</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`badge ${
                        tenant.status === 'active' ? 'badge-green' :
                        tenant.status === 'trial' ? 'badge-yellow' :
                        tenant.status === 'suspended' ? 'badge-orange' : 'badge-red'
                      }`}>
                        {tenant.status.toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Filters */}
      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap items-center gap-4">
          <FunnelIcon className="h-5 w-5 text-gray-400" />

          <div className="w-40">
            <select
              value={filters.email_type}
              onChange={(e) => setFilters({ ...filters, email_type: e.target.value })}
              className="form-input w-full"
            >
              <option value="">All Types</option>
              <option value="batch">Batch</option>
              <option value="test">Test</option>
              <option value="manual">Manual</option>
            </select>
          </div>

          <div className="w-40">
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="form-input w-full"
            >
              <option value="">All Status</option>
              <option value="sent">Sent</option>
              <option value="failed">Failed</option>
              <option value="queued">Queued</option>
              <option value="delivered">Delivered</option>
            </select>
          </div>

          <div className="flex-1 min-w-[200px]">
            <input
              type="text"
              placeholder="Search emails..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="form-input w-full"
            />
          </div>
        </div>
      </div>


      {/* Logs Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                {user?.role === 'super_admin' && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tenant
                  </th>
                )}
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Recipient
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Subject
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Documents Received
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Sent At
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className="text-lg mr-2">{getTypeIcon(log.email_type)}</span>
                      <span className="text-sm text-gray-900 capitalize">{log.email_type}</span>
                    </div>
                  </td>
                  {user?.role === 'super_admin' && (
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <BuildingOfficeIcon className="h-4 w-4 text-gray-400 mr-2" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">{log.tenant_name}</div>
                          <div className="text-xs text-gray-500">Tenant ID: {log.tenant}</div>
                        </div>
                      </div>
                    </td>
                  )}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{log.to_email}</div>
                    <div className="text-sm text-gray-500">From: {log.from_email}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900 truncate max-w-xs" title={log.subject}>
                      {log.subject}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`badge ${getStatusBadge(log.status)}`}>
                      {log.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {log.email_type === 'batch' ? (
                      <div className="flex items-center">
                        <input
                          type="checkbox"
                          checked={log.documents_received || false}
                          onChange={(e) => handleDocumentsReceivedChange(log.id, e.target.checked)}
                          className="h-4 w-4 text-recalliq-600 focus:ring-recalliq-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-700">
                          {log.documents_received ? 'Yes' : 'No'}
                        </span>
                        {log.documents_received && log.documents_received_by_email && (
                          <div className="ml-2 text-xs text-gray-500">
                            by {log.documents_received_by_email}
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="text-sm text-gray-400">N/A</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {log.sent_at
                      ? new Date(log.sent_at).toLocaleString()
                      : new Date(log.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {logs.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No email logs found</p>
          </div>
        )}
      </div>
    </div>
  );
}