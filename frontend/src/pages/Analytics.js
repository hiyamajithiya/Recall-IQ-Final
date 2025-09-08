import React, { useState, useEffect, useMemo } from 'react';
import { logsAPI } from '../utils/api';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement,
} from 'chart.js';
import toast from 'react-hot-toast';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement
);

export default function Analytics() {
  const [dailyStats, setDailyStats] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(30);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchAnalytics();
  }, [period]);

  const fetchAnalytics = async () => {
    // Set refreshing state when not initial load
    if (!loading) {
      setRefreshing(true);
    }
    
    try {
      // Calculate date range for filtered stats
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(endDate.getDate() - period);
      
      const [dailyResponse, statsResponse] = await Promise.all([
        logsAPI.getDailyStats(period),
        logsAPI.getEmailLogStats()
      ]);
      
      setDailyStats(dailyResponse.data);
      setStats(statsResponse.data);
      
      // Debug: Log the stats data to console
      console.log('Stats Data:', statsResponse.data);
      console.log('By Status:', statsResponse.data?.by_status);
      console.log('By Type:', statsResponse.data?.by_type);
      
    } catch (error) {
      console.error('Analytics fetch error:', error);
      toast.error('Failed to load analytics data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Daily chart data
  const dailyChartData = {
    labels: dailyStats.map(item => new Date(item.date).toLocaleDateString()),
    datasets: [
      {
        label: 'Sent',
        data: dailyStats.map(item => item.sent),
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.4,
      },
      {
        label: 'Failed',
        data: dailyStats.map(item => item.failed),
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.4,
      },
    ],
  };

  // Enhanced data checking with more detailed validation
  const hasStatusData = stats?.by_status && 
    typeof stats.by_status === 'object' && 
    Object.keys(stats.by_status).length > 0 &&
    Object.values(stats.by_status).some(value => value > 0);

  const hasTypeData = stats?.by_type && 
    typeof stats.by_type === 'object' && 
    Object.keys(stats.by_type).length > 0 &&
    Object.values(stats.by_type).some(value => value > 0);

  // Enhanced Status Chart Data with better error handling
  const statusChartData = useMemo(() => {
    if (!hasStatusData) {
      return {
        labels: ['No Data'],
        datasets: [{
          data: [1],
          backgroundColor: ['#E5E7EB'],
          borderColor: ['#9CA3AF'],
          borderWidth: 1,
        }]
      };
    }
    
    // Filter out zero values
    const filteredData = Object.entries(stats.by_status)
      .filter(([key, value]) => value > 0)
      .reduce((acc, [key, value]) => {
        acc[key] = value;
        return acc;
      }, {});

    const labels = Object.keys(filteredData);
    const values = Object.values(filteredData);
    
    // Color mapping for different statuses
    const statusColors = {
      'sent': '#10B981',
      'delivered': '#3B82F6',
      'opened': '#8B5CF6',
      'clicked': '#06B6D4',
      'failed': '#EF4444',
      'bounced': '#F59E0B',
      'queued': '#6B7280',
      'processing': '#EC4899'
    };

    const backgroundColor = labels.map(status => 
      statusColors[status.toLowerCase()] || '#6B7280'
    );

    const borderColor = backgroundColor.map(color => {
      // Darken the color for border
      const hex = color.replace('#', '');
      const r = parseInt(hex.substr(0, 2), 16);
      const g = parseInt(hex.substr(2, 2), 16);
      const b = parseInt(hex.substr(4, 2), 16);
      return `rgb(${Math.max(0, r - 30)}, ${Math.max(0, g - 30)}, ${Math.max(0, b - 30)})`;
    });
    
    return {
      labels: labels.map(status => 
        status.charAt(0).toUpperCase() + status.slice(1)
      ),
      datasets: [{
        data: values,
        backgroundColor,
        borderColor,
        borderWidth: 2,
        hoverOffset: 8,
        hoverBorderWidth: 3,
      }]
    };
  }, [stats?.by_status, hasStatusData]);

  // Enhanced Type Chart Data with better error handling
  const typeChartData = useMemo(() => {
    if (!hasTypeData) {
      return {
        labels: ['No Data'],
        datasets: [{
          data: [1],
          backgroundColor: ['#E5E7EB'],
          borderColor: ['#9CA3AF'],
          borderWidth: 1,
        }]
      };
    }
    
    // Filter out zero values
    const filteredData = Object.entries(stats.by_type)
      .filter(([key, value]) => value > 0)
      .reduce((acc, [key, value]) => {
        acc[key] = value;
        return acc;
      }, {});

    const labels = Object.keys(filteredData);
    const values = Object.values(filteredData);
    
    // Color mapping for different types
    const typeColors = {
      'welcome': '#10B981',
      'promotional': '#EC4899',
      'newsletter': '#06B6D4',
      'transactional': '#3B82F6',
      'batch': '#8B5CF6',
      'test': '#F59E0B',
      'manual': '#EF4444',
      'automated': '#84CC16',
      'reminder': '#F97316'
    };

    const backgroundColor = labels.map(type => 
      typeColors[type.toLowerCase()] || '#6B7280'
    );

    const borderColor = backgroundColor.map(color => {
      // Darken the color for border
      const hex = color.replace('#', '');
      const r = parseInt(hex.substr(0, 2), 16);
      const g = parseInt(hex.substr(2, 2), 16);
      const b = parseInt(hex.substr(4, 2), 16);
      return `rgb(${Math.max(0, r - 30)}, ${Math.max(0, g - 30)}, ${Math.max(0, b - 30)})`;
    });
    
    return {
      labels: labels.map(type => 
        type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')
      ),
      datasets: [{
        data: values,
        backgroundColor,
        borderColor,
        borderWidth: 2,
        hoverOffset: 8,
        hoverBorderWidth: 3,
      }]
    };
  }, [stats?.by_type, hasTypeData]);

  // Early return after all hooks
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
    },
  };

  // Enhanced Pie Chart Options with better interactivity
  const pieChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          padding: 20,
          usePointStyle: true,
          pointStyle: 'circle',
          font: { size: 12 },
          generateLabels: (chart) => {
            const data = chart.data;
            if (data.labels.length && data.datasets.length) {
              const dataset = data.datasets[0];
              const total = dataset.data.reduce((sum, val) => sum + val, 0);
              
              return data.labels.map((label, i) => {
                const value = dataset.data[i];
                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';
                
                return {
                  text: `${label}: ${value} (${percentage}%)`,
                  fillStyle: dataset.backgroundColor[i],
                  strokeStyle: dataset.borderColor[i],
                  lineWidth: dataset.borderWidth,
                  hidden: false,
                  index: i
                };
              });
            }
            return [];
          }
        }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: 'white',
        bodyColor: 'white',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        callbacks: {
          label: function(context) {
            const label = context.label || '';
            const value = context.parsed;
            const total = context.dataset.data.reduce((sum, val) => sum + val, 0);
            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';
            return `${label}: ${value} emails (${percentage}%)`;
          }
        }
      }
    },
    cutout: '50%', // Doughnut hole size
    radius: '90%', // Chart size
    animation: {
      animateRotate: true,
      animateScale: true,
      duration: 1000,
    },
    interaction: {
      intersect: false,
      mode: 'nearest'
    }
  };

  return (
    <div className="space-y-6">
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Email Analytics
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Detailed insights into your email campaign performance.
          </p>
        </div>
        <div className="mt-4 flex items-center space-x-3 md:mt-0 md:ml-4">
          {refreshing && (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
          )}
          <button
            onClick={fetchAnalytics}
            disabled={refreshing}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
          <div className="relative">
            <select
              value={period}
              onChange={(e) => setPeriod(Number(e.target.value))}
              className="form-input min-w-[140px] appearance-none bg-white border border-gray-300 rounded-md py-2 pl-3 pr-8 text-sm leading-5 focus:outline-none focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              disabled={refreshing}
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
            </select>
            {/* <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
              <svg className="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              </svg>
            </div> */}
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-5">
          <div className="card p-6 flex flex-col items-center justify-center min-h-[120px]">
            <div className="text-3xl font-bold text-gray-900">{stats.total_emails}</div>
            <div className="text-sm text-gray-500">Total Emails</div>
            <div className="mt-2 text-xs text-gray-400">All time</div>
          </div>
          <div className="card p-6 flex flex-col items-center justify-center min-h-[120px]">
            <div className="text-3xl font-bold text-green-600">{stats.sent_emails || 0}</div>
            <div className="text-sm text-gray-500">Successfully Sent</div>
            <div className="mt-2 text-xs text-green-500">
              {stats.total_emails > 0 
                ? Math.round((stats.sent_emails / stats.total_emails) * 100)
                : 0}% of total
            </div>
          </div>
          <div className="card p-6 flex flex-col items-center justify-center min-h-[120px]">
            <div className="text-3xl font-bold text-blue-600">{stats.received_emails || 0}</div>
            <div className="text-sm text-gray-500">Received</div>
            <div className="mt-2 text-xs text-blue-500">Delivered to inbox</div>
          </div>
          <div className="card p-6 flex flex-col items-center justify-center min-h-[120px]">
            <div className="text-3xl font-bold text-red-600">{stats.failed_emails || 0}</div>
            <div className="text-sm text-gray-500">Failed Deliveries</div>
            <div className="mt-2 text-xs text-red-500">
              {stats.total_emails > 0 
                ? Math.round((stats.failed_emails / stats.total_emails) * 100)
                : 0}% of total
            </div>
          </div>
          <div className="card p-6 flex flex-col items-center justify-center min-h-[120px]">
            <div className="text-3xl font-bold text-primary-600">{stats.success_rate || 0}%</div>
            <div className="text-sm text-gray-500">Success Rate</div>
            <div className="mt-2 text-xs text-primary-500">Delivery rate</div>
          </div>
        </div>
      )}

      {/* Daily Activity Chart */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Daily Email Activity (Last {period} days)
        </h3>
        <div className="h-80">
          <Line data={dailyChartData} options={chartOptions} />
        </div>
      </div>

      {/* Status and Type Charts - Enhanced */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">Email Status Distribution</h3>
            {hasStatusData && (
              <span className="text-sm text-gray-500">
                Total: {Object.values(stats.by_status).reduce((a, b) => a + b, 0)} emails
              </span>
            )}
          </div>
          <div className="h-80 relative">
            {hasStatusData ? (
              <Doughnut 
                data={statusChartData} 
                options={pieChartOptions}
                key={`status-${JSON.stringify(stats.by_status)}`} // Force re-render on data change
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="mx-auto h-12 w-12 text-gray-400 mb-4">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <h3 className="text-sm font-medium text-gray-900">No status data</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    No email status data available for the selected period.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="card p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">Email Type Distribution</h3>
            {hasTypeData && (
              <span className="text-sm text-gray-500">
                Total: {Object.values(stats.by_type).reduce((a, b) => a + b, 0)} emails
              </span>
            )}
          </div>
          <div className="h-80 relative">
            {hasTypeData ? (
              <Doughnut 
                data={typeChartData} 
                options={pieChartOptions}
                key={`type-${JSON.stringify(stats.by_type)}`} // Force re-render on data change
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="mx-auto h-12 w-12 text-gray-400 mb-4">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <h3 className="text-sm font-medium text-gray-900">No type data</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    No email type data available for the selected period.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Activity Summary */}
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
        {stats?.recent_activity && stats.recent_activity.length > 0 ? (
          <div className="space-y-3">
            {stats.recent_activity.slice(0, 5).map((activity, index) => (
              <div key={index} className="flex items-center justify-between py-2 border-b border-gray-100">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      activity.status === 'sent' ? 'bg-green-100 text-green-800' :
                      activity.status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {activity.status}
                    </span>
                    <span className="text-sm text-gray-600">{activity.to_email}</span>
                  </div>
                  <div className="text-sm text-gray-500 truncate max-w-md mt-1">
                    {activity.subject}
                  </div>
                </div>
                <div className="text-sm text-gray-400">
                  {new Date(activity.created_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="mx-auto h-12 w-12 text-gray-400 mb-4">
              <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-sm font-medium text-gray-900">No recent activity</h3>
            <p className="mt-1 text-sm text-gray-500">
              No email activity found for the selected period.
            </p>
            <div className="mt-6">
              <button
                type="button"
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                onClick={() => window.location.href = '/users'}
              >
                Create a User
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}