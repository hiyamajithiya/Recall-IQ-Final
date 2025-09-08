import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import {
  PlusIcon,
  MagnifyingGlassIcon,
  ArrowDownTrayIcon,
  ArrowUpTrayIcon,
  PencilIcon,
  TrashIcon,
  EllipsisVerticalIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline';
import { Menu, Transition } from '@headlessui/react';
import RecipientModal from '../components/Recipients/RecipientModal';
import DeleteConfirmationModal from '../components/DeleteConfirmationModal';
import api from '../utils/api';

export default function Recipients() {
  const { user } = useAuth();
  const [recipients, setRecipients] = useState([]);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedGroup, setSelectedGroup] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRecipient, setEditingRecipient] = useState(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [recipientToDelete, setRecipientToDelete] = useState(null);
  const [uploadingFile, setUploadingFile] = useState(false);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const itemsPerPage = 20;

  useEffect(() => {
    fetchRecipients();
    fetchGroups();
  }, [currentPage, searchTerm, selectedGroup]);

  const fetchRecipients = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: itemsPerPage.toString(),
      });

      if (searchTerm) {
        params.append('search', searchTerm);
      }
      if (selectedGroup) {
        params.append('groups', selectedGroup);
      }

      const response = await api.recipients.list(params.toString());
      setRecipients(response.data.results || response.data);
      setTotalPages(Math.ceil(response.data.count / itemsPerPage));
      setTotalCount(response.data.count || response.data.length);
    } catch (error) {
      console.error('Error fetching recipients:', error);
      toast.error('Failed to load recipients');
    } finally {
      setLoading(false);
    }
  };

  const fetchGroups = async () => {
    try {
      const response = await api.contactGroups.list();
      setGroups(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching groups:', error);
    }
  };

  const handleCreateRecipient = () => {
    setEditingRecipient(null);
    setIsModalOpen(true);
  };

  const handleEditRecipient = (recipient) => {
    setEditingRecipient(recipient);
    setIsModalOpen(true);
  };

  const handleDeleteRecipient = (recipient) => {
    setRecipientToDelete(recipient);
    setDeleteModalOpen(true);
  };

  const confirmDelete = async () => {
    try {
      await api.recipients.delete(recipientToDelete.id);
      toast.success('Recipient deleted successfully');
      fetchRecipients();
    } catch (error) {
      console.error('Error deleting recipient:', error);
      toast.error('Failed to delete recipient');
    } finally {
      setDeleteModalOpen(false);
      setRecipientToDelete(null);
    }
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setEditingRecipient(null);
  };

  const handleModalSuccess = () => {
    fetchRecipients();
    handleModalClose();
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await api.recipients.downloadTemplate();
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'recipient_template.xlsx';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success('Template downloaded successfully');
    } catch (error) {
      console.error('Error downloading template:', error);
      toast.error('Failed to download template');
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      setUploadingFile(true);
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.recipients.uploadExcel(formData);

      if (response.data.success) {
        toast.success(`Successfully uploaded ${response.data.created_count} recipients`);
        if (response.data.errors.length > 0) {
          console.warn('Upload errors:', response.data.errors);
          toast.error(`${response.data.errors.length} rows had errors`);
        }
        fetchRecipients();
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      toast.error('Failed to upload file');
    } finally {
      setUploadingFile(false);
      event.target.value = '';
    }
  };

  const handleExportExcel = async () => {
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (selectedGroup) params.append('groups', selectedGroup);

      const response = await api.recipients.exportExcel(params.toString());
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `recipients_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success('Recipients exported to Excel successfully');
    } catch (error) {
      console.error('Error exporting recipients to Excel:', error);
      toast.error('Failed to export recipients to Excel');
    }
  };

  const handleExportCSV = async () => {
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (selectedGroup) params.append('groups', selectedGroup);
      params.append('format', 'csv');

      const response = await api.recipients.exportExcel(params.toString());
      const blob = new Blob([response.data], {
        type: 'text/csv'
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `recipients_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success('Recipients exported to CSV successfully');
    } catch (error) {
      console.error('Error exporting recipients to CSV:', error);
      toast.error('Failed to export recipients to CSV');
    }
  };

  const filteredRecipients = recipients.filter(recipient =>
    recipient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    recipient.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    recipient.organization_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Recipients</h1>
          <p className="mt-2 text-sm text-gray-700">
            Manage your email recipients and contact information.
          </p>
        </div>
        {/* <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <button
            type="button"
            className="btn-primary"
            onClick={handleCreateRecipient}
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Add Recipient
          </button>
        </div> */}
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button onClick={handleCreateRecipient} className="btn-primary flex items-center">
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Recipient
          </button>
        </div>
      </div>

      {/* Filters and Actions */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center gap-4 mb-4">
          {/* Search */}
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none z-10" />
            <input
              type="text"
              placeholder="Search recipients..."
              className="form-input with-icon w-full"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {/* Group Filter */}
          <div className="flex-1">
            <select
              className="form-select w-full"
              value={selectedGroup}
              onChange={(e) => setSelectedGroup(e.target.value)}
            >
              <option value="">All Groups</option>
              {groups.map(group => (
                <option key={group.id} value={group.id}>
                  {group.name}
                </option>
              ))}
            </select>
          </div>

          {/* Action Buttons Group */}
          <div className="flex gap-2">
            {/* Template Button */}
            <button
              onClick={handleDownloadTemplate}
              className="btn-secondary w-36 flex items-center justify-center"
              title="Download Template"
            >
              <span className="text-sm font-medium">Template</span>
              <ArrowDownTrayIcon className="h-4 w-4 mr-1 ml-1.5" />
            </button>

            {/* Import Button */}
            <label className="btn-secondary w-36 flex items-center justify-center cursor-pointer">
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={handleFileUpload}
                className="hidden"
                disabled={uploadingFile}
              />
              <span className="text-sm font-medium">{uploadingFile ? 'Uploading...' : 'Import'}</span>
              <ArrowDownTrayIcon className="h-4 w-4 mr-1 ml-1.5" />
            </label>

            {/* Export Dropdown */}
            <Menu as="div" className="relative w-36">
              <Menu.Button className="btn-secondary w-full flex items-center justify-center">
                <ArrowUpTrayIcon className="h-4 w-4 mr-2" />
                <span className="text-sm font-medium">Export</span>
                <ChevronDownIcon className="h-4 w-4 ml-2" />
              </Menu.Button>

              <Transition
                enter="transition ease-out duration-100"
                enterFrom="transform opacity-0 scale-95"
                enterTo="transform opacity-100 scale-100"
                leave="transition ease-in duration-75"
                leaveFrom="transform opacity-100 scale-100"
                leaveTo="transform opacity-0 scale-95"
              >
                <Menu.Items className="absolute right-0 z-10 mt-2 w-48 origin-top-right bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none rounded-md">
                  <div className="py-1">
                    <Menu.Item>
                      {({ active }) => (
                        <button
                          onClick={handleExportExcel}
                          className={`${active ? 'bg-gray-100 text-gray-900' : 'text-gray-700'} group flex items-center px-4 py-2 text-sm w-full text-left`}
                        >
                          <ArrowUpTrayIcon className="mr-3 h-4 w-4" />
                          Excel Format (.xlsx)
                        </button>
                      )}
                    </Menu.Item>
                    <Menu.Item>
                      {({ active }) => (
                        <button
                          onClick={handleExportCSV}
                          className={`${active ? 'bg-gray-100 text-gray-900' : 'text-gray-700'} group flex items-center px-4 py-2 text-sm w-full text-left`}
                        >
                          <ArrowUpTrayIcon className="mr-3 h-4 w-4" />
                          CSV Format (.csv)
                        </button>
                      )}
                    </Menu.Item>
                  </div>
                </Menu.Items>
              </Transition>
            </Menu>
          </div>
        </div>

        {/* Stats */}
        <div className="text-sm text-gray-600">
          Showing {filteredRecipients.length} of {totalCount} recipients
        </div>
      </div>

      {/* Recipients Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-recalliq-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading recipients...</p>
          </div>
        ) : filteredRecipients.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-gray-500">No recipients found.</p>
            <button
              onClick={handleCreateRecipient}
              className="mt-4 btn-primary"
            >
              Add your first recipient
            </button>
          </div>
        ) : (
          <>
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Organization
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Groups
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="relative px-6 py-3">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredRecipients.map((recipient) => (
                  <tr key={recipient.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {recipient.name}
                      </div>
                      {recipient.title && (
                        <div className="text-sm text-gray-500">
                          {recipient.title}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {recipient.email}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {recipient.organization_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex flex-wrap gap-1">
                        {recipient.groups?.map((group) => (
                          <span
                            key={group.id}
                            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                          >
                            {group.name}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${recipient.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                        }`}>
                        {recipient.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <Menu as="div" className="relative inline-block text-left">
                        {({ open }) => (
                          <>
                            <Menu.Button className="flex items-center text-gray-400 hover:text-gray-600">
                              <EllipsisVerticalIcon className="h-5 w-5" />
                            </Menu.Button>
                            {open && (
                              <div className="fixed inset-0 z-40" aria-hidden="true" />
                            )}
                            <Transition
                              enter="transition ease-out duration-100"
                              enterFrom="transform opacity-0 scale-95"
                              enterTo="transform opacity-100 scale-100"
                              leave="transition ease-in duration-75"
                              leaveFrom="transform opacity-100 scale-100"
                              leaveTo="transform opacity-0 scale-95"
                            >
                              <Menu.Items
                                className="fixed z-50 mt-2 w-56 bg-white shadow-xl ring-1 ring-black ring-opacity-5 focus:outline-none rounded-md border border-gray-200"
                                style={{
                                  top: 'var(--menu-top, auto)',
                                  right: 'var(--menu-right, 1rem)',
                                }}
                                ref={(el) => {
                                  if (el) {
                                    const button = el.parentElement?.querySelector('[role="button"]');
                                    if (button) {
                                      const rect = button.getBoundingClientRect();
                                      el.style.setProperty('--menu-top', `${rect.bottom + 8}px`);
                                      el.style.setProperty('--menu-right', `${window.innerWidth - rect.right}px`);
                                    }
                                  }
                                }}
                              >
                                <div className="py-1">
                                  <Menu.Item>
                                    {({ active }) => (
                                      <button
                                        onClick={() => handleEditRecipient(recipient)}
                                        className={`${active ? 'bg-gray-100 text-gray-900' : 'text-gray-700'
                                          } group flex items-center px-4 py-2 text-sm w-full text-left`}
                                      >
                                        <PencilIcon className="mr-3 h-4 w-4" />
                                        Edit
                                      </button>
                                    )}
                                  </Menu.Item>
                                  <Menu.Item>
                                    {({ active }) => (
                                      <button
                                        onClick={() => handleDeleteRecipient(recipient)}
                                        className={`${active ? 'bg-gray-100 text-gray-900' : 'text-gray-700'
                                          } group flex items-center px-4 py-2 text-sm w-full text-left`}
                                      >
                                        <TrashIcon className="mr-3 h-4 w-4" />
                                        Delete
                                      </button>
                                    )}
                                  </Menu.Item>
                                </div>
                              </Menu.Items>
                            </Transition>
                          </>
                        )}
                      </Menu>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
                <div className="flex-1 flex justify-between sm:hidden">
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                    disabled={currentPage === 1}
                    className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                    disabled={currentPage === totalPages}
                    className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
                <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      Showing{' '}
                      <span className="font-medium">{(currentPage - 1) * itemsPerPage + 1}</span>
                      {' '}to{' '}
                      <span className="font-medium">
                        {Math.min(currentPage * itemsPerPage, totalCount)}
                      </span>
                      {' '}of{' '}
                      <span className="font-medium">{totalCount}</span>
                      {' '}results
                    </p>
                  </div>
                  <div>
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                      <button
                        onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                        disabled={currentPage === 1}
                        className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Previous
                      </button>

                      {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                        const pageNum = i + 1;
                        return (
                          <button
                            key={pageNum}
                            onClick={() => setCurrentPage(pageNum)}
                            className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${currentPage === pageNum
                              ? 'z-10 bg-recalliq-50 border-recalliq-500 text-recalliq-600'
                              : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                              }`}
                          >
                            {pageNum}
                          </button>
                        );
                      })}

                      <button
                        onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                        disabled={currentPage === totalPages}
                        className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Next
                      </button>
                    </nav>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Modals */}
      {isModalOpen && (
        <RecipientModal
          recipient={editingRecipient}
          groups={groups}
          onClose={handleModalClose}
          onSuccess={handleModalSuccess}
        />
      )}

      {deleteModalOpen && (
        <DeleteConfirmationModal
          isOpen={deleteModalOpen}
          onClose={() => setDeleteModalOpen(false)}
          onConfirm={confirmDelete}
          title="Delete Recipient"
          message={`Are you sure you want to delete "${recipientToDelete?.name}"? This action cannot be undone.`}
        />
      )}
    </div>
  );
}