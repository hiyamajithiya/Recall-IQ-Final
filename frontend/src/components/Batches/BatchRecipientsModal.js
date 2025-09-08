import React, { useState, useEffect } from 'react';
import { batchesAPI } from '../../utils/api';
import { formatDateIST, getRelativeTimeIST } from '../../utils/timezone';
import TimezoneIndicator from '../common/TimezoneIndicator';
import { 
  XMarkIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  EnvelopeIcon,
  ExclamationTriangleIcon,
  UsersIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function BatchRecipientsModal({ batch, onClose, onUpdate }) {
  const [recipients, setRecipients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [selectedRecipients, setSelectedRecipients] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('all'); // all, completed, pending

  useEffect(() => {
    if (batch) {
      fetchRecipients();
    }
  }, [batch]);

  const fetchRecipients = async () => {
    try {
      const response = await batchesAPI.getRecipients(batch.id);
      const recipientData = response.data.results || response.data || [];
      setRecipients(recipientData);
    } catch (error) {
      console.error('Failed to load recipients:', error);
      toast.error('Failed to load recipients');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkReceived = async (received = true) => {
    if (selectedRecipients.length === 0) {
      toast.error('Please select recipients to update');
      return;
    }

    setUpdating(true);
    try {
      // Extract recipient IDs - we need the actual Recipient model IDs, not BatchRecipient IDs
      const recipientIds = selectedRecipients.map(r => {
        // The recipient field contains the Recipient model ID
        return r.recipient?.id || r.recipient_id;
      }).filter(Boolean);
      
      if (recipientIds.length === 0) {
        toast.error('Unable to identify recipient IDs');
        return;
      }

      if (received) {
        await batchesAPI.markDocumentsReceived(batch.id, { recipient_ids: recipientIds });
        toast.success(`Marked ${selectedRecipients.length} recipient(s) as documents received`);
      } else {
        await batchesAPI.markDocumentsNotReceived(batch.id, { recipient_ids: recipientIds });
        toast.success(`Marked ${selectedRecipients.length} recipient(s) as documents not received`);
      }
      
      setSelectedRecipients([]);
      await fetchRecipients();
      
      // Notify parent component to refresh batch data
      if (onUpdate) {
        onUpdate();
      }
    } catch (error) {
      console.error('Failed to update recipients:', error);
      toast.error('Failed to update recipients');
    } finally {
      setUpdating(false);
    }
  };

  const toggleRecipientSelection = (recipient) => {
    setSelectedRecipients(prev => {
      const isSelected = prev.some(r => r.id === recipient.id);
      if (isSelected) {
        return prev.filter(r => r.id !== recipient.id);
      } else {
        return [...prev, recipient];
      }
    });
  };

  const toggleSelectAll = () => {
    if (selectedRecipients.length === filteredRecipients.length && filteredRecipients.length > 0) {
      setSelectedRecipients([]);
    } else {
      setSelectedRecipients([...filteredRecipients]);
    }
  };

  const filteredRecipients = recipients.filter(recipient => {
    const name = recipient.recipient_name || recipient.recipient?.name || '';
    const email = recipient.recipient_email || recipient.recipient?.email || '';
    const organization = recipient.organization || recipient.recipient?.organization_name || '';
    
    const matchesSearch = !searchTerm || 
      name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      organization.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = filter === 'all' || 
      (filter === 'completed' && (recipient.is_completed || recipient.documents_received)) ||
      (filter === 'pending' && !(recipient.is_completed || recipient.documents_received));
    
    return matchesSearch && matchesFilter;
  });

  const getStatusBadge = (recipient) => {
    if (recipient.is_completed || recipient.documents_received) {
      const completedAt = recipient.completed_at || recipient.updated_at;
      return (
        <div className="flex flex-col items-end">
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
            <CheckCircleIcon className="h-3 w-3 mr-1" />
            Completed
          </span>
          {completedAt && (
            <span className="text-xs text-gray-500 mt-1">
              {formatDateIST(completedAt, 'date')}
            </span>
          )}
        </div>
      );
    } else if ((recipient.emails_sent_count || 0) > 0) {
      const reminderNum = recipient.reminder_number || recipient.emails_sent_count || 1;
      const lastSent = recipient.last_email_sent_at;
      return (
        <div className="flex flex-col items-end">
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-yellow-100 text-yellow-800">
            <EnvelopeIcon className="h-3 w-3 mr-1" />
            Reminder #{reminderNum}
          </span>
          {lastSent && (
            <span className="text-xs text-gray-500 mt-1">
              Last: {getRelativeTimeIST(lastSent)}
            </span>
          )}
        </div>
      );
    } else {
      return (
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-800">
          <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
          Pending
        </span>
      );
    }
  };

  const completedCount = recipients.filter(r => r.is_completed || r.documents_received).length;

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-recalliq-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />

        <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full">
          {/* Header */}
          <div className="card-header">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <UsersIcon className="h-6 w-6 text-recalliq-600 mr-2" />
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    Recipients - {batch.name}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {recipients.length} total recipients • {completedCount} completed
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="action-button"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
          </div>

          <div className="px-6 py-4">
            {/* Search and Filter Controls */}
            <div className="flex flex-col sm:flex-row gap-4 mb-6">
              <div className="flex-1 relative">
                <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by name, email, or organization..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="form-input pl-10"
                />
              </div>
              <div className="flex gap-2">
                <select
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  className="form-input"
                >
                  <option value="all">All Recipients</option>
                  <option value="completed">Documents Received</option>
                  <option value="pending">Pending</option>
                </select>
              </div>
            </div>

            {/* Bulk Action Buttons */}
            {selectedRecipients.length > 0 && (
              <div className="flex items-center gap-4 mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                <span className="text-sm text-blue-700 font-medium">
                  {selectedRecipients.length} recipient(s) selected
                </span>
                <div className="flex gap-2 ml-auto">
                  <button
                    onClick={() => handleMarkReceived(true)}
                    disabled={updating}
                    className="btn-primary text-sm py-1 px-3 flex items-center"
                  >
                    <CheckCircleIcon className="h-4 w-4 mr-1" />
                    Mark Received
                  </button>
                  <button
                    onClick={() => handleMarkReceived(false)}
                    disabled={updating}
                    className="btn-secondary text-sm py-1 px-3 flex items-center"
                  >
                    <XCircleIcon className="h-4 w-4 mr-1" />
                    Mark Not Received
                  </button>
                </div>
              </div>
            )}

            {/* Recipients Table */}
            <div className="bg-white shadow overflow-hidden sm:rounded-md border border-gray-200">
              {/* Table Header */}
              <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedRecipients.length === filteredRecipients.length && filteredRecipients.length > 0}
                    onChange={toggleSelectAll}
                    className="rounded border-gray-300 text-recalliq-600 focus:ring-recalliq-500"
                  />
                  <span className="ml-2 text-sm font-medium text-gray-700">
                    Select All ({filteredRecipients.length})
                  </span>
                </label>
              </div>

              {/* Recipients List */}
              <div className="max-h-96 overflow-y-auto">
                {filteredRecipients.length === 0 ? (
                  <div className="text-center py-8">
                    <UsersIcon className="mx-auto h-12 w-12 text-gray-400" />
                    <h3 className="mt-2 text-sm font-medium text-gray-900">No recipients found</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      {searchTerm ? 'Try adjusting your search terms.' : 'No recipients match the current filter.'}
                    </p>
                  </div>
                ) : (
                  <ul className="divide-y divide-gray-200">
                    {filteredRecipients.map((recipient) => {
                      const name = recipient.recipient_name || recipient.recipient?.name || 'No Name';
                      const email = recipient.recipient_email || recipient.recipient?.email || 'No Email';
                      const organization = recipient.organization || recipient.recipient?.organization_name || '';
                      const emailCount = recipient.emails_sent_count || 0;
                      
                      return (
                        <li key={recipient.id} className="px-4 py-4 hover:bg-gray-50 transition-colors">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center flex-1">
                              <input
                                type="checkbox"
                                checked={selectedRecipients.some(r => r.id === recipient.id)}
                                onChange={() => toggleRecipientSelection(recipient)}
                                className="rounded border-gray-300 text-recalliq-600 focus:ring-recalliq-500"
                              />
                              <div className="ml-3 flex-1">
                                <div className="flex items-center">
                                  <p className="text-sm font-medium text-gray-900">
                                    {name}
                                  </p>
                                  {(recipient.is_completed || recipient.documents_received) && (
                                    <CheckCircleIcon className="h-4 w-4 text-green-500 ml-2" />
                                  )}
                                </div>
                                <p className="text-sm text-gray-600">{email}</p>
                                {organization && (
                                  <p className="text-xs text-gray-500">{organization}</p>
                                )}
                                {emailCount > 0 && (
                                  <p className="text-xs text-blue-600 mt-1">
                                    {emailCount} email(s) sent
                                  </p>
                                )}
                              </div>
                            </div>
                            <div className="ml-4">
                              {getStatusBadge(recipient)}
                            </div>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
            <div className="flex justify-between items-center">
              <div className="text-sm text-gray-600">
                <div>
                  <span className="font-medium">{completedCount}</span> of <span className="font-medium">{recipients.length}</span> completed
                  {batch.sub_cycle_enabled && (
                    <span className="ml-4 text-blue-600">
                      📧 Reminder emails enabled
                    </span>
                  )}
                </div>
                <TimezoneIndicator className="mt-1" />
              </div>
              <button
                type="button"
                onClick={onClose}
                className="btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}