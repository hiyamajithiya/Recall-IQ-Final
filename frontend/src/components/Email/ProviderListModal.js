import React, { useState, useEffect } from 'react';
import { emailsAPI } from '../../utils/api';
import { 
  XMarkIcon, 
  InformationCircleIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  CogIcon,
  EnvelopeIcon
} from '@heroicons/react/24/outline';
import ProviderConfigModal from './ProviderConfigModal';
import toast from 'react-hot-toast';

export default function ProviderListModal({ onClose, onSelectProvider }) {
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProvider, setSelectedProvider] = useState(null);
  const [showConfig, setShowConfig] = useState(false);

  useEffect(() => {
    fetchProviders();
  }, []);

  const fetchProviders = async () => {
    try {
      const response = await emailsAPI.getProviderConfigs();
      setProviders(response.data.providers);
    } catch (error) {
      toast.error('Failed to load email providers');
    } finally {
      setLoading(false);
    }
  };

  const getProviderIcon = (authType) => {
    switch (authType) {
      case 'oauth2':
        return <CheckCircleIcon className="h-6 w-6 text-green-500" />;
      case 'app_password':
        return <ExclamationTriangleIcon className="h-6 w-6 text-yellow-500" />;
      case 'password':
        return <InformationCircleIcon className="h-6 w-6 text-blue-500" />;
      default:
        return <CogIcon className="h-6 w-6 text-gray-500" />;
    }
  };

  const getSecurityLevel = (authType) => {
    switch (authType) {
      case 'oauth2':
        return { level: 'High Security', color: 'text-green-600', bg: 'bg-green-100' };
      case 'app_password':
        return { level: 'Medium Security', color: 'text-yellow-600', bg: 'bg-yellow-100' };
      case 'password':
        return { level: 'Basic Security', color: 'text-blue-600', bg: 'bg-blue-100' };
      case 'bridge':
        return { level: 'High Security', color: 'text-green-600', bg: 'bg-green-100' };
      case 'custom':
        return { level: 'Variable', color: 'text-gray-600', bg: 'bg-gray-100' };
      default:
        return { level: 'Unknown', color: 'text-gray-600', bg: 'bg-gray-100' };
    }
  };

  const handleProviderClick = (provider) => {
    if (onSelectProvider) {
      onSelectProvider(provider);
      onClose();
    }
  };

  const handleViewConfig = (provider) => {
    setSelectedProvider(provider.key);
    setShowConfig(true);
  };

  const handleCloseConfig = () => {
    setShowConfig(false);
    setSelectedProvider(null);
  };

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
          <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
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

  return (
    <>
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
          <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose} />

          <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-5xl sm:w-full">
            {/* Header */}
            <div className="card-header">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-recalliq-100 rounded-lg flex items-center justify-center mr-3">
                    <EnvelopeIcon className="h-6 w-6 text-recalliq-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      Email Provider Configuration
                    </h3>
                    <p className="text-sm text-gray-500">
                      Choose an email provider and view setup instructions
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
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {providers.map((provider) => {
                  const security = getSecurityLevel(provider.auth_type);
                  return (
                    <div
                      key={provider.key}
                      className="border border-gray-200 rounded-lg p-4 hover:border-recalliq-300 hover:shadow-sm transition-all duration-200 cursor-pointer"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center">
                          {getProviderIcon(provider.auth_type)}
                          <div className="ml-3">
                            <h4 className="text-sm font-semibold text-gray-900">
                              {provider.name}
                            </h4>
                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${security.bg} ${security.color} mt-1`}>
                              {security.level}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <p className="text-xs text-gray-600 mb-4 line-clamp-2">
                        {provider.description}
                      </p>
                      
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleViewConfig(provider)}
                          className="flex-1 btn-secondary text-xs py-2"
                        >
                          View Setup
                        </button>
                        {onSelectProvider && (
                          <button
                            onClick={() => handleProviderClick(provider)}
                            className="flex-1 btn-primary text-xs py-2"
                          >
                            Select
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Footer */}
            <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-500">
                  {providers.length} email providers available
                </div>
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

      {/* Provider Configuration Modal */}
      {showConfig && (
        <ProviderConfigModal
          provider={selectedProvider}
          onClose={handleCloseConfig}
        />
      )}
    </>
  );
}