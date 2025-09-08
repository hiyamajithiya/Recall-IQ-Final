import React from 'react';
import StatsCard from './StatsCard';
import EmailActivityChart from './EmailActivityChart';
import RecentActivity from './RecentActivity';
import UpcomingBatches from './UpcomingBatches';
import {
  EnvelopeIcon,
  UserGroupIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  UsersIcon,
} from '@heroicons/react/24/outline';

export default function TenantDashboard({ 
  user, 
  overview, 
  recentBatches, 
  recentEmailActivity, 
  upcomingBatches, 
  emailActivityChart, 
  dashboardData 
}) {
  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Welcome back, {user?.first_name || user?.username}!
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Here's what's happening with your email campaigns today.
          </p>
        </div>
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Total Templates"
          value={overview.total_templates || 0}
          icon={DocumentTextIcon}
        />
        <StatsCard
          title="Contact Groups"
          value={overview.total_groups || 0}
          icon={UserGroupIcon}
        />
        <StatsCard
          title="Active Batches"
          value={overview.active_batches || 0}
          icon={EnvelopeIcon}
        />
        <StatsCard
          title="Total Contacts"
          value={overview.total_contacts || 0}
          icon={UsersIcon}
        />
      </div>

      {/* Email Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatsCard
          title="Emails Sent"
          value={overview.emails_sent || 0}
          icon={CheckCircleIcon}
        />
        <StatsCard
          title="Emails Received"
          value={overview.emails_received || 0}
          icon={EnvelopeIcon}
        />
        <StatsCard
          title="Emails Failed"
          value={overview.total_emails_failed || 0}
          icon={ExclamationTriangleIcon}
        />
        <StatsCard
          title="Success Rate"
          value={`${overview.success_rate || 0}%`}
          icon={CheckCircleIcon}
        />
      </div>

      {/* User Limits Section */}
      {dashboardData?.user?.tenant_id && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900 flex items-center">
              <UsersIcon className="h-5 w-5 mr-2 text-blue-600" />
              User Management
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Current user allocation for your organization
            </p>
          </div>
          <div className="px-6 py-4">
            {dashboardData?.tenant?.current_user_counts ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Tenant Admins */}
                <div className="bg-purple-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium text-purple-900">Tenant Admins</div>
                    <div className="text-xs text-purple-600">
                      {dashboardData.tenant.current_user_counts.tenant_admin}/{dashboardData.tenant.max_tenant_admins}
                    </div>
                  </div>
                  <div className="mt-2">
                    <div className="bg-purple-200 rounded-full h-2">
                      <div 
                        className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                        style={{ 
                          width: `${Math.min(100, (dashboardData.tenant.current_user_counts.tenant_admin / dashboardData.tenant.max_tenant_admins) * 100)}%` 
                        }}
                      ></div>
                    </div>
                  </div>
                </div>

                {/* Staff Admins */}
                <div className="bg-green-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium text-green-900">Staff Admins</div>
                    <div className="text-xs text-green-600">
                      {dashboardData.tenant.current_user_counts.staff_admin}/{dashboardData.tenant.max_staff_admins}
                    </div>
                  </div>
                  <div className="mt-2">
                    <div className="bg-green-200 rounded-full h-2">
                      <div 
                        className="bg-green-600 h-2 rounded-full transition-all duration-300"
                        style={{ 
                          width: `${Math.min(100, (dashboardData.tenant.current_user_counts.staff_admin / dashboardData.tenant.max_staff_admins) * 100)}%` 
                        }}
                      ></div>
                    </div>
                  </div>
                </div>

                {/* Staff Users */}
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium text-blue-900">Staff Users</div>
                    <div className="text-xs text-blue-600">
                      {(dashboardData.tenant.current_user_counts.staff || 0) + (dashboardData.tenant.current_user_counts.sales_team || 0)}/{dashboardData.tenant.max_staff_users}
                    </div>
                  </div>
                  <div className="mt-2">
                    <div className="bg-blue-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ 
                          width: `${Math.min(100, ((dashboardData.tenant.current_user_counts.staff + dashboardData.tenant.current_user_counts.sales_team) / dashboardData.tenant.max_staff_users) * 100)}%` 
                        }}
                      ></div>
                    </div>
                  </div>
                </div>

                {/* Total Users */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium text-gray-900">Total Users</div>
                    <div className="text-xs text-gray-600">
                      {dashboardData.tenant.current_user_counts.total}/{dashboardData.tenant.max_total_users}
                    </div>
                  </div>
                  <div className="mt-2">
                    <div className="bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full transition-all duration-300 ${
                          dashboardData.tenant.user_usage_percentage >= 90 ? 'bg-red-600' : 
                          dashboardData.tenant.user_usage_percentage >= 70 ? 'bg-yellow-500' : 'bg-gray-600'
                        }`}
                        style={{ 
                          width: `${Math.min(100, dashboardData.tenant.user_usage_percentage)}%` 
                        }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-sm text-gray-500">
                User limit information not available
              </div>
            )}
          </div>
        </div>
      )}

      {/* Charts and Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <EmailActivityChart data={emailActivityChart} />
        <RecentActivity activities={recentEmailActivity} />
      </div>

      {/* Recent Batches and Upcoming */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Batches */}
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Batches</h3>
          {recentBatches.length > 0 ? (
            <div className="space-y-4">
              {recentBatches.map((batch) => (
                <div key={batch.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{batch.name}</p>
                    <p className="text-xs text-gray-500">Template: {batch.template_name}</p>
                    <div className="flex items-center space-x-4 mt-1">
                      <span className="text-xs text-gray-500">
                        {batch.total_recipients} recipients
                      </span>
                      <span className="text-xs text-gray-500">
                        {batch.emails_sent} sent
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`badge ${
                      batch.status === 'completed' ? 'badge-green' :
                      batch.status === 'running' ? 'badge-blue' :
                      batch.status === 'failed' ? 'badge-red' :
                      'badge-yellow'
                    }`}>
                      {batch.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">No recent batches</p>
            </div>
          )}
        </div>

        <UpcomingBatches batches={upcomingBatches} />
      </div>

      {/* Performance Summary */}
      {dashboardData?.performance_metrics && (
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Summary (Last 30 Days)</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-semibold text-gray-900">
                {dashboardData.performance_metrics.emails_last_30_days}
              </p>
              <p className="text-sm text-gray-500">Emails Sent</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-semibold text-gray-900">
                {dashboardData.performance_metrics.batches_last_30_days}
              </p>
              <p className="text-sm text-gray-500">Batches Created</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-semibold text-gray-900">
                {dashboardData.performance_metrics.avg_emails_per_batch}
              </p>
              <p className="text-sm text-gray-500">Avg Emails/Batch</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-semibold text-gray-900">
                {overview.success_rate || 0}%
              </p>
              <p className="text-sm text-gray-500">Success Rate</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}