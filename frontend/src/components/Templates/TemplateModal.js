import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { emailsAPI } from '../../utils/api';
import { XMarkIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function TemplateModal({ template, mode, onClose, onSuccess }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [previewMode, setPreviewMode] = useState('editor');

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm();

  const watchedFields = watch();

  useEffect(() => {
    if (template && mode === 'edit') {
      setValue('name', template.name);
      setValue('subject', template.subject);
      setValue('body', template.body);
      setValue('is_html', template.is_html);
      setValue('is_active', template.is_active);
    }
  }, [template, mode, setValue]);

  const onSubmit = async (data) => {
    console.log('Submitting template data:', data);
    setIsSubmitting(true);
    try {
      if (mode === 'create') {
        await emailsAPI.createTemplate(data);
        toast.success('Template created successfully');
      } else {
        await emailsAPI.updateTemplate(template.id, data);
        toast.success('Template updated successfully');
      }
      onSuccess();
    } catch (error) {
      console.error('Template submission error:', error);
      console.error('Error response:', error.response);
      
      if (error.response?.data) {
        const errorData = error.response.data;
        console.error('Error data:', errorData);
        
        // Handle specific validation errors
        if (errorData.name && Array.isArray(errorData.name)) {
          toast.error(`Name: ${errorData.name[0]}`);
        } else if (errorData.subject && Array.isArray(errorData.subject)) {
          toast.error(`Subject: ${errorData.subject[0]}`);
        } else if (errorData.body && Array.isArray(errorData.body)) {
          toast.error(`Body: ${errorData.body[0]}`);
        } else if (errorData.detail) {
          toast.error(errorData.detail);  
        } else if (errorData.non_field_errors) {
          toast.error(errorData.non_field_errors[0]);
        } else {
          // Show the full error response for debugging
          toast.error(`Validation Error: ${JSON.stringify(errorData)}`);
        }
      } else {
        toast.error(`Failed to ${mode} template. Error: ${error.message}`);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderPreview = () => {
    if (previewMode === 'editor') return null;

    const content = watchedFields.body || '';
    
    return (
      <div className="mt-4 p-4 border rounded-lg bg-gray-50">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Preview:</h4>
        <div className="bg-white p-4 rounded border">
          <div className="mb-2">
            <strong>Subject:</strong> {watchedFields.subject || 'No subject'}
          </div>
          <div className="border-t pt-2">
            {watchedFields.is_html ? (
              <div dangerouslySetInnerHTML={{ __html: content }} />
            ) : (
              <pre className="whitespace-pre-wrap text-sm">{content}</pre>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  {mode === 'create' ? 'Create' : 'Edit'} Email Template
                </h3>
                <button
                  type="button"
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="form-label">Template Name</label>
                    <input
                      {...register('name', { required: 'Template name is required' })}
                      type="text"
                      className="form-input"
                      placeholder="Enter template name"
                    />
                    {errors.name && (
                      <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="form-label">Subject</label>
                    <input
                      {...register('subject', { required: 'Subject is required' })}
                      type="text"
                      className="form-input"
                      placeholder="Email subject line"
                    />
                    {errors.subject && (
                      <p className="mt-1 text-sm text-red-600">{errors.subject.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="form-label">Email Body</label>
                    <div className="mb-2 flex space-x-2">
                      <button
                        type="button"
                        onClick={() => setPreviewMode('editor')}
                        className={`text-sm px-3 py-1 rounded ${
                          previewMode === 'editor' ? 'bg-primary-100 text-primary-700' : 'text-gray-600'
                        }`}
                      >
                        Editor
                      </button>
                      <button
                        type="button"
                        onClick={() => setPreviewMode('preview')}
                        className={`text-sm px-3 py-1 rounded ${
                          previewMode === 'preview' ? 'bg-primary-100 text-primary-700' : 'text-gray-600'
                        }`}
                      >
                        Preview
                      </button>
                    </div>
                    <textarea
                      {...register('body', { required: 'Email body is required' })}
                      rows={12}
                      className="form-input"
                      placeholder="Enter email content..."
                    />
                    {errors.body && (
                      <p className="mt-1 text-sm text-red-600">{errors.body.message}</p>
                    )}
                  </div>

                  <div className="flex items-center space-x-6">
                    <label className="flex items-center">
                      <input
                        {...register('is_html')}
                        type="checkbox"
                        className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">HTML Content</span>
                    </label>

                    <label className="flex items-center">
                      <input
                        {...register('is_active')}
                        type="checkbox"
                        defaultChecked={true}
                        className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">Active</span>
                    </label>
                  </div>
                </div>

                <div>
                  {renderPreview()}
                  
                  <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                    <h4 className="text-sm font-medium text-blue-900 mb-2">Template Variables</h4>
                    <p className="text-sm text-blue-800 mb-2">
                      You can use these variables in your template:
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      <div>
                        <h5 className="text-xs font-semibold text-blue-900 mb-1">Built-in Variables:</h5>
                        <ul className="text-sm text-blue-700 space-y-1">
                          <li><code className="bg-blue-100 px-1 rounded">{'{recipient_name}'}</code> - Recipient's name</li>
                          <li><code className="bg-blue-100 px-1 rounded">{'{recipient_email}'}</code> - Recipient's email</li>
                        </ul>
                      </div>
                      <div>
                        <h5 className="text-xs font-semibold text-blue-900 mb-1">Custom Variables:</h5>
                        <ul className="text-sm text-blue-700 space-y-1">
                          <li><code className="bg-blue-100 px-1 rounded">{'{company_name}'}</code> - Company name</li>
                          <li><code className="bg-blue-100 px-1 rounded">{'{first_name}'}</code> - First name</li>
                          <li><code className="bg-blue-100 px-1 rounded">{'{custom_field}'}</code> - Any custom field</li>
                        </ul>
                      </div>
                    </div>
                    <div className="mt-2 text-xs text-blue-600">
                      💡 Variables will be replaced with actual values when sending emails
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
              >
                {isSubmitting ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  mode === 'create' ? 'Create Template' : 'Update Template'
                )}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
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