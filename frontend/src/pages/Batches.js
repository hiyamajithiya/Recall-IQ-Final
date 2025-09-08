import React, { useState, useEffect } from 'react';
import { batchesAPI } from '../utils/api';
import { formatDateIST } from '../utils/timezone';
import { 
  PlusIcon, 
  TrashIcon,
  EnvelopeIcon,
  PencilIcon,
  ChartBarIcon,
  ClockIcon,
  UsersIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import BatchModal from '../components/Batches/BatchModal';
import BatchRecipientsModal from '../components/Batches/BatchRecipientsModal';
import toast from 'react-hot-toast';

const getStatusBadge = (status) => {
  const statusClasses = {
    draft: 'badge-gray',
    scheduled: 'badge-recalliq',
    running: 'badge-yellow',
    completed: 'badge-green',
    paused: 'badge-yellow',
    cancelled: 'badge-red',
    failed: 'badge-red',
  };
  return statusClasses[status] || 'badge-gray';
};

const getStatusIcon = (status) => {
  switch (status) {
    case 'completed':
      return <ChartBarIcon className="h-4 w-4" />;
    case 'scheduled':
      return <ClockIcon className="h-4 w-4" />;
    default:
      return <EnvelopeIcon className="h-4 w-4" />;
  }
};

export default function Batches() {
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [showRecipientsModal, setShowRecipientsModal] = useState(false);
  const [modalMode, setModalMode] = useState('create');
  
  // Real-time status tracking
  const [previousBatchStatuses, setPreviousBatchStatuses] = useState({});
  const [isPolling, setIsPolling] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('connected');
  const [lastUpdateTime, setLastUpdateTime] = useState(null);

  useEffect(() => {
    fetchBatches();
    ensureAutomationEnabled(); // Silently ensure automation is always on
    
    // Set up enhanced real-time polling with status change detection
    const interval = setInterval(() => {
      fetchBatchesWithStatusTracking(); // Enhanced polling with notifications
    }, 10000); // Poll every 10 seconds for better real-time experience
    
    return () => clearInterval(interval);
  }, []);

  const fetchBatches = async () => {
    try {
      const response = await batchesAPI.getBatches();
      const batchData = response.data.results || response.data;
      setBatches(batchData);
      
      // Initialize status tracking on first load
      if (Object.keys(previousBatchStatuses).length === 0) {
        const statusMap = {};
        batchData.forEach(batch => {
          statusMap[batch.id] = batch.status;
        });
        setPreviousBatchStatuses(statusMap);
      }
    } catch (error) {
      toast.error('Failed to load batches');
    } finally {
      setLoading(false);
    }
  };

  // Enhanced polling with real-time status change detection and notifications
  const fetchBatchesWithStatusTracking = async () => {
    if (isPolling) return; // Prevent overlapping requests
    
    try {
      setIsPolling(true);
      setConnectionStatus('connecting');
      
      const response = await batchesAPI.getBatches();
      const newBatchData = response.data.results || response.data;
      
      // Check for status changes and show toast notifications
      newBatchData.forEach(newBatch => {
        const previousStatus = previousBatchStatuses[newBatch.id];
        if (previousStatus && previousStatus !== newBatch.status) {
          showStatusChangeNotification(newBatch, previousStatus, newBatch.status);
        }
      });
      
      // Update batches and status tracking
      setBatches(newBatchData);
      setLastUpdateTime(new Date());
      setConnectionStatus('connected');
      
      const newStatusMap = {};
      newBatchData.forEach(batch => {
        newStatusMap[batch.id] = batch.status;
      });
      setPreviousBatchStatuses(newStatusMap);
      
    } catch (error) {
      console.error('Real-time polling error:', error);
      setConnectionStatus('error');
      
      // Show connection error toast (but not too frequently)
      if (!sessionStorage.getItem('connection_error_shown')) {
        toast.error('Connection issue - retrying...', {
          duration: 3000,
          icon: '🔄',
        });
        sessionStorage.setItem('connection_error_shown', 'true');
        // Clear the flag after 30 seconds
        setTimeout(() => {
          sessionStorage.removeItem('connection_error_shown');
        }, 30000);
      }
    } finally {
      setIsPolling(false);
      // Reset connection status after a delay
      setTimeout(() => {
        if (connectionStatus !== 'error') {
          setConnectionStatus('idle');
        }
      }, 2000);
    }
  };

  // Show toast notifications for batch status changes
  const showStatusChangeNotification = (batch, oldStatus, newStatus) => {
    const statusMessages = {
      'scheduled': '📅 Batch scheduled for execution',
      'running': '🚀 Batch execution started',
      'completed': '✅ Batch completed successfully',
      'failed': '❌ Batch execution failed',
      'paused': '⏸️ Batch paused',
      'cancelled': '🚫 Batch cancelled'
    };
    
    const message = statusMessages[newStatus] || `📊 Status changed to ${newStatus}`;
    const batchInfo = `${batch.name}: ${message}`;
    
    // Different toast types based on status
    if (newStatus === 'completed') {
      toast.success(batchInfo, {
        duration: 6000,
        icon: '🎉',
      });
    } else if (newStatus === 'failed') {
      toast.error(batchInfo, {
        duration: 8000,
        icon: '💥',
      });
    } else if (newStatus === 'running') {
      toast.loading(batchInfo, {
        duration: 4000,
        icon: '⚡',
      });
    } else {
      toast(batchInfo, {
        duration: 4000,
        icon: '📊',
      });
    }
  };

  // Silently ensure automation is always enabled (no UI - compulsory)
  const ensureAutomationEnabled = async () => {
    try {
      // Silently ensure automation is working in background
      // No API calls needed - automation is compulsory and always on
      console.log('Automation is compulsory and always enabled');
    } catch (error) {
      // Silent - no user notification, automation works automatically
      console.log('Automation handling automatically');
    }
  };

  const handleDelete = async (batch) => {
    if (!window.confirm(`Are you sure you want to delete the batch "${batch.name}"? This action cannot be undone.`)) {
      return;
    }
    
    try {
      await batchesAPI.deleteBatch(batch.id);
      toast.success('Batch deleted successfully');
      fetchBatches();
    } catch (error) {
      toast.error('Failed to delete batch');
    }
  };

  const handleCreate = () => {
    setSelectedBatch(null);
    setModalMode('create');
    setShowModal(true);
  };

  const handleEdit = (batch) => {
    setSelectedBatch(batch);
    setModalMode('edit');
    setShowModal(true);
  };

  const handleModalClose = () => {
    setShowModal(false);
    setSelectedBatch(null);
  };

  const handleModalSuccess = () => {
    fetchBatches();
    handleModalClose();
  };

  const handleViewRecipients = (batch) => {
    setSelectedBatch(batch);
    setShowRecipientsModal(true);
  };

  const handleRecipientsModalClose = () => {
    setShowRecipientsModal(false);
    setSelectedBatch(null);
  };

  const handleRecipientsUpdate = () => {
    // Refresh batch data when recipients are updated
    fetchBatches();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-recalliq-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
              Email Batches
            </h1>
            {isPolling && (
              <div className="ml-3 flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-sm text-blue-600 font-medium">Live Updates</span>
              </div>
            )}
          </div>
          <p className="mt-1 text-sm text-gray-500">
            Create and manage your email campaigns and batch sending.
            {isPolling && (
              <span className="ml-2 text-blue-600">● Polling every 10 seconds</span>
            )}
          </p>
        </div>
        <div className="mt-4 flex items-center space-x-3 md:mt-0 md:ml-4">
          {/* Connection Status Indicator */}
          <div className="flex items-center text-sm">
            <div className={`w-2 h-2 rounded-full mr-2 ${
              connectionStatus === 'connected' ? 'bg-green-500' :
              connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
              connectionStatus === 'error' ? 'bg-red-500' : 'bg-gray-400'
            }`}></div>
            <span className={`text-xs ${
              connectionStatus === 'connected' ? 'text-green-600' :
              connectionStatus === 'connecting' ? 'text-yellow-600' :
              connectionStatus === 'error' ? 'text-red-600' : 'text-gray-500'
            }`}>
              {connectionStatus === 'connected' ? 'Live' :
               connectionStatus === 'connecting' ? 'Updating...' :
               connectionStatus === 'error' ? 'Offline' : 'Ready'}
            </span>
            {lastUpdateTime && (
              <span className="ml-2 text-xs text-gray-400">
                Updated {lastUpdateTime.toLocaleTimeString()}
              </span>
            )}
          </div>
          
          <button onClick={handleCreate} className="btn-primary flex items-center">
            <PlusIcon className="h-5 w-5 mr-2" />
            New Batch
          </button>
        </div>
      </div>

      {batches.length === 0 ? (
        <div className="text-center py-40">
          <EnvelopeIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-lg font-medium text-gray-900">No email batches</h3>
          <p className="mt-1 text-lg text-gray-500">Get started by creating a new email batch.</p>
          {/* <div className="mt-6">
            <button onClick={handleCreate} className="btn-primary">
              <PlusIcon className="h-5 w-5 mr-2" />
              New Batch
            </button>
          </div> */}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 xl:grid-cols-3">
          {batches.map((batch) => {
            // Calculate progress percentages for real-time display
            const totalEmails = (batch.emails_sent || 0) + (batch.emails_failed || 0);
            const successRate = totalEmails > 0 ? ((batch.emails_sent || 0) / totalEmails * 100) : 0;
            const documentsRate = batch.total_recipients > 0 ? ((batch.documents_received_count || 0) / batch.total_recipients * 100) : 0;
            const isActive = ['running', 'scheduled'].includes(batch.status);
            
            return (
              <div key={batch.id} className={`card ${isActive ? 'ring-2 ring-blue-200 ring-opacity-50' : ''}`}>
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center flex-1 min-w-0 mr-4">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center mr-3 flex-shrink-0 ${
                      isActive ? 'bg-blue-100 animate-pulse' : 'bg-recalliq-100'
                    }`}>
                      {getStatusIcon(batch.status)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 truncate" title={batch.name}>
                        {batch.name}
                        {isPolling && isActive && (
                          <span className="ml-2 inline-flex items-center">
                            <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-blue-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                          </span>
                        )}
                      </h3>
                      <p className="text-sm text-gray-500 truncate">
                        Created {formatDateIST(batch.created_at, 'date')}
                        {isActive && (
                          <span className="ml-2 text-blue-600 font-medium">● Live</span>
                        )}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 flex-shrink-0">
                    <button 
                      onClick={() => handleEdit(batch)}
                      className="action-button"
                      title="Edit Batch"
                    >
                      <PencilIcon className="h-5 w-5" />
                    </button>
                    <button 
                      onClick={() => handleDelete(batch)}
                      className="action-button text-red-500 hover:text-red-700"
                      title="Delete Batch"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
                
                <div className="flex items-center justify-between mb-4">
                  <span className={`badge ${getStatusBadge(batch.status)} ${
                    isActive ? 'animate-pulse' : ''
                  }`}>
                    {batch.status}
                    {batch.status === 'running' && (
                      <span className="ml-1">⚡</span>
                    )}
                  </span>
                  <div className="flex items-center text-sm text-gray-500">
                    <UsersIcon className="h-4 w-4 mr-1 text-recalliq-500" />
                    <span className="font-medium mr-1">{batch.total_recipients}</span>recipients
                  </div>
                </div>

                {/* Real-time Progress Bars */}
                <div className="space-y-3 mb-4">
                  {/* Email Progress */}
                  <div>
                    <div className="flex justify-between text-sm text-gray-600 mb-1">
                      <span>Email Progress</span>
                      <span>{batch.emails_sent || 0} sent, {batch.emails_failed || 0} failed</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full transition-all duration-500 ${
                          successRate > 80 ? 'bg-green-500' : 
                          successRate > 50 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${Math.min(successRate, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                  
                  {/* Documents Progress */}
                  <div>
                    <div className="flex justify-between text-sm text-gray-600 mb-1">
                      <span>Documents Received</span>
                      <span className="font-medium text-recalliq-600">
                        {batch.documents_received_count || 0}/{batch.total_recipients}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-recalliq-500 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(documentsRate, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                </div>

                <div className="space-y-2 mb-4 text-sm text-gray-600">
                  {batch.start_time && (
                    <div>Start: {formatDateIST(batch.start_time, 'datetime')}</div>
                  )}
                  {batch.sub_cycle_enabled && (
                    <div className="text-blue-600">
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100">
                        📧 Reminders: {batch.sub_cycle_interval_display} 
                        {batch.sub_cycles_completed > 0 && ` (${batch.sub_cycles_completed} cycles)`}
                      </span>
                    </div>
                  )}
                </div>

                {(batch.emails_sent > 0 || batch.emails_failed > 0) && (
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-gray-600">Progress</span>
                      <span className="text-sm text-gray-600">
                        {Math.round((batch.emails_sent / batch.total_recipients) * 100)}%
                      </span>
                    </div>
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-recalliq-500 h-2 rounded-full transition-all duration-300"
                        style={{
                          width: `${(batch.emails_sent / batch.total_recipients) * 100}%`
                        }}
                      />
                    </div>
                  </div>
                )}

                <div className="flex space-x-2">
                  <button
                    onClick={() => handleViewRecipients(batch)}
                    className="flex-1 btn-secondary text-sm py-2 flex items-center justify-center"
                  >
                    <EyeIcon className="h-4 w-4 mr-1" />
                    View Recipients
                  </button>
                </div>
              </div>
            </div>
            );
          })}
        </div>
      )}

      {/* BatchModal */}
      {showModal && (
        <BatchModal
          batch={selectedBatch}
          mode={modalMode}
          onClose={handleModalClose}
          onSuccess={handleModalSuccess}
        />
      )}

      {/* BatchRecipientsModal */}
      {showRecipientsModal && selectedBatch && (
        <BatchRecipientsModal
          batch={selectedBatch}
          onClose={handleRecipientsModalClose}
          onUpdate={handleRecipientsUpdate}
        />
      )}
    </div>
  );
}