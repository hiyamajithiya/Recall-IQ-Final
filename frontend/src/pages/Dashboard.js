import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { authAPI } from '../utils/api';
import SuperAdminDashboard from '../components/Dashboard/SuperAdminDashboard';
import TenantDashboard from '../components/Dashboard/TenantDashboard';
import toast from 'react-hot-toast';

export default function Dashboard() {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      fetchDashboardData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Use different endpoint based on user role for better performance
      let response;
      if (user?.role === 'super_admin' || user?.role === 'support_team') {
        response = await authAPI.getDashboard(); // Faster super admin endpoint
      } else {
        response = await authAPI.getTenantDashboard(); // Tenant-specific endpoint
      }
      
      setDashboardData(response.data);
    } catch (error) {
      console.error('Dashboard error:', error);
      toast.error('Failed to load dashboard data');
      
      // Set minimal dashboard data to prevent complete failure
      setDashboardData({
        user: user,
        tenant: null,
        role: user?.role,
        permissions: []
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading || !user) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-sm text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <p className="text-sm text-gray-600">Dashboard data unavailable</p>
          <button 
            onClick={fetchDashboardData}
            className="mt-2 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const overview = dashboardData?.overview || {};
  const recentBatches = dashboardData?.recent_batches || [];
  const recentEmailActivity = dashboardData?.recent_email_activity || [];
  const upcomingBatches = dashboardData?.upcoming_batches || [];
  const emailActivityChart = dashboardData?.email_activity_chart || [];
  const recentTenants = dashboardData?.recent_tenants || [];
  const systemHealth = dashboardData?.system_health || {};



  return (
    <div>
      {(user?.role === 'super_admin' || user?.role === 'support_team') ? (
        <SuperAdminDashboard 
          user={user}
          dashboardData={dashboardData}
          overview={overview}
          recentTenants={recentTenants}
          systemHealth={systemHealth}
        />
      ) : (
        <TenantDashboard 
          user={user}
          overview={overview}
          recentBatches={recentBatches}
          recentEmailActivity={recentEmailActivity}
          upcomingBatches={upcomingBatches}
          emailActivityChart={emailActivityChart}
          dashboardData={dashboardData}
        />
      )}
    </div>
  );
}