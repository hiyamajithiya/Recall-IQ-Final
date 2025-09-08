import React, { useState, useEffect } from 'react';
import { emailsAPI } from '../utils/api';
import { useAuth } from '../context/AuthContext';
import { PlusIcon, PencilIcon, TrashIcon, EyeIcon, PaperAirplaneIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import TemplateModal from '../components/Templates/TemplateModal';
import PreviewModal from '../components/Templates/PreviewModal';
import TestEmailModal from '../components/Templates/TestEmailModal';
import toast from 'react-hot-toast';

export default function Templates() {
  const { user: currentUser } = useAuth();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showTestEmail, setShowTestEmail] = useState(false);
  const [modalMode, setModalMode] = useState('create');

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await emailsAPI.getTemplates();
      setTemplates(response.data.results || response.data);
    } catch (error) {
      toast.error('Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setSelectedTemplate(null);
    setModalMode('create');
    setShowModal(true);
  };

  const handleEdit = (template) => {
    setSelectedTemplate(template);
    setModalMode('edit');
    setShowModal(true);
  };

  const handleDelete = async (template) => {
    if (window.confirm(`Are you sure you want to delete template "${template.name}"?`)) {
      try {
        await emailsAPI.deleteTemplate(template.id);
        toast.success('Template deleted successfully');
        fetchTemplates();
      } catch (error) {
        toast.error('Failed to delete template');
      }
    }
  };

  const handlePreview = (template) => {
    setSelectedTemplate(template);
    setShowPreview(true);
  };

  const handleTestEmail = (template) => {
    setSelectedTemplate(template);
    setShowTestEmail(true);
  };

  const handleModalClose = () => {
    setShowModal(false);
    setSelectedTemplate(null);
  };

  const handleModalSuccess = () => {
    fetchTemplates();
    handleModalClose();
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
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Email Templates
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Create and manage reusable email templates for your campaigns.
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button
            onClick={handleCreate}
            className="btn-primary flex items-center"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            New Template
          </button>
        </div>
      </div>

      {/* Templates Grid */}
      {templates.length === 0 ? (
        <div className="text-center py-40">
          <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-lg font-medium text-gray-900">No templates</h3>
          <p className="mt-1 text-lg text-gray-500">Get started by creating a new email template.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {templates.map((template) => (
            <div key={template.id} className="card overflow-hidden">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900 truncate">
                    {template.name}
                  </h3>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handlePreview(template)}
                      className="text-gray-400 hover:text-gray-600"
                      title="Preview"
                    >
                      <EyeIcon className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleTestEmail(template)}
                      className="text-gray-400 hover:text-blue-600"
                      title="Send Test Email"
                    >
                      <PaperAirplaneIcon className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleEdit(template)}
                      className="text-gray-400 hover:text-primary-600"
                      title="Edit"
                    >
                      <PencilIcon className="h-5 w-5" />
                    </button>
                    {currentUser?.role !== 'support_team' && (
                      <button
                        onClick={() => handleDelete(template)}
                        className="text-gray-400 hover:text-red-600"
                        title="Delete"
                      >
                        <TrashIcon className="h-5 w-5" />
                      </button>
                    )}
                  </div>
                </div>

                <div className="mb-4">
                  <p className="text-sm font-medium text-gray-700 mb-1">Subject:</p>
                  <p className="text-sm text-gray-600 truncate">{template.subject}</p>
                </div>

                <div className="mb-4">
                  <p className="text-sm text-gray-600 line-clamp-3">
                    {(template.body_html || template.body_text || template.body || '').replace(/<[^>]*>/g, '').substring(0, 150)}...
                  </p>
                </div>

                <div className="flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center space-x-4">
                    <span className={`badge ${template.body_html ? 'badge-blue' : 'badge-gray'}`}>
                      {template.body_html ? 'HTML' : 'Text'}
                    </span>
                    <span className={`badge ${template.is_active ? 'badge-green' : 'badge-red'}`}>
                      {template.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <span>
                    {new Date(template.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modals */}
      {showModal && (
        <TemplateModal
          template={selectedTemplate}
          mode={modalMode}
          onClose={handleModalClose}
          onSuccess={handleModalSuccess}
        />
      )}

      {showPreview && (
        <PreviewModal
          template={selectedTemplate}
          onClose={() => setShowPreview(false)}
        />
      )}

      {showTestEmail && (
        <TestEmailModal
          template={selectedTemplate}
          onClose={() => setShowTestEmail(false)}
        />
      )}
    </div>
  );
}