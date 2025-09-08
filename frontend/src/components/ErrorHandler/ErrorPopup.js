import React from 'react';
import { XMarkIcon, ExclamationTriangleIcon, InformationCircleIcon } from '@heroicons/react/24/outline';

const ErrorPopup = ({ error, onClose, showDetails = true }) => {
  if (!error) return null;

  const getErrorInfo = (error) => {
    const errorInfo = {
      title: 'Something went wrong',
      message: 'An unexpected error occurred',
      file: 'Unknown',
      code: 'UNKNOWN_ERROR',
      details: '',
      suggestions: []
    };

    // Handle different types of errors
    if (error?.response) {
      // API/HTTP errors
      const status = error.response.status;
      const data = error.response.data;
      
      errorInfo.code = `HTTP_${status}`;
      errorInfo.file = `API Request: ${error.config?.url || 'Unknown endpoint'}`;
      
      switch (status) {
        case 400:
          errorInfo.title = 'Bad Request';
          errorInfo.message = data?.detail || data?.error || 'The request was invalid';
          errorInfo.suggestions = [
            'Check your input data',
            'Ensure all required fields are filled',
            'Contact support if the problem persists'
          ];
          break;
        case 401:
          errorInfo.title = 'Authentication Failed';
          errorInfo.message = 'Your session has expired or credentials are invalid';
          errorInfo.suggestions = [
            'Try logging in again',
            'Check your username and password',
            'Clear browser cache and try again'
          ];
          break;
        case 403:
          errorInfo.title = 'Access Denied';
          errorInfo.message = 'You don\'t have permission to perform this action';
          errorInfo.suggestions = [
            'Contact your administrator for access',
            'Check if you\'re logged in with the right account'
          ];
          break;
        case 404:
          errorInfo.title = 'Not Found';
          errorInfo.message = 'The requested resource could not be found';
          errorInfo.file = `Missing endpoint: ${error.config?.url}`;
          errorInfo.suggestions = [
            'Check if the backend server is running',
            'Verify the API URL configuration',
            'Contact technical support'
          ];
          break;
        case 500:
          errorInfo.title = 'Server Error';
          errorInfo.message = 'The server encountered an internal error';
          errorInfo.suggestions = [
            'Try again in a few minutes',
            'Contact technical support',
            'Check if the backend server is running properly'
          ];
          break;
        default:
          errorInfo.title = `HTTP Error ${status}`;
          errorInfo.message = data?.detail || data?.error || `Server responded with status ${status}`;
      }
      
      errorInfo.details = JSON.stringify(data, null, 2);
    } else if (error?.request) {
      // Network errors
      errorInfo.title = 'Network Error';
      errorInfo.message = 'Could not connect to the server';
      errorInfo.code = 'NETWORK_ERROR';
      errorInfo.file = 'Network Connection';
      errorInfo.suggestions = [
        'Check your internet connection',
        'Verify the backend server is running on port 8002',
        'Check if any firewall is blocking the connection',
        'Try refreshing the page'
      ];
      errorInfo.details = `Request URL: ${error.config?.url || 'Unknown'}\nMethod: ${error.config?.method || 'Unknown'}`;
    } else if (error?.name === 'TypeError') {
      // JavaScript/Runtime errors
      errorInfo.title = 'Application Error';
      errorInfo.message = error.message || 'A JavaScript error occurred';
      errorInfo.code = 'JS_ERROR';
      errorInfo.file = error.stack ? error.stack.split('\n')[1]?.trim() || 'Unknown file' : 'Unknown file';
      errorInfo.suggestions = [
        'Try refreshing the page',
        'Clear browser cache',
        'Contact technical support if the problem persists'
      ];
      errorInfo.details = error.stack || 'No stack trace available';
    } else {
      // Generic errors
      errorInfo.message = error?.message || error?.toString() || 'An unknown error occurred';
      errorInfo.details = JSON.stringify(error, null, 2);
      errorInfo.suggestions = [
        'Try refreshing the page',
        'Contact technical support'
      ];
    }

    return errorInfo;
  };

  const errorInfo = getErrorInfo(error);

  const copyErrorDetails = () => {
    const errorReport = `
ERROR REPORT
============
Title: ${errorInfo.title}
Code: ${errorInfo.code}
File/Source: ${errorInfo.file}
Message: ${errorInfo.message}
Time: ${new Date().toISOString()}

Details:
${errorInfo.details}

Stack Trace:
${error?.stack || 'No stack trace available'}

Config:
${JSON.stringify(error?.config, null, 2) || 'No config available'}
    `.trim();
    
    navigator.clipboard.writeText(errorReport).then(() => {
      alert('Error details copied to clipboard! You can now paste this information when contacting support.');
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-red-200 bg-red-50">
          <div className="flex items-center space-x-3">
            <ExclamationTriangleIcon className="h-8 w-8 text-red-600" />
            <div>
              <h3 className="text-lg font-semibold text-red-800">{errorInfo.title}</h3>
              <p className="text-sm text-red-600">Error Code: {errorInfo.code}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-red-400 hover:text-red-600 transition-colors"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Error Message */}
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h4 className="font-medium text-red-800 mb-2">What happened?</h4>
            <p className="text-red-700">{errorInfo.message}</p>
          </div>

          {/* File/Source Information */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-800 mb-2">Where did it happen?</h4>
            <p className="text-blue-700 font-mono text-sm break-all">{errorInfo.file}</p>
          </div>

          {/* Suggestions */}
          {errorInfo.suggestions.length > 0 && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h4 className="font-medium text-green-800 mb-2">What can you do?</h4>
              <ul className="text-green-700 space-y-1">
                {errorInfo.suggestions.map((suggestion, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <span className="text-green-500 font-bold">•</span>
                    <span>{suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Technical Details (Collapsible) */}
          {showDetails && errorInfo.details && (
            <details className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <summary className="font-medium text-gray-800 cursor-pointer hover:text-gray-600">
                <InformationCircleIcon className="h-5 w-5 inline mr-2" />
                Technical Details (for developers)
              </summary>
              <div className="mt-3 p-3 bg-gray-100 rounded border">
                <pre className="text-xs text-gray-700 overflow-x-auto whitespace-pre-wrap">
                  {errorInfo.details}
                </pre>
              </div>
            </details>
          )}
        </div>

        {/* Footer */}
        <div className="flex flex-col sm:flex-row gap-3 p-6 border-t border-gray-200 bg-gray-50">
          <button
            onClick={copyErrorDetails}
            className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors font-medium"
          >
            Copy Error Details for Support
          </button>
          <button
            onClick={() => window.location.reload()}
            className="flex-1 bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors font-medium"
          >
            Refresh Page
          </button>
          <button
            onClick={onClose}
            className="flex-1 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors font-medium"
          >
            Close
          </button>
        </div>

        {/* Help Notice */}
        <div className="px-6 pb-4 text-center">
          <p className="text-sm text-gray-500">
            <strong>Need help?</strong> Copy the error details above and send them to your technical support team.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ErrorPopup;