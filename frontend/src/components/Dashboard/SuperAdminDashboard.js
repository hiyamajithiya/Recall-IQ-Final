import React from 'react';
import StatsCard from './StatsCard';
import {
  BuildingOfficeIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ServerIcon,
} from '@heroicons/react/24/outline';

export default function SuperAdminDashboard({ user, dashboardData, overview, recentTenants, systemHealth }) {
  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            {user?.role === 'super_admin' ? 'Super Admin Dashboard' : 'Support Team Dashboard'}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            System-wide overview and management console.
          </p>
        </div>
      </div>

      {/* SaaS Business Metrics */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Customers"
          value={overview.total_tenants || 0}
          icon={BuildingOfficeIcon}
        />
        <StatsCard
          title="Active Subscriptions"
          value={overview.active_tenants || 0}
          icon={CheckCircleIcon}
        />
        <StatsCard
          title="Trial Accounts"
          value={overview.trial_tenants || 0}
          icon={ExclamationTriangleIcon}
        />
        <StatsCard
          title="Monthly Revenue"
          value={`$${(overview.monthly_revenue || 0).toLocaleString()}`}
          icon={ServerIcon}
        />
      </div>

      {/* Email Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Successful Emails Sent"
          value={overview.total_emails_sent || 0}
          icon={CheckCircleIcon}
        />
        <StatsCard
          title="Total Emails Failed"
          value={overview.total_emails_failed || 0}
          icon={ExclamationTriangleIcon}
        />
        <StatsCard
          title="Success Rate"
          value={`${overview.success_rate?.toFixed(1) || 0}%`}
          icon={CheckCircleIcon}
        />
        <StatsCard
          title="System Status"
          value="Operational"
          icon={ServerIcon}
        />
      </div>

      {/* System Health */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">System Health</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="flex items-center">
            <div className={`w-3 h-3 rounded-full mr-3 ${systemHealth.database ? 'bg-green-400' : 'bg-red-400'}`}></div>
            <span className="text-sm text-gray-700">Database</span>
          </div>
          <div className="flex items-center">
            <div className={`w-3 h-3 rounded-full mr-3 ${systemHealth.redis ? 'bg-green-400' : 'bg-red-400'}`}></div>
            <span className="text-sm text-gray-700">Redis Cache</span>
          </div>
          <div className="flex items-center">
            <div className={`w-3 h-3 rounded-full mr-3 ${systemHealth.email_queue ? 'bg-green-400' : 'bg-red-400'}`}></div>
            <span className="text-sm text-gray-700">Email Queue</span>
          </div>
        </div>
      </div>

      {/* Recent Customer Signups */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Customer Signups</h3>
        {recentTenants.length > 0 ? (
          <div className="space-y-4">
            {recentTenants.map((tenant) => (
              <div key={tenant.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <div className="h-10 w-10 rounded-lg bg-primary-100 flex items-center justify-center mr-3">
                    <BuildingOfficeIcon className="h-6 w-6 text-primary-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{tenant.name}</p>
                    <p className="text-xs text-gray-500">{tenant.contact_email}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className={`text-xs px-2 py-1 rounded ${
                        tenant.plan === 'enterprise' ? 'bg-purple-100 text-purple-800' :
                        tenant.plan === 'professional' ? 'bg-blue-100 text-blue-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {tenant.plan?.toUpperCase() || 'STARTER'}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded ${
                        tenant.status === 'active' ? 'bg-green-100 text-green-800' :
                        tenant.status === 'trial' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {tenant.status?.toUpperCase() || 'TRIAL'}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-xs text-gray-500">
                    {new Date(tenant.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-500">No customers yet</p>
          </div>
        )}
      </div>
    </div>
  );
}