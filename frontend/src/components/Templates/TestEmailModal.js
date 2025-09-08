import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { emailsAPI } from '../../utils/api';
import { XMarkIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function TestEmailModal({ template, onClose }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [variables, setVariables] = useState({});

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm();

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    try {
      const response = await emailsAPI.sendTestEmail(template.id, {
        test_email: data.test_email,
        template_variables: variables,
      });
      
      // Show detailed success message with sender info
      const senderInfo = response.data.sender_name ? 
        `from ${response.data.sender_name} (${response.data.sender})` : 
        `from ${response.data.sender}`;
      
      toast.success(`Test email sent successfully ${senderInfo}!`);
      onClose();
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Failed to send test email';
      toast.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleVariableChange = (key, value) => {
    setVariables(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const addVariableField = () => {
    const container = document.getElementById('variables-container');
    const div = document.createElement('div');
    div.className = 'grid grid-cols-2 gap-2';
    div.innerHTML = `
      <input
        type="text"
        placeholder="Variable name"
        class="form-input"
        onblur="handleVariableUpdate()"
      />
      <input
        type="text"
        placeholder="Variable value"
        class="form-input"
        onblur="handleVariableUpdate()"
      />
    `;
    container.appendChild(div);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Send Test Email
                </h3>
                <button
                  type="button"
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-600 mb-4">
                    Send a test email using template: <strong>{template.name}</strong>
                  </p>
                </div>

                <div>
                  <label className="form-label">Test Email Address</label>
                  <input
                    {...register('test_email', {
                      required: 'Email address is required',
                      pattern: {
                        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                        message: 'Invalid email address',
                      },
                    })}
                    type="email"
                    className="form-input"
                    placeholder="test@example.com"
                  />
                  {errors.test_email && (
                    <p className="mt-1 text-sm text-red-600">{errors.test_email.message}</p>
                  )}
                </div>

                <div>
                  <label className="form-label">Template Variables (Optional)</label>
                  <div id="variables-container" className="space-y-2">
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="text"
                        placeholder="Variable name"
                        className="form-input"
                        onChange={(e) => {
                          const value = e.target.parentElement.children[1].value;
                          if (e.target.value && value) {
                            handleVariableChange(e.target.value, value);
                          }
                        }}
                      />
                      <input
                        type="text"
                        placeholder="Variable value"
                        className="form-input"
                        onChange={(e) => {
                          const key = e.target.parentElement.children[0].value;
                          if (key && e.target.value) {
                            handleVariableChange(key, e.target.value);
                          }
                        }}
                      />
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={addVariableField}
                    className="mt-2 text-sm text-primary-600 hover:text-primary-700"
                  >
                    + Add another variable
                  </button>
                </div>

                <div className="bg-blue-50 p-3 rounded-lg">
                  <p className="text-sm text-blue-800">
                    <strong>Note:</strong> The test email will be sent with a "TEST" prefix in the subject line.
                    Available default variables: recipient_name, recipient_email
                  </p>
                  <p className="text-xs text-blue-700 mt-1">
                    Sender will be automatically detected from tenant email configuration or admin user details.<br></br>
                    <strong>THIS IS STILL IN TESTING PHASE WILL BE ADDED SOON</strong>
                  </p>

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
                  'Send Test Email'
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