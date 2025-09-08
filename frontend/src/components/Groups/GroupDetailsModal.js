import React, { useState, useEffect } from 'react';
import { tenantsAPI } from '../../utils/api';
import { XMarkIcon, UsersIcon, EnvelopeIcon, TrashIcon, UserPlusIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function GroupDetailsModal({ group, onClose, onUpdate }) {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(null);
  const [showAddEmailForm, setShowAddEmailForm] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [newName, setNewName] = useState('');
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    if (group) {
      fetchGroupEmails();
    }
  }, [group]);

  const fetchGroupEmails = async () => {
    try {
      setLoading(true);
      console.log('Fetching emails for group:', group.id);
      console.log('Group object:', group);
      
      const response = await tenantsAPI.getGroupEmails({ group: group.id });
      console.log('API response:', response);
      
      const emailsData = response.data.results || response.data;
      console.log('Emails data:', emailsData);
      
      setEmails(Array.isArray(emailsData) ? emailsData : []);
    } catch (error) {
      console.error('Error fetching group emails:', error);
      console.error('Error response:', error.response);
      
      let errorMessage = 'Failed to load group contacts';
      
      if (error.response) {
        if (error.response.status === 401) {
          errorMessage = 'Authentication required. Please log in again.';
        } else if (error.response.status === 403) {
          errorMessage = 'Permission denied. Contact your administrator.';
        } else if (error.response.status === 404) {
          errorMessage = 'Group not found.';
        } else if (error.response.status >= 500) {
          errorMessage = 'Server error. Please try again later.';
        } else if (error.response.data?.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.response.data?.message) {
          errorMessage = error.response.data.message;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast.error(errorMessage);
      setEmails([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteEmail = async (emailId) => {
    if (!window.confirm('Are you sure you want to remove this contact from the group?')) {
      return;
    }

    try {
      setDeleting(emailId);
      await tenantsAPI.deleteGroupEmail(emailId);
      toast.success('Contact removed successfully');
      fetchGroupEmails();
      if (onUpdate) onUpdate();
    } catch (error) {
      toast.error('Failed to remove contact');
      console.error('Error deleting email:', error);
    } finally {
      setDeleting(null);
    }
  };

  const handleAddEmail = async (e) => {
    e.preventDefault();
    if (!newEmail.trim()) return;

    try {
      setAdding(true);
      await tenantsAPI.createGroupEmail({
        group: group.id,
        email: newEmail.trim(),
        name: newName.trim()
      });
      toast.success('Contact added successfully');
      setNewEmail('');
      setNewName('');
      setShowAddEmailForm(false);
      fetchGroupEmails();
      if (onUpdate) onUpdate();
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Failed to add contact';
      toast.error(errorMsg);
      console.error('Error adding email:', error);
    } finally {
      setAdding(false);
    }
  };

  const canModify = () => {
    const userInfo = localStorage.getItem('user_info');
    if (userInfo) {
      const user = JSON.parse(userInfo);
      return user.role === 'tenant_admin' || user.role === 'staff_admin' || user.role === 'super_admin';
    }
    return false;
  };

  const isAdmin = canModify();

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          {/* Header */}
          <div className="bg-white px-6 pt-6 pb-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center mr-3">
                  <UsersIcon className="h-6 w-6 text-primary-600" />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-gray-900">
                    {group?.name}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {emails.length} contact{emails.length !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {isAdmin && (
                  <button
                    onClick={() => setShowAddEmailForm(!showAddEmailForm)}
                    className="btn-secondary flex items-center"
                  >
                    <UserPlusIcon className="h-4 w-4 mr-2" />
                    Add Contact
                  </button>
                )}
                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
            </div>
            
            {group?.description && (
              <p className="mt-2 text-sm text-gray-600">
                {group.description}
              </p>
            )}
          </div>

          {/* Add Email Form */}
          {showAddEmailForm && isAdmin && (
            <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
              <form onSubmit={handleAddEmail} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Email Address *
                    </label>
                    <input
                      type="email"
                      required
                      value={newEmail}
                      onChange={(e) => setNewEmail(e.target.value)}
                      className="form-input"
                      placeholder="contact@example.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Name (Optional)
                    </label>
                    <input
                      type="text"
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                      className="form-input"
                      placeholder="Contact Name"
                    />
                  </div>
                </div>
                <div className="flex space-x-3">
                  <button
                    type="submit"
                    disabled={adding || !newEmail.trim()}
                    className="btn-primary disabled:opacity-50"
                  >
                    {adding ? 'Adding...' : 'Add Contact'}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowAddEmailForm(false);
                      setNewEmail('');
                      setNewName('');
                    }}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Content */}
          <div className="bg-white px-6 py-4 max-h-96 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              </div>
            ) : emails.length === 0 ? (
              <div className="text-center py-8">
                <EnvelopeIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h4 className="mt-2 text-sm font-medium text-gray-900">No contacts yet</h4>
                <p className="mt-1 text-sm text-gray-500">
                  {isAdmin ? 'Add contacts to this group to get started.' : 'This group doesn\'t have any contacts yet.'}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {emails.map((email) => (
                  <div
                    key={email.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div className="flex items-center flex-1 min-w-0">
                      <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center mr-3 flex-shrink-0">
                        <EnvelopeIcon className="h-4 w-4 text-primary-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {email.name || email.email}
                        </p>
                        {email.name && (
                          <p className="text-sm text-gray-500 truncate">
                            {email.email}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 ml-4">
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        email.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {email.is_active ? 'Active' : 'Inactive'}
                      </span>
                      {isAdmin && (
                        <button
                          onClick={() => handleDeleteEmail(email.id)}
                          disabled={deleting === email.id}
                          className="p-1 rounded text-gray-400 hover:text-red-600 transition-colors disabled:opacity-50"
                          title="Remove from group"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">
                Created on {new Date(group?.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </div>
              <div className="flex space-x-3">
                <button
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
    </div>
  );
}
