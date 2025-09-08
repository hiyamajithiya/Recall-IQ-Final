import React, { useState, useEffect } from 'react';
import {
  XMarkIcon,
  UsersIcon,
  EnvelopeIcon,
  TrashIcon,
  UserPlusIcon,
  PencilIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function GroupDetailsModalSimple({ group, onClose, onUpdate }) {
  // --- START: New state variables for group editing ---
  const [currentGroup, setCurrentGroup] = useState(group);
  const [isEditingGroupInfo, setIsEditingGroupInfo] = useState(false);
  const [groupInfoForm, setGroupInfoForm] = useState({ name: '', description: '' });
  // --- END: New state variables ---

  // Original state variables (preserved)
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', email: '', company: '' });
  const [showAddForm, setShowAddForm] = useState(false);
  const [addForm, setAddForm] = useState({ name: '', email: '', company: '' });
  const [actionLoading, setActionLoading] = useState(null);

  useEffect(() => {
    if (group) {
      setCurrentGroup(group);
      fetchGroupEmailsSimple();
    }
  }, [group]);

  // Original function (preserved)
  const fetchGroupEmailsSimple = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const userInfo = localStorage.getItem('user_info');
      if (!token || !userInfo) {
        toast.error('Authentication required. Please log in again.');
        setEmails([]);
        return;
      }
      const user = JSON.parse(userInfo);
      const baseURL = 'http://localhost:8000/api';
      let endpoint;
      if (user.role === 'tenant_admin' || user.role === 'staff_admin' || user.role === 'super_admin') {
        endpoint = `${baseURL}/tenants/admin/group-emails/?group=${group.id}`;
      } else {
        endpoint = `${baseURL}/tenants/staff/group-emails/?group=${group.id}`;
      }
      const response = await fetch(endpoint, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json', 'Accept': 'application/json' }
      });
      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }
      const data = await response.json();
      const emailsData = data.results || data;
      if (Array.isArray(emailsData)) {
        setEmails(emailsData);
      } else {
        setEmails([]);
      }
    } catch (error) {
      console.error('Error fetching emails:', error);
      toast.error('Failed to load contacts.');
      setEmails([]);
    } finally {
      setLoading(false);
    }
  };

  // Original function (preserved)
  const makeApiCall = async (endpoint, method = 'GET', data = null) => {
    const token = localStorage.getItem('access_token');
    const options = {
      method,
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json', 'Accept': 'application/json' }
    };
    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      options.body = JSON.stringify(data);
    }
    const response = await fetch(endpoint, options);
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error ${response.status}: ${errorText}`);
    }
    if (method === 'DELETE') { return { success: true }; }
    return await response.json();
  };

  // --- START: New functions to handle group info editing ---
  const handleStartEditGroupInfo = () => {
    setGroupInfoForm({ name: currentGroup.name, description: currentGroup.description || '' });
    setIsEditingGroupInfo(true);
  };

  const handleCancelEditGroupInfo = () => {
    setIsEditingGroupInfo(false);
  };

  const handleUpdateGroupInfo = async () => {
    if (!groupInfoForm.name.trim()) {
      toast.error('Group name cannot be empty.');
      return;
    }
    try {
      setActionLoading('update-group');
      const baseURL = 'http://localhost:8000/api';
      const endpoint = `${baseURL}/tenants/admin/groups/${group.id}/`;
      const result = await makeApiCall(endpoint, 'PATCH', { name: groupInfoForm.name, description: groupInfoForm.description });
      setCurrentGroup(result);
      setIsEditingGroupInfo(false);
      toast.success('Group information updated!');
      if (onUpdate) { onUpdate(); }
    } catch (error) {
      console.error('Error updating group info:', error);
      toast.error('Failed to update group. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };
  // --- END: New functions for group editing ---

  // All original contact-management functions are preserved below
  const handleAddEmail = async () => {
    if (!addForm.email.trim() || !addForm.email.includes('@')) {
      toast.error('Please enter a valid email address');
      return;
    }
    try {
      setActionLoading('add');
      const baseURL = 'http://localhost:8000/api';
      const endpoint = `${baseURL}/tenants/admin/group-emails/`;
      const newEmailData = { group: group.id, email: addForm.email.trim(), name: addForm.name.trim() || '', company: addForm.company.trim() || '', is_active: true };
      const result = await makeApiCall(endpoint, 'POST', newEmailData);
      setEmails(prev => [...prev, result]);
      setAddForm({ name: '', email: '', company: '' });
      setShowAddForm(false);
      toast.success('Email added successfully');
      if (onUpdate) { onUpdate(); }
    } catch (error) {
      console.error('Error adding email:', error);
      toast.error('Failed to add email. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleEditEmail = async (emailId) => {
    if (!editForm.email.trim() || !editForm.email.includes('@')) {
      toast.error('Please enter a valid email address');
      return;
    }
    try {
      setActionLoading(`edit-${emailId}`);
      const baseURL = 'http://localhost:8000/api';
      const endpoint = `${baseURL}/tenants/admin/group-emails/${emailId}/`;
      const updateData = { group: group.id, email: editForm.email.trim(), name: editForm.name.trim() || '', company: editForm.company.trim() || '', is_active: true };
      const result = await makeApiCall(endpoint, 'PUT', updateData);
      setEmails(prev => prev.map(email => email.id === emailId ? result : email));
      setEditingId(null);
      setEditForm({ name: '', email: '', company: '' });
      toast.success('Email updated successfully');
      if (onUpdate) { onUpdate(); }
    } catch (error) {
      console.error('Error updating email:', error);
      toast.error('Failed to update email. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteEmail = async (emailId, emailAddress) => {
    if (!window.confirm(`Are you sure you want to delete "${emailAddress}" from this group?`)) { return; }
    try {
      setActionLoading(`delete-${emailId}`);
      const baseURL = 'http://localhost:8000/api';
      const endpoint = `${baseURL}/tenants/admin/group-emails/${emailId}/`;
      await makeApiCall(endpoint, 'DELETE');
      setEmails(prev => prev.filter(email => email.id !== emailId));
      toast.success('Email deleted successfully');
      if (onUpdate) { onUpdate(); }
    } catch (error) {
      console.error('Error deleting email:', error);
      toast.error('Failed to delete email. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  const startEdit = (email) => {
    setEditingId(email.id);
    setEditForm({ name: email.name || '', email: email.email, company: email.company || '' });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditForm({ name: '', email: '', company: '' });
  };

  const cancelAdd = () => {
    setShowAddForm(false);
    setAddForm({ name: '', email: '', company: '' });
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

  if (!group) { return null; }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-900 bg-opacity-60 transition-opacity backdrop-blur-sm" onClick={onClose} />
        <div className="inline-block align-bottom bg-white rounded-2xl text-left overflow-hidden shadow-2xl transform transition-all sm:my-8 sm:align-middle sm:max-w-5xl sm:w-full">

          {/* START: MODIFIED HEADER SECTION */}
          <div className="bg-gradient-to-r from-primary-600 to-primary-700 px-8 pt-8 pb-6">
            <div className="flex items-start justify-between">
              <div className="flex items-center flex-1">
                <div className="w-12 h-12 bg-white bg-opacity-20 rounded-xl flex items-center justify-center mr-4 flex-shrink-0">
                  <UsersIcon className="h-7 w-7 text-white" />
                </div>
                {isEditingGroupInfo ? (
                  <div className="flex-1 space-y-3">
                    <input type="text" value={groupInfoForm.name} onChange={(e) => setGroupInfoForm(prev => ({ ...prev, name: e.target.value }))} className="w-full bg-white bg-opacity-25 text-white placeholder-primary-200 text-2xl font-bold rounded-lg px-3 py-1 focus:outline-none focus:ring-2 focus:ring-white" placeholder="Group Name" disabled={actionLoading === 'update-group'} />
                    <p className="text-primary-100 -mt-1">{emails.length} contact{emails.length !== 1 ? 's' : ''} • Manage group members</p>
                  </div>
                ) : (
                  <div>
                    <div className="flex items-center space-x-3">
                      <h3 className="text-2xl font-bold text-white">{currentGroup.name}</h3>
                      {isAdmin && <button onClick={handleStartEditGroupInfo} className="text-white hover:text-primary-200 p-1.5 rounded-full hover:bg-white hover:bg-opacity-20 transition-all" title="Edit group name & description"><PencilIcon className="h-4 w-4" /></button>}
                    </div>
                    <p className="text-primary-100 mt-1">{emails.length} contact{emails.length !== 1 ? 's' : ''} • Manage group members</p>
                  </div>
                )}
              </div>
              <div className="flex items-center space-x-3 ml-4">
                {isAdmin && !isEditingGroupInfo && <button onClick={() => setShowAddForm(true)} disabled={showAddForm} className="bg-white bg-opacity-20 hover:bg-opacity-30 text-white font-medium px-4 py-2 rounded-lg flex items-center space-x-2 transition-all duration-200"><UserPlusIcon className="h-5 w-5" /><span>Add Contact</span></button>}
                <button onClick={onClose} className="text-white hover:text-primary-200 transition-colors p-2 rounded-lg hover:bg-white hover:bg-opacity-10"><XMarkIcon className="h-6 w-6" /></button>
              </div>
            </div>
            <div className="mt-4 p-4 bg-white bg-opacity-10 rounded-lg">
              {isEditingGroupInfo ? (
                <div className="space-y-4">
                  <textarea value={groupInfoForm.description} onChange={(e) => setGroupInfoForm(prev => ({ ...prev, description: e.target.value }))} className="w-full bg-white bg-opacity-25 text-primary-100 placeholder-primary-200 text-sm leading-relaxed rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-white" rows="2" placeholder="Group Description (optional)" disabled={actionLoading === 'update-group'} />
                  <div className="flex items-center justify-end space-x-3">
                    <button onClick={handleCancelEditGroupInfo} className="text-white font-medium px-4 py-1.5 rounded-lg hover:bg-white hover:bg-opacity-10" disabled={actionLoading === 'update-group'}>Cancel</button>
                    <button onClick={handleUpdateGroupInfo} className="bg-white text-primary-600 font-bold px-4 py-1.5 rounded-lg hover:bg-primary-50 flex items-center space-x-2 disabled:opacity-70" disabled={actionLoading === 'update-group'}>
                      {actionLoading === 'update-group' ? <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary-600 border-t-transparent"></div> : <CheckIcon className="h-5 w-5" />}
                      <span>Save Changes</span>
                    </button>
                  </div>
                </div>
              ) : (
                <p className="text-primary-100 text-sm leading-relaxed">{currentGroup.description || 'No description provided.'}</p>
              )}
            </div>
          </div>
          {/* END: MODIFIED HEADER SECTION */}

          {/* START: FULLY PRESERVED CONTENT SECTION */}
          <div className="bg-gray-50 px-8 py-6">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-200 border-t-primary-600 mx-auto"></div>
                  <p className="text-gray-600 mt-4 font-medium">Loading contacts...</p>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {showAddForm && isAdmin && (
                  <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
                    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 border-b border-blue-100">
                      <h4 className="text-lg font-semibold text-gray-900 flex items-center"><UserPlusIcon className="h-5 w-5 text-blue-600 mr-2" /> Add New Contact</h4>
                      <p className="text-sm text-gray-600 mt-1">Fill in the contact details below</p>
                    </div>
                    <div className="p-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="md:col-span-2">
                          <label className="block text-sm font-semibold text-gray-700 mb-2">Email Address *</label>
                          <input type="email" placeholder="john.doe@company.com" value={addForm.email} onChange={(e) => setAddForm(prev => ({ ...prev, email: e.target.value }))} className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200" disabled={actionLoading === 'add'} />
                        </div>
                        <div>
                          <label className="block text-sm font-semibold text-gray-700 mb-2">Full Name</label>
                          <input type="text" placeholder="John Doe" value={addForm.name} onChange={(e) => setAddForm(prev => ({ ...prev, name: e.target.value }))} className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200" disabled={actionLoading === 'add'} />
                        </div>
                        <div>
                          <label className="block text-sm font-semibold text-gray-700 mb-2">Company</label>
                          <input type="text" placeholder="Acme Corporation" value={addForm.company} onChange={(e) => setAddForm(prev => ({ ...prev, company: e.target.value }))} className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200" disabled={actionLoading === 'add'} />
                        </div>
                      </div>
                      <div className="flex items-center justify-end space-x-3 mt-6 pt-4 border-t border-gray-100">
                        <button onClick={cancelAdd} disabled={actionLoading === 'add'} className="px-6 py-2.5 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-all duration-200">Cancel</button>
                        <button onClick={handleAddEmail} disabled={actionLoading === 'add'} className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium flex items-center space-x-2 transition-all duration-200 disabled:opacity-50">
                          {actionLoading === 'add' ? <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div> : <CheckIcon className="h-4 w-4" />}
                          <span>Add Contact</span>
                        </button>
                      </div>
                    </div>
                  </div>
                )}
                {emails.length === 0 ? (
                  <div className="text-center py-16 bg-white rounded-xl shadow-sm border border-gray-200">
                    <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4"><EnvelopeIcon className="h-10 w-10 text-gray-400" /></div>
                    <h4 className="text-xl font-semibold text-gray-900 mb-2">No contacts yet</h4>
                    <p className="text-gray-500 mb-6 max-w-md mx-auto">This group doesn't have any contacts. Start building your contact list by adding the first member.</p>
                    {isAdmin && <button onClick={() => setShowAddForm(true)} className="bg-primary-600 hover:bg-primary-700 text-white font-medium px-6 py-3 rounded-lg flex items-center space-x-2 mx-auto transition-all duration-200"><UserPlusIcon className="h-5 w-5" /><span>Add First Contact</span></button>}
                  </div>
                ) : (
                  <div className="space-y-4">
                    {emails.map((email) => (
                      <div key={email.id} className="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-all duration-200">
                        {editingId === email.id ? (
                          <div className="p-6">
                            <div className="bg-gradient-to-r from-yellow-50 to-orange-50 -m-6 mb-6 px-6 py-4 border-b border-orange-100">
                              <h5 className="font-semibold text-gray-900 flex items-center"><PencilIcon className="h-5 w-5 text-orange-600 mr-2" /> Edit Contact</h5>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div className="md:col-span-2"><label className="block text-sm font-semibold text-gray-700 mb-2">Email Address *</label><input type="email" value={editForm.email} onChange={(e) => setEditForm(prev => ({ ...prev, email: e.target.value }))} className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all duration-200" disabled={actionLoading === `edit-${email.id}`} /></div>
                              <div><label className="block text-sm font-semibold text-gray-700 mb-2">Full Name</label><input type="text" value={editForm.name} onChange={(e) => setEditForm(prev => ({ ...prev, name: e.target.value }))} placeholder="Full name" className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all duration-200" disabled={actionLoading === `edit-${email.id}`} /></div>
                              <div><label className="block text-sm font-semibold text-gray-700 mb-2">Company</label><input type="text" value={editForm.company} onChange={(e) => setEditForm(prev => ({ ...prev, company: e.target.value }))} placeholder="Company name" className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-all duration-200" disabled={actionLoading === `edit-${email.id}`} /></div>
                            </div>
                            <div className="flex items-center justify-end space-x-3 mt-6 pt-4 border-t border-gray-100">
                              <button onClick={cancelEdit} disabled={actionLoading === `edit-${email.id}`} className="px-6 py-2.5 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg font-medium transition-all duration-200">Cancel</button>
                              <button onClick={() => handleEditEmail(email.id)} disabled={actionLoading === `edit-${email.id}`} className="px-6 py-2.5 bg-orange-600 hover:bg-orange-700 text-white rounded-lg font-medium flex items-center space-x-2 transition-all duration-200 disabled:opacity-50">
                                {actionLoading === `edit-${email.id}` ? <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div> : <CheckIcon className="h-4 w-4" />}
                                <span>Save Changes</span>
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="p-6">
                            <div className="flex items-start justify-between">
                              <div className="flex items-start space-x-4 flex-1">
                                <div className="w-12 h-12 bg-gradient-to-br from-primary-100 to-primary-200 rounded-xl flex items-center justify-center flex-shrink-0"><EnvelopeIcon className="h-6 w-6 text-primary-600" /></div>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center space-x-3 mb-1">
                                    <h5 className="text-lg font-semibold text-gray-900 truncate">{email.name || 'No Name'}</h5>
                                    <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${email.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>{email.is_active ? 'Active' : 'Inactive'}</span>
                                  </div>
                                  <p className="text-primary-600 font-medium mb-1">{email.email}</p>
                                  {email.company && <p className="text-gray-500 text-sm flex items-center"><svg className="h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2h-3a1 1 0 01-1-1v-6a1 1 0 00-1-1H9a1 1 0 00-1 1v6a1 1 0 01-1 1H4a1 1 0 110-2V4zm3 8a1 1 0 011-1h4a1 1 0 011 1v4H7v-4z" clipRule="evenodd" /></svg>{email.company}</p>}
                                  <p className="text-xs text-gray-400 mt-2">Added {new Date(email.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</p>
                                </div>
                              </div>
                              {isAdmin && (
                                <div className="flex items-center space-x-2 ml-4">
                                  <button onClick={() => startEdit(email)} disabled={actionLoading !== null} className="p-2.5 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-all duration-200" title="Edit contact"><PencilIcon className="h-5 w-5" /></button>
                                  <button onClick={() => handleDeleteEmail(email.id, email.email)} disabled={actionLoading !== null} className="p-2.5 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-lg transition-all duration-200" title="Delete contact">
                                    {actionLoading === `delete-${email.id}` ? <div className="animate-spin rounded-full h-5 w-5 border-2 border-red-600 border-t-transparent"></div> : <TrashIcon className="h-5 w-5" />}
                                  </button>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
          {/* END: FULLY PRESERVED CONTENT SECTION */}

          {/* START: PRESERVED FOOTER */}
          <div className="bg-white px-8 py-6 border-t border-gray-100">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-500 flex items-center space-x-4">
                <span className="flex items-center">
                  <svg className="h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" /></svg>
                  Created {new Date(group.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
                </span>
                {emails.length > 0 && <span className="flex items-center"><UsersIcon className="h-4 w-4 mr-1" />{emails.length} total contacts</span>}
              </div>
              <button onClick={onClose} className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium px-6 py-2.5 rounded-lg transition-all duration-200">Close</button>
            </div>
          </div>
          {/* END: PRESERVED FOOTER */}

        </div>
      </div>
    </div>
  );
}