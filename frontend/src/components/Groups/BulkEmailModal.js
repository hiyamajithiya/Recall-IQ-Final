import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { tenantsAPI } from '../../utils/api';
import { XMarkIcon, DocumentArrowUpIcon, DocumentArrowDownIcon, TableCellsIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function BulkEmailModal({ group, onClose, onSuccess }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [importMode, setImportMode] = useState('paste'); // 'paste', 'csv', or 'excel'
  const [selectedFile, setSelectedFile] = useState(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm();

  const emailsText = watch('emails_text', '');

  const parseEmails = (text) => {
    const lines = text.split('\n').filter(line => line.trim());
    const contacts = [];

    lines.forEach(line => {
      const parts = line.split(',').map(part => part.trim());
      if (parts.length >= 1) {
        const email = parts[0];
        const name = parts.length > 1 ? parts[1] : '';
        const organization = parts.length > 2 ? parts[2] : '';
        
        // Basic email validation
        if (email.includes('@')) {
          contacts.push({
            email,
            name,
            organization
          });
        }
      }
    });

    return contacts;
  };

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    try {
      const contacts = parseEmails(data.emails_text);
      
      if (contacts.length === 0) {
        toast.error('No valid emails found');
        setIsSubmitting(false);
        return;
      }

      // Check for duplicate emails
      const emails = contacts.map(c => c.email);
      const duplicates = emails.filter((email, index) => emails.indexOf(email) !== index);
      
      if (duplicates.length > 0) {
        const confirmMessage = `Found ${duplicates.length} duplicate email(s): ${duplicates.slice(0, 3).join(', ')}${duplicates.length > 3 ? '...' : ''}.\n\nDo you want to add them anyway?`;
        
        if (!window.confirm(confirmMessage)) {
          setIsSubmitting(false);
          return;
        }
      }

      const result = await tenantsAPI.bulkAddEmails(group.id, {
        contacts: contacts
      });

      toast.success(result.data.message || `Added ${contacts.length} contacts successfully`);
      onSuccess();
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to add contacts';
      toast.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (importMode === 'excel') {
        setSelectedFile(file);
      } else {
        const reader = new FileReader();
        reader.onload = (e) => {
          setValue('emails_text', e.target.result);
        };
        reader.readAsText(file);
      }
    }
  };

  const handleExcelUpload = async () => {
    if (!selectedFile) {
      toast.error('Please select an Excel file');
      return;
    }

    setIsSubmitting(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const result = await tenantsAPI.uploadExcel(group.id, formData);
      toast.success(result.data.message || 'Contacts uploaded successfully');
      onSuccess();
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.response?.data?.file || 'Failed to upload Excel file';
      toast.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await tenantsAPI.downloadTemplate();
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'email_template.xlsx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      toast.success('Template downloaded successfully');
    } catch (error) {
      toast.error('Failed to download template');
    }
  };

  const previewEmails = parseEmails(emailsText);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />

        <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="card-header">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  Add Emails to {group.name}
                </h3>
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
              <div className="space-y-4">
                {/* Import Mode Selection */}
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => setImportMode('paste')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      importMode === 'paste'
                        ? 'bg-recalliq-100 text-recalliq-700 border border-recalliq-200'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    Paste Text
                  </button>
                  <button
                    type="button"
                    onClick={() => setImportMode('csv')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      importMode === 'csv'
                        ? 'bg-recalliq-100 text-recalliq-700 border border-recalliq-200'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    Upload CSV
                  </button>
                  <button
                    type="button"
                    onClick={() => setImportMode('excel')}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      importMode === 'excel'
                        ? 'bg-recalliq-100 text-recalliq-700 border border-recalliq-200'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    Upload Excel
                  </button>
                </div>

                {importMode === 'paste' ? (
                  <div>
                    <label className="form-label">
                      Contact Information
                      <span className="text-sm font-normal text-gray-500 ml-2">
                        (One per line, format: email@domain.com,Name,Organization)
                      </span>
                    </label>
                    <textarea
                      {...register('emails_text', { required: 'Please enter contact information' })}
                      rows={8}
                      className="form-input"
                      placeholder={`john@example.com,John Doe,Tech Corp
jane@example.com,Jane Smith,Marketing Inc
admin@company.com,Admin User,RecallIQ`}
                    />
                    {errors.emails_text && (
                      <p className="mt-1 text-sm text-red-600">{errors.emails_text.message}</p>
                    )}
                  </div>
                ) : importMode === 'csv' ? (
                  <div>
                    <label className="form-label">Upload CSV File</label>
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                      <DocumentArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                      <input
                        type="file"
                        accept=".csv"
                        onChange={handleFileUpload}
                        className="hidden"
                        id="csv-upload"
                      />
                      <label
                        htmlFor="csv-upload"
                        className="cursor-pointer text-recalliq-600 hover:text-recalliq-700 font-medium"
                      >
                        Choose CSV file
                      </label>
                      <p className="text-sm text-gray-500 mt-1">
                        Format: email,name,organization (one per line)
                      </p>
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <label className="form-label">Upload Excel File</label>
                      <button
                        type="button"
                        onClick={handleDownloadTemplate}
                        className="flex items-center text-sm text-recalliq-600 hover:text-recalliq-700 font-medium"
                      >
                        <DocumentArrowDownIcon className="h-4 w-4 mr-1" />
                        Download Template
                      </button>
                    </div>
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                      <TableCellsIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                      <input
                        type="file"
                        accept=".xlsx,.xls"
                        onChange={handleFileUpload}
                        className="hidden"
                        id="excel-upload"
                      />
                      <label
                        htmlFor="excel-upload"
                        className="cursor-pointer text-recalliq-600 hover:text-recalliq-700 font-medium"
                      >
                        {selectedFile ? selectedFile.name : 'Choose Excel file'}
                      </label>
                      <p className="text-sm text-gray-500 mt-1">
                        Format: Column A = Email, Column B = Name, Column C = Organization
                      </p>
                      {selectedFile && (
                        <div className="mt-3">
                          <button
                            type="button"
                            onClick={handleExcelUpload}
                            disabled={isSubmitting}
                            className="btn-primary text-sm"
                          >
                            {isSubmitting ? 'Uploading...' : 'Upload Excel File'}
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Preview */}
                {previewEmails.length > 0 && (
                  <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
                    <h4 className="text-sm font-semibold text-blue-900 mb-2">
                      Preview ({previewEmails.length} contacts)
                    </h4>
                    <div className="max-h-32 overflow-y-auto space-y-1">
                      {previewEmails.slice(0, 5).map((contact, index) => (
                        <div key={index} className="text-sm text-blue-800">
                          <strong>{contact.email}</strong>
                          {contact.name && <span className="text-blue-600"> - {contact.name}</span>}
                          {contact.organization && <span className="text-blue-500"> ({contact.organization})</span>}
                        </div>
                      ))}
                      {previewEmails.length > 5 && (
                        <div className="text-sm text-blue-600">
                          ... and {previewEmails.length - 5} more
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                  <p className="text-sm text-yellow-800">
                    <strong>Note:</strong> If duplicate emails are found, you'll be asked to confirm before adding them.
                    Format: email,name,organization - Name and organization are optional.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 px-6 py-4 sm:flex sm:flex-row-reverse border-t border-gray-200">
              {importMode !== 'excel' && (
                <button
                  type="submit"
                  disabled={isSubmitting || previewEmails.length === 0}
                  className="btn-primary sm:ml-3 sm:w-auto w-full disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mx-auto"></div>
                  ) : (
                    `Add ${previewEmails.length} Contact${previewEmails.length !== 1 ? 's' : ''}`
                  )}
                </button>
              )}
              <button
                type="button"
                onClick={onClose}
                className="btn-secondary mt-3 sm:mt-0 sm:w-auto w-full"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}