import React, { useState, useEffect } from 'react';
import { useAuthContext } from '../context/AuthContext';
import { tenantsAPI } from '../utils/api';
import {
  PlusIcon,
  UserGroupIcon,
  PencilIcon,
  TrashIcon,
  EnvelopeIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  EllipsisVerticalIcon,
  UserPlusIcon,
  UsersIcon
} from '@heroicons/react/24/outline';
import GroupModal from '../components/Groups/GroupModal';
import BulkEmailModal from '../components/Groups/BulkEmailModal';
import GroupDetailsModalSimple from '../components/Groups/GroupDetailsModalSimple';
import toast from 'react-hot-toast';

// Helper function to check if user can perform admin actions
const canPerformAdminActions = () => {
  const userInfo = localStorage.getItem('user_info');
  if (userInfo) {
    const user = JSON.parse(userInfo);
    return user.role === 'tenant_admin' || user.role === 'staff_admin' || user.role === 'staff' || user.role === 'support_team';
  }
  return false;
};

// Helper function to check if user can delete (support_team cannot delete)
const canDeleteGroups = () => {
  const userInfo = localStorage.getItem('user_info');
  if (userInfo) {
    const user = JSON.parse(userInfo);
    return user.role === 'tenant_admin' || user.role === 'staff_admin' || user.role === 'super_admin';
  }
  return false;
};

export default function Groups() {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [selectedGroupForDetails, setSelectedGroupForDetails] = useState(null);
  const [showGroupModal, setShowGroupModal] = useState(false);
  const [showBulkEmailModal, setShowBulkEmailModal] = useState(false);
  const [showGroupDetailsModal, setShowGroupDetailsModal] = useState(false);
  const [modalMode, setModalMode] = useState('create');
  const [isAdmin, setIsAdmin] = useState(false);
  const [canDelete, setCanDelete] = useState(false);

  useEffect(() => {
    setIsAdmin(canPerformAdminActions());
    setCanDelete(canDeleteGroups());
    fetchGroups();
  }, []);

  const fetchGroups = async () => {
    try {
      const response = await tenantsAPI.getGroups();
      setGroups(response.data.results || response.data);
    } catch (error) {
      toast.error('Failed to load groups');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setSelectedGroup(null);
    setModalMode('create');
    setShowGroupModal(true);
  };

  const handleEdit = (group) => {
    setSelectedGroup(group);
    setModalMode('edit');
    setShowGroupModal(true);
    handleViewGroupDetails(group);
  };

  const handleDelete = async (group) => {
    if (window.confirm(`Are you sure you want to delete group "${group.name}"? This action cannot be undone.`)) {
      try {
        await tenantsAPI.deleteGroup(group.id);
        toast.success('Group deleted successfully');
        fetchGroups();
      } catch (error) {
        toast.error('Failed to delete group');
      }
    }
  };

  const handleBulkAddEmails = (group) => {
    setSelectedGroup(group);
    setShowBulkEmailModal(true);
  };

  const handleViewGroupDetails = (group) => {
    setSelectedGroupForDetails(group);
    setShowGroupDetailsModal(true);
  };

  const handleModalClose = () => {
    setShowGroupModal(false);
    setShowBulkEmailModal(false);
    setShowGroupDetailsModal(false);
    setSelectedGroup(null);
    setSelectedGroupForDetails(null);
  };

  const handleModalSuccess = () => {
    fetchGroups();
    handleModalClose();
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
            Contact Groups
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Organize your contacts into groups for targeted email campaigns.
          </p>
        </div>
        {/* {isAdmin && (
          
        )} */}
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button onClick={handleCreate} className="btn-primary flex items-center">
            <PlusIcon className="h-5 w-5 mr-2" />
            New Group
          </button>
        </div>
      </div>

      {groups.length === 0 ? (
        <div className="text-center py-40">
          <UserGroupIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-lg font-medium text-gray-900">No contact groups</h3>
          <p className="mt-1 text-lg text-gray-500">
            {isAdmin ? 'Get started by creating a new contact group.' : 'No contact groups have been created yet.'}
          </p>
          {/* {isAdmin && (
            <div className="mt-6">
              <button onClick={handleCreate} className="btn-primary">
                <PlusIcon className="h-5 w-5 mr-2" />
                New Group
              </button>
            </div>
          )} */}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {groups.map((group) => (
            <div key={group.id} className="card hover:shadow-lg transition-shadow duration-200 cursor-pointer">
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-recalliq-100 rounded-lg flex items-center justify-center mr-3">
                      <UserGroupIcon className="h-6 w-6 text-recalliq-600" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 truncate">
                        {group.name}
                      </h3>
                      <p className="text-sm text-gray-500">
                        Created At: {new Date(group.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleEdit(group)}
                      className="action-button"
                      title="Edit Group"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(group)}
                      className="p-2 rounded-lg hover:bg-red-50 text-gray-500 hover:text-red-600 transition-colors duration-200"
                      title="Delete Group"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                  {group.description || 'No description provided'}
                </p>

                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center text-sm text-gray-500">
                    <UsersIcon className="h-4 w-4 mr-1 text-recalliq-500" />
                    <span className="font-medium">{group.email_count}{" contacts"}</span>
                  </div>
                  <span className={`badge ${group.is_active ? 'badge-green' : 'badge-gray'}`}>
                    {group.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>

                <div className="flex space-x-2" onClick={(e) => e.stopPropagation()}>
                  {isAdmin && (
                    <>
                      <button
                        onClick={() => handleBulkAddEmails(group)}
                        className="flex-1 btn-secondary text-sm py-2 flex items-center justify-center"
                      >
                        <UserPlusIcon className="h-4 w-4 mr-1" />
                        Add Emails
                      </button>
                    </>
                  )}
                  {!isAdmin && (
                    <div className="flex-1 text-center text-sm text-gray-500 py-2">
                      View Only - Contact Administrator
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modals */}
      {showGroupModal && (
        <GroupModal
          group={selectedGroup}
          mode={modalMode}
          onClose={handleModalClose}
          onSuccess={handleModalSuccess}
        />
      )}

      {showBulkEmailModal && (
        <BulkEmailModal
          group={selectedGroup}
          onClose={handleModalClose}
          onSuccess={handleModalSuccess}
        />
      )}

      {showGroupDetailsModal && (
        <GroupDetailsModalSimple
          group={selectedGroupForDetails}
          onClose={handleModalClose}
          onUpdate={fetchGroups}
        />
      )}
    </div>
  );
}