import React, { useState, useEffect } from 'react';
import { emailsAPI } from '../../utils/api';
import { 
  XMarkIcon, 
  InformationCircleIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  CogIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function ProviderConfigModal({ provider, onClose }) {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (provider) {
      fetchProviderConfig();
    }
  }, [provider]);

  const fetchProviderConfig = async () => {
    try {
      const response = await emailsAPI.getProviderConfigs(provider);
      setConfig(response.data.config);
    } catch (error) {
      toast.error('Failed to load provider configuration');
    } finally {
      setLoading(false);
    }
  };

  const getAuthTypeIcon = (authType) => {
    switch (authType) {
      case 'oauth2':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'app_password':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'password':
        return <InformationCircleIcon className="h-5 w-5 text-blue-500" />;
      default:
        return <CogIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getAuthTypeDescription = (authType) => {
    switch (authType) {
      case 'oauth2':
        return 'Most secure - Uses OAuth 2.0 authentication';
      case 'app_password':
        return 'Secure - Requires app-specific password';
      case 'password':
        return 'Basic - Uses regular email password';
      case 'bridge':
        return 'Special - Requires bridge application';
      case 'custom':
        return 'Flexible - Custom SMTP configuration';
      default:
        return 'Authentication required';
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
          <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
            <div className="px-6 py-4">
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-recalliq-600"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
          <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
            <div className="px-6 py-4">
              <div className="text-center">
                <ExclamationTriangleIcon className="h-12 w-12 text-red-400 mx-auto mb-2" />
                <p className="text-gray-600">Provider configuration not found</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />

        <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          {/* Header */}
          <div className="card-header">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-10 h-10 bg-recalliq-100 rounded-lg flex items-center justify-center mr-3">
                  <CogIcon className="h-6 w-6 text-recalliq-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {config.name} Configuration
                  </h3>
                  <p className="text-sm text-gray-500">
                    Setup instructions and requirements
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

          {/* Content */}
          <div className="px-6 py-4 max-h-96 overflow-y-auto">
            <div className="space-y-6">
              {/* Description */}
              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-2">Description</h4>
                <p className="text-sm text-gray-600">{config.description}</p>
              </div>

              {/* Authentication Type */}
              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-2">Authentication</h4>
                <div className="flex items-center space-x-2">
                  {getAuthTypeIcon(config.auth_type)}
                  <span className="text-sm text-gray-600">
                    {getAuthTypeDescription(config.auth_type)}
                  </span>
                </div>
              </div>

              {/* SMTP Settings (if available) */}
              {config.smtp_settings && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 mb-2">SMTP Settings</h4>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-gray-700">Host:</span>
                        <span className="ml-2 text-gray-600">{config.smtp_settings.host}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Port:</span>
                        <span className="ml-2 text-gray-600">{config.smtp_settings.port}</span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">TLS:</span>
                        <span className="ml-2 text-gray-600">
                          {config.smtp_settings.tls ? 'Enabled' : 'Disabled'}
                        </span>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">SSL:</span>
                        <span className="ml-2 text-gray-600">
                          {config.smtp_settings.ssl ? 'Enabled' : 'Disabled'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Required Fields */}
              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-2">Required Information</h4>
                <div className="flex flex-wrap gap-2">
                  {config.required_fields.map((field) => (
                    <span
                      key={field}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"
                    >
                      {field.replace('_', ' ')}
                    </span>
                  ))}
                </div>
                {config.optional_fields && config.optional_fields.length > 0 && (
                  <div className="mt-2">
                    <span className="text-xs text-gray-500 mb-1 block">Optional:</span>
                    <div className="flex flex-wrap gap-2">
                      {config.optional_fields.map((field) => (
                        <span
                          key={field}
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                        >
                          {field.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Setup Instructions */}
              <div>
                <h4 className="text-sm font-semibold text-gray-900 mb-3">Setup Instructions</h4>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <ol className="space-y-2">
                    {config.setup_instructions.map((instruction, index) => (
                      <li key={index} className="text-sm text-blue-900 flex">
                        <span className="font-medium mr-2">{index + 1}.</span>
                        <span>{instruction.replace(/^\d+\.\s*/, '')}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              </div>

              {/* Important Notes */}
              {config.notes && config.notes.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 mb-3">Important Notes</h4>
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <ul className="space-y-1">
                      {config.notes.map((note, index) => (
                        <li key={index} className="text-sm text-yellow-900 flex items-start">
                          <span className="mr-2">•</span>
                          <span>{note.replace(/^•\s*/, '')}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
            <div className="flex justify-end">
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