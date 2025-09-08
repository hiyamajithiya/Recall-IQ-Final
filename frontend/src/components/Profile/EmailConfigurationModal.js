import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { authAPI } from '../../utils/api';
import { XMarkIcon, CheckCircleIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function EmailConfigurationModal({ config, mode, onClose, onSuccess, currentUser }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [showEmailPassword, setShowEmailPassword] = useState(false);
  const [showClientSecret, setShowClientSecret] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm();

  const watchedProvider = watch('provider');

  const emailProviders = {
    gmail: {
      name: 'Gmail API (OAuth 2.0)',
      auth_type: 'oauth2',
      instructions: {
        title: 'Gmail OAuth Setup Instructions',
        steps: [
          'Go to Google Cloud Console (https://console.cloud.google.com/)',
          'Create a new project or select existing one',
          'Enable the Gmail API for your project',
          'Create OAuth 2.0 Client ID credentials',
          'Set authorized redirect URIs to include your domain',
          'Complete OAuth flow to get access tokens'
        ],
        note: 'Most secure option - No passwords needed!'
      }
    },
    gmail_smtp: {
      name: 'Gmail SMTP',
      auth_type: 'smtp',
      host: 'smtp.gmail.com',
      port: '587',
      use_tls: true,
      use_ssl: false,
      instructions: {
        title: 'Gmail SMTP Setup Instructions',
        steps: [
          'Enable 2-Step Verification in your Google Account',
          'Go to Google Account Settings > Security > 2-Step Verification',
          'Click on "App passwords" at the bottom',
          'Select "Mail" and your device, then click "Generate"',
          'Use the generated 16-character password in the "Email Password" field'
        ],
        note: 'Use App Password, not your regular Gmail password!'
      }
    },
    outlook: {
      name: 'Microsoft Graph API (OAuth 2.0)',
      auth_type: 'oauth2',
      instructions: {
        title: 'Microsoft Graph OAuth Setup Instructions',
        steps: [
          'Go to Azure Active Directory admin center',
          'Navigate to App registrations > New registration',
          'Set redirect URI to your application domain',
          'Add Microsoft Graph "Mail.Send" permission',
          'Generate client secret in Certificates & secrets',
          'Complete OAuth flow to get access tokens'
        ],
        note: 'Most secure option for Microsoft accounts!'
      }
    },
    outlook_smtp: {
      name: 'Outlook SMTP',
      auth_type: 'smtp',
      host: 'smtp-mail.outlook.com',
      port: '587',
      use_tls: true,
      use_ssl: false,
      instructions: {
        title: 'Outlook SMTP Setup Instructions',
        steps: [
          'Go to Outlook.com and sign in to your account',
          'Click on Settings (gear icon) > View all Outlook settings',
          'Go to Mail > Sync email',
          'Enable "POP and IMAP" if not already enabled',
          'Use your full Outlook email address as username'
        ],
        note: 'Make sure IMAP is enabled in your Outlook settings!'
      }
    },
    yahoo: {
      name: 'Yahoo Mail SMTP',
      auth_type: 'smtp',
      host: 'smtp.mail.yahoo.com',
      port: '587',
      use_tls: true,
      use_ssl: false,
      instructions: {
        title: 'Yahoo Mail Setup Instructions',
        steps: [
          'Go to Yahoo Account Security settings',
          'Turn on 2-Step Verification if not enabled',
          'Click "Generate app password"',
          'Select "Other app" and enter "RecallIQ"',
          'Use your Yahoo email and generated app password'
        ],
        note: 'Requires 2-Step Verification and app password!'
      }
    },
    icloud: {
      name: 'iCloud Mail SMTP',
      auth_type: 'smtp',
      host: 'smtp.mail.me.com',
      port: '587',
      use_tls: true,
      use_ssl: false,
      instructions: {
        title: 'iCloud Mail Setup Instructions',
        steps: [
          'Go to Apple ID account page (appleid.apple.com)',
          'Sign in and go to Security section',
          'Enable Two-Factor Authentication if not active',
          'Generate an app-specific password for mail',
          'Use your iCloud email and app password'
        ],
        note: 'Requires Two-Factor Authentication and app password!'
      }
    },
    zoho: {
      name: 'Zoho Mail SMTP',
      auth_type: 'smtp',
      host: 'smtp.zoho.com',
      port: '587',
      use_tls: true,
      use_ssl: false,
      instructions: {
        title: 'Zoho Mail Setup Instructions',
        steps: [
          'Log into your Zoho Mail account',
          'Go to Settings > Mail Accounts > IMAP/POP Access',
          'Enable IMAP/POP access if not enabled',
          'Generate app-specific password for enhanced security',
          'Use your Zoho email and password/app password'
        ],
        note: 'App-specific passwords recommended for security!'
      }
    },
    aol: {
      name: 'AOL Mail SMTP',
      auth_type: 'smtp',
      host: 'smtp.aol.com',
      port: '587',
      use_tls: true,
      use_ssl: false,
      instructions: {
        title: 'AOL Mail Setup Instructions',
        steps: [
          'Go to AOL Account Security settings',
          'Enable 2-Step Verification if not active',
          'Generate an app-specific password for mail',
          'Use your AOL email and generated app password'
        ],
        note: 'Requires app-specific password for security!'
      }
    },
    protonmail: {
      name: 'ProtonMail Bridge',
      auth_type: 'bridge',
      host: '127.0.0.1',
      port: '1025',
      use_tls: true,
      use_ssl: false,
      instructions: {
        title: 'ProtonMail Bridge Setup Instructions',
        steps: [
          'Download and install ProtonMail Bridge application',
          'Log into Bridge with your ProtonMail credentials',
          'Set up SMTP access in Bridge settings',
          'Use Bridge-provided SMTP credentials',
          'Keep Bridge running for email sending'
        ],
        note: 'Requires paid ProtonMail account and Bridge app!'
      }
    },
    smtp: {
      name: 'Custom SMTP Server',
      auth_type: 'smtp',
      host: '',
      port: '587',
      use_tls: true,
      use_ssl: false,
      instructions: {
        title: 'Custom SMTP Setup Instructions',
        steps: [
          'Obtain SMTP server details from your email provider',
          'Get SMTP host address (e.g., mail.yourprovider.com)',
          'Determine correct port (587 for TLS, 465 for SSL)',
          'Check if TLS/SSL encryption is required',
          'Use your email credentials for authentication'
        ],
        note: 'Contact your email provider for correct settings!'
      }
    }
  };

  // Helper function to check if provider uses OAuth
  const isOAuthProvider = (provider) => {
    return emailProviders[provider]?.auth_type === 'oauth2';
  };
  
  // Helper function to check if provider uses SMTP
  const isSMTPProvider = (provider) => {
    return emailProviders[provider]?.auth_type === 'smtp';
  };
  
  // Helper function to check if provider uses Bridge
  const isBridgeProvider = (provider) => {
    return emailProviders[provider]?.auth_type === 'bridge';
  };

  useEffect(() => {
    if (config && mode === 'edit') {
      setValue('name', config.name);
      setValue('provider', config.provider);
      setValue('email_host', config.email_host);
      setValue('email_port', config.email_port);
      setValue('email_use_tls', config.email_use_tls);
      setValue('email_use_ssl', config.email_use_ssl);
      setValue('email_host_user', config.email_host_user);
      setValue('from_email', config.from_email);
      setValue('from_name', config.from_name);
      setValue('is_default', config.is_default);
      setValue('is_active', config.is_active);
      setValue('user', config.user);
    } else {
      // Set defaults for new configuration
      setValue('provider', 'gmail_smtp'); // Default to SMTP instead of OAuth
      setValue('email_use_tls', true);
      setValue('email_use_ssl', false);
      setValue('is_active', true);
      setValue('is_default', false);
    }
  }, [config, mode, setValue, currentUser]);

  useEffect(() => {
    if (watchedProvider && emailProviders[watchedProvider]) {
      const provider = emailProviders[watchedProvider];
      
      // Only set SMTP settings for SMTP and Bridge providers
      if (isSMTPProvider(watchedProvider) || isBridgeProvider(watchedProvider)) {
        setValue('email_host', provider.host || '');
        setValue('email_port', provider.port || '587');
        setValue('email_use_tls', provider.use_tls || false);
        setValue('email_use_ssl', provider.use_ssl || false);
      } else {
        // Clear SMTP fields for OAuth providers
        setValue('email_host', '');
        setValue('email_port', '');
        setValue('email_use_tls', false);
        setValue('email_use_ssl', false);
        setValue('email_host_user', '');
        setValue('email_host_password', '');
      }
    }
  }, [watchedProvider, setValue]);

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    try {
      console.log('Submitting email configuration:', { mode, data, configId: config?.id });
      console.log('Current user:', currentUser);
      
      // Clean up the data - remove empty fields
      const cleanData = { ...data };
      
      // Remove empty string fields that should be null/undefined
      Object.keys(cleanData).forEach(key => {
        if (cleanData[key] === '') {
          if (['from_name'].includes(key)) {
            // These fields can be empty strings
            return;
          }
          delete cleanData[key];
        }
      });
      
      console.log('Data being sent:', JSON.stringify(cleanData, null, 2));
      
      if (mode === 'create') {
        await authAPI.createEmailConfiguration(cleanData);
        toast.success('Email configuration created successfully');
      } else {
        // For updates, don't send empty password
        const updateData = { ...cleanData };
        if (!updateData.email_host_password || updateData.email_host_password.trim() === '') {
          delete updateData.email_host_password;
        }
        
        await authAPI.updateEmailConfiguration(config.id, updateData);
        toast.success('Email configuration updated successfully');
      }
      onSuccess();
    } catch (error) {
      console.error('Email configuration error:', error);
      console.error('Error response:', error.response);
      console.error('Error data:', error.response?.data);
      
      // Extract error message from response
      let errorMsg = `Failed to ${mode} email configuration`;
      if (error.response?.data?.error) {
        errorMsg = error.response.data.error;
      } else if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail;
      } else if (error.response?.data?.name) {
        errorMsg = `Name: ${error.response.data.name[0]}`;
      } else if (error.response?.data) {
        // Handle field-specific errors
        const fieldErrors = [];
        Object.keys(error.response.data).forEach(field => {
          if (Array.isArray(error.response.data[field])) {
            fieldErrors.push(`${field}: ${error.response.data[field][0]}`);
          } else if (typeof error.response.data[field] === 'string') {
            fieldErrors.push(`${field}: ${error.response.data[field]}`);
          }
        });
        if (fieldErrors.length > 0) {
          errorMsg = fieldErrors.join(', ');
        }
      }
      
      toast.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTestConfiguration = async () => {
    setIsTesting(true);
    try {
      if (mode === 'edit' && config.id) {
        // For edit mode, check if password is provided in form
        const formData = watch();
        const hasNewPassword = formData.email_host_password && formData.email_host_password.trim() !== '';
        
        if (hasNewPassword) {
          // If new password is provided, test with form data
          if (!formData.email_host || !formData.email_host_user || !formData.from_email) {
            toast.error('Please fill in all required fields (Host, Username, From Email) before testing');
            return;
          }
          
          const testData = {
            email_host: formData.email_host,
            email_port: formData.email_port || 587,
            email_host_user: formData.email_host_user,
            email_host_password: formData.email_host_password,
            from_email: formData.from_email,
            email_use_tls: formData.email_use_tls || false,
            email_use_ssl: formData.email_use_ssl || false
          };
          
          await authAPI.testEmailSettings(testData);
        } else {
          // Test existing saved configuration
          await authAPI.testEmailConfiguration(config.id);
        }
        toast.success('Email configuration test successful!');
      } else {
        // Test with current form data for new configurations
        const formData = watch();
        
        // Validate required fields
        if (!formData.email_host || !formData.email_host_user || !formData.email_host_password || !formData.from_email) {
          toast.error('Please fill in all required fields (Host, Username, Password, From Email) before testing');
          return;
        }
        
        // Prepare test data
        const testData = {
          email_host: formData.email_host,
          email_port: formData.email_port || 587,
          email_host_user: formData.email_host_user,
          email_host_password: formData.email_host_password,
          from_email: formData.from_email,
          email_use_tls: formData.email_use_tls || false,
          email_use_ssl: formData.email_use_ssl || false
        };
        
        // Test with settings endpoint
        await authAPI.testEmailSettings(testData);
        toast.success('Email configuration test successful!');
      }
    } catch (error) {
      const errorMsg = error.response?.data?.error || error.response?.data?.detail || 'Email configuration test failed';
      toast.error(errorMsg);
    } finally {
      setIsTesting(false);
    }
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
                  {mode === 'create' ? 'Add Email Configuration' : 'Edit Email Configuration'}
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
                {/* Left Column - Configuration */}
                <div className="space-y-4">
                  <div>
                    <label className="form-label">Configuration Name *</label>
                    <input
                      {...register('name', { required: 'Configuration name is required' })}
                      type="text"
                      className="form-input"
                      placeholder="e.g., My Gmail Account"
                    />
                    {errors.name && (
                      <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                    )}
                  </div>


                  <div>
                    <label className="form-label">Email Provider</label>
                    <select
                      {...register('provider', { required: 'Provider is required' })}
                      className="form-input"
                    >
                      {Object.entries(emailProviders).map(([key, provider]) => (
                        <option key={key} value={key}>{provider.name}</option>
                      ))}
                    </select>
                  </div>

                  {/* SMTP Settings - Only show for SMTP and Bridge providers */}
                  {(isSMTPProvider(watchedProvider) || isBridgeProvider(watchedProvider)) && (
                    <>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="form-label">SMTP Host *</label>
                          <input
                            {...register('email_host', { 
                              required: (isSMTPProvider(watchedProvider) || isBridgeProvider(watchedProvider)) ? 'SMTP host is required' : false 
                            })}
                            type="text"
                            className="form-input"
                            placeholder="smtp.gmail.com"
                          />
                        </div>
                        <div>
                          <label className="form-label">SMTP Port *</label>
                          <input
                            {...register('email_port', { 
                              required: (isSMTPProvider(watchedProvider) || isBridgeProvider(watchedProvider)) ? 'Port is required' : false 
                            })}
                            type="number"
                            className="form-input"
                            placeholder="587"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="flex items-center">
                          <input
                            {...register('email_use_tls')}
                            type="checkbox"
                            className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                          />
                          <label className="ml-2 text-sm text-gray-900">Use TLS (Port 587)</label>
                        </div>
                        <div className="flex items-center">
                          <input
                            {...register('email_use_ssl')}
                            type="checkbox"
                            className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                          />
                          <label className="ml-2 text-sm text-gray-900">Use SSL (Port 465)</label>
                        </div>
                      </div>
                    </>
                  )}

                  {/* OAuth Message - Show for OAuth providers */}
                  {isOAuthProvider(watchedProvider) && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-center">
                        <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                        <div>
                          <h4 className="text-sm font-medium text-green-900">OAuth 2.0 Authentication</h4>
                          <p className="text-sm text-green-800">
                            This provider uses OAuth 2.0 for secure authentication. No SMTP host, port, or password configuration needed.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Authentication Fields - Show for SMTP and Bridge providers */}
                  {(isSMTPProvider(watchedProvider) || isBridgeProvider(watchedProvider)) && (
                    <>
                      <div>
                        <label className="form-label">Email Username *</label>
                        <input
                          {...register('email_host_user', { 
                            required: (isSMTPProvider(watchedProvider) || isBridgeProvider(watchedProvider)) ? 'Email username is required' : false 
                          })}
                          type="email"
                          className="form-input"
                          placeholder="your-email@example.com"
                        />
                        {errors.email_host_user && (
                          <p className="mt-1 text-sm text-red-600">{errors.email_host_user.message}</p>
                        )}
                      </div>

                      <div>
                        <label className="form-label">
                          {watchedProvider === 'gmail_smtp' || watchedProvider === 'yahoo' || watchedProvider === 'aol' || watchedProvider === 'icloud' 
                            ? 'App-Specific Password *' 
                            : 'Email Password *'}
                        </label>
                        <div className="relative">
                          <input
                            {...register('email_host_password', { 
                              required: (mode === 'create' && (isSMTPProvider(watchedProvider) || isBridgeProvider(watchedProvider))) ? 'Password is required' : false 
                            })}
                            type={showEmailPassword ? 'text' : 'password'}
                            className="form-input pr-12"
                            placeholder={
                              mode === 'edit' 
                                ? 'Leave blank to keep current password' 
                                : (watchedProvider === 'gmail_smtp' || watchedProvider === 'yahoo' || watchedProvider === 'aol' || watchedProvider === 'icloud')
                                  ? 'Generated App Password'
                                  : 'Password or App Password'
                            }
                            autoComplete="off"
                            data-lpignore="true"
                            data-1p-ignore="true"
                          />
                          <button
                            type="button"
                            onClick={() => setShowEmailPassword(!showEmailPassword)}
                            className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-400 hover:text-blue-500 transition-colors duration-200"
                            tabIndex={-1}
                          >
                            {showEmailPassword ? (
                              <EyeSlashIcon className="h-5 w-5" />
                            ) : (
                              <EyeIcon className="h-5 w-5" />
                            )}
                          </button>
                        </div>
                        {errors.email_host_password && (
                          <p className="mt-1 text-sm text-red-600">{errors.email_host_password.message}</p>
                        )}
                      </div>
                    </>
                  )}

                  {/* OAuth Credentials - Show for OAuth providers */}
                  {isOAuthProvider(watchedProvider) && (
                    <div className="space-y-4">
                      <div>
                        <label className="form-label">Client ID *</label>
                        <input
                          {...register('client_id', { 
                            required: isOAuthProvider(watchedProvider) ? 'Client ID is required' : false 
                          })}
                          type="text"
                          className="form-input"
                          placeholder="Your OAuth Client ID"
                        />
                        {errors.client_id && (
                          <p className="mt-1 text-sm text-red-600">{errors.client_id.message}</p>
                        )}
                      </div>

                      <div>
                        <label className="form-label">Client Secret *</label>
                        <div className="relative">
                          <input
                            {...register('client_secret', { 
                              required: isOAuthProvider(watchedProvider) ? 'Client Secret is required' : false 
                            })}
                            type={showClientSecret ? 'text' : 'password'}
                            className="form-input pr-12"
                            placeholder="Your OAuth Client Secret"
                            autoComplete="off"
                            data-lpignore="true"
                            data-1p-ignore="true"
                          />
                          <button
                            type="button"
                            onClick={() => setShowClientSecret(!showClientSecret)}
                            className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-400 hover:text-blue-500 transition-colors duration-200"
                            tabIndex={-1}
                          >
                            {showClientSecret ? (
                              <EyeSlashIcon className="h-5 w-5" />
                            ) : (
                              <EyeIcon className="h-5 w-5" />
                            )}
                          </button>
                        </div>
                        {errors.client_secret && (
                          <p className="mt-1 text-sm text-red-600">{errors.client_secret.message}</p>
                        )}
                      </div>

                      <div>
                        <label className="form-label">Access Token</label>
                        <input
                          {...register('access_token')}
                          type="text"
                          className="form-input"
                          placeholder="Will be generated during OAuth flow"
                          readOnly
                        />
                      </div>

                      <div>
                        <label className="form-label">Refresh Token</label>
                        <input
                          {...register('refresh_token')}
                          type="text"
                          className="form-input"
                          placeholder="Will be generated during OAuth flow"
                          readOnly
                        />
                      </div>

                      <div className="pt-2">
                        <button
                          type="button"
                          className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                          onClick={() => {
                            toast.info('OAuth authentication flow will be implemented in future updates');
                          }}
                        >
                          <CheckCircleIcon className="h-4 w-4 mr-2" />
                          Authenticate with {watchedProvider === 'gmail' ? 'Google' : 'Microsoft'}
                        </button>
                        <p className="mt-2 text-xs text-gray-500 text-center">
                          Click to start OAuth flow and automatically generate tokens
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Right Column - Email Details */}
                <div className="space-y-4">
                  <div>
                    <label className="form-label">From Email *</label>
                    <input
                      {...register('from_email', { required: 'From email is required' })}
                      type="email"
                      className="form-input"
                      placeholder="noreply@yourcompany.com"
                    />
                    {errors.from_email && (
                      <p className="mt-1 text-sm text-red-600">{errors.from_email.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="form-label">From Name</label>
                    <input
                      {...register('from_name')}
                      type="text"
                      className="form-input"
                      placeholder="Your Company Name"
                    />
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center">
                      <input
                        {...register('is_active')}
                        type="checkbox"
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                      <label className="ml-2 text-sm text-gray-900">Active Configuration</label>
                    </div>
                    
                    <div className="flex items-center">
                      <input
                        {...register('is_default')}
                        type="checkbox"
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                      <label className="ml-2 text-sm text-gray-900">Set as Default</label>
                    </div>
                  </div>

                  {/* Instructions */}
                  {watchedProvider && emailProviders[watchedProvider]?.instructions && (
                    <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                      <h4 className="text-sm font-medium text-blue-900 mb-2">
                        {emailProviders[watchedProvider].instructions.title}
                      </h4>
                      <ol className="list-decimal list-inside space-y-1 text-sm text-blue-800">
                        {emailProviders[watchedProvider].instructions.steps.map((step, index) => (
                          <li key={index}>{step}</li>
                        ))}
                      </ol>
                      {emailProviders[watchedProvider].instructions.note && (
                        <div className="mt-3 flex items-start">
                          <CheckCircleIcon className="h-4 w-4 text-blue-500 mt-0.5 mr-2" />
                          <p className="text-sm text-blue-800">
                            <strong>Important:</strong> {emailProviders[watchedProvider].instructions.note}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="button"
                onClick={handleTestConfiguration}
                disabled={isTesting}
                className="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
              >
                {isTesting ? 'Testing...' : 'Test Configuration'}
              </button>
              
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
              >
                {isSubmitting ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                ) : (
                  mode === 'create' ? 'Create Configuration' : 'Update Configuration'
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