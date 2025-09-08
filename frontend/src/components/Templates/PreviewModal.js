import React, { useState } from 'react';
import { emailsAPI } from '../../utils/api';
import { XMarkIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function PreviewModal({ template, onClose }) {
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [variables, setVariables] = useState({});
  const [recipientName, setRecipientName] = useState('John Doe');
  const [recipientEmail, setRecipientEmail] = useState('');

  const generatePreview = async () => {
    setLoading(true);
    try {
      const response = await emailsAPI.previewTemplate(template.id, {
        template_variables: variables,
        recipient_name: recipientName,
        recipient_email: recipientEmail,
      });
      setPreview(response.data);
    } catch (error) {
      toast.error('Failed to generate preview');
    } finally {
      setLoading(false);
    }
  };

  const handleVariableChange = (key, value) => {
    setVariables(prev => ({
      ...prev,
      [key]: value
    }));
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">
                Preview Template: {template.name}
              </h3>
              <button
                type="button"
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Variables Panel */}
              <div className="space-y-4">
                <h4 className="text-md font-medium text-gray-900">Template Variables</h4>
                
                <div>
                  <label className="form-label">Recipient Name</label>
                  <input
                    type="text"
                    value={recipientName}
                    onChange={(e) => setRecipientName(e.target.value)}
                    className="form-input"
                    placeholder="Recipient name"
                  />
                </div>

                <div>
                  <label className="form-label">Recipient Email</label>
                  <input
                    type="email"
                    value={recipientEmail}
                    onChange={(e) => setRecipientEmail(e.target.value)}
                    className="form-input"
                    placeholder="recipient@example.com"
                  />
                </div>

                <div>
                  <label className="form-label">Custom Variables</label>
                  <div className="space-y-2">
                    <input
                      type="text"
                      placeholder="Variable name"
                      onBlur={(e) => {
                        if (e.target.value && e.target.nextElementSibling?.value) {
                          handleVariableChange(e.target.value, e.target.nextElementSibling.value);
                        }
                      }}
                      className="form-input"
                    />
                    <input
                      type="text"
                      placeholder="Variable value"
                      className="form-input"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      const inputs = document.querySelectorAll('input[placeholder="Variable name"]');
                      const lastInput = inputs[inputs.length - 1];
                      const container = lastInput.parentElement;
                      const newDiv = container.cloneNode(true);
                      newDiv.querySelectorAll('input').forEach(input => input.value = '');
                      container.parentElement.appendChild(newDiv);
                    }}
                    className="mt-2 text-sm text-primary-600 hover:text-primary-700"
                  >
                    + Add variable
                  </button>
                </div>

                <button
                  onClick={generatePreview}
                  disabled={loading}
                  className="w-full btn-primary"
                >
                  {loading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mx-auto"></div>
                  ) : (
                    'Generate Preview'
                  )}
                </button>
              </div>

              {/* Preview Panel */}
              <div className="lg:col-span-2">
                {preview ? (
                  <div className="border rounded-lg bg-white">
                    <div className="border-b p-4 bg-gray-50">
                      <h4 className="font-medium text-gray-900">Email Preview</h4>
                    </div>
                    <div className="p-4">
                      <div className="mb-4">
                        <div className="text-sm text-gray-600 mb-1">Subject:</div>
                        <div className="font-medium">{preview.subject}</div>
                      </div>
                      <div className="border-t pt-4">
                        {template.is_html ? (
                          <div 
                            className="prose max-w-none"
                            dangerouslySetInnerHTML={{ __html: preview.body }}
                          />
                        ) : (
                          <pre className="whitespace-pre-wrap text-sm font-sans">
                            {preview.body}
                          </pre>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
                    <div className="text-gray-500">
                      <p className="text-lg font-medium mb-2">No Preview Generated</p>
                      <p className="text-sm">
                        Set your variables and click "Generate Preview" to see how your email will look.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              onClick={onClose}
              className="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:w-auto sm:text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}