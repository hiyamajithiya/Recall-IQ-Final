import React from 'react';
import useErrorHandler from '../../hooks/useErrorHandler';

const ErrorTestPage = () => {
  const { handleError } = useErrorHandler();

  const testNetworkError = () => {
    const networkError = new Error('Network connection failed');
    networkError.code = 'NETWORK_ERROR';
    networkError.request = {
      url: 'http://94.136.184.80:8002/api/test',
      method: 'GET'
    };
    networkError.config = {
      url: 'http://94.136.184.80:8002/api/test',
      method: 'GET'
    };
    handleError(networkError);
  };

  const test404Error = () => {
    const error404 = {
      response: {
        status: 404,
        statusText: 'Not Found',
        data: {
          detail: 'The requested endpoint does not exist'
        }
      },
      config: {
        url: 'http://94.136.184.80:8002/api/nonexistent-endpoint',
        method: 'GET'
      },
      message: 'Request failed with status code 404'
    };
    handleError(error404);
  };

  const test500Error = () => {
    const error500 = {
      response: {
        status: 500,
        statusText: 'Internal Server Error',
        data: {
          detail: 'Database connection failed',
          error: 'Internal server error'
        }
      },
      config: {
        url: 'http://94.136.184.80:8002/api/users',
        method: 'POST'
      },
      message: 'Request failed with status code 500'
    };
    handleError(error500);
  };

  const testAuthError = () => {
    const authError = {
      response: {
        status: 401,
        statusText: 'Unauthorized',
        data: {
          detail: 'Authentication credentials were not provided'
        }
      },
      config: {
        url: 'http://94.136.184.80:8002/api/profile',
        method: 'GET'
      },
      message: 'Request failed with status code 401'
    };
    handleError(authError);
  };

  const testJavaScriptError = () => {
    const jsError = new TypeError('Cannot read properties of undefined');
    jsError.stack = `TypeError: Cannot read properties of undefined
    at ErrorTestPage (ErrorTestPage.js:65:12)
    at App.js:42:15
    at React.Component.render (react-dom.js:1234:56)`;
    handleError(jsError);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">
            🧪 Error Handling Test Page
          </h1>
          <p className="text-gray-600 mb-8">
            This page is for testing the new user-friendly error system. 
            Click any button below to see how different types of errors are displayed.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button
              onClick={testNetworkError}
              className="bg-red-500 text-white px-6 py-3 rounded-lg hover:bg-red-600 transition-colors"
            >
              🌐 Test Network Error
            </button>

            <button
              onClick={test404Error}
              className="bg-orange-500 text-white px-6 py-3 rounded-lg hover:bg-orange-600 transition-colors"
            >
              🔍 Test 404 Not Found
            </button>

            <button
              onClick={test500Error}
              className="bg-purple-500 text-white px-6 py-3 rounded-lg hover:bg-purple-600 transition-colors"
            >
              🚨 Test Server Error (500)
            </button>

            <button
              onClick={testAuthError}
              className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition-colors"
            >
              🔐 Test Authentication Error
            </button>

            <button
              onClick={testJavaScriptError}
              className="bg-yellow-500 text-white px-6 py-3 rounded-lg hover:bg-yellow-600 transition-colors"
            >
              ⚡ Test JavaScript Error
            </button>

            <button
              onClick={() => {
                throw new Error('This is a component crash test');
              }}
              className="bg-gray-500 text-white px-6 py-3 rounded-lg hover:bg-gray-600 transition-colors"
            >
              💥 Test Component Crash
            </button>
          </div>

          <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h3 className="font-semibold text-blue-800 mb-2">
              📋 What to look for in the error popups:
            </h3>
            <ul className="text-blue-700 text-sm space-y-1">
              <li>• <strong>Clear error title and message</strong> - Easy to understand what went wrong</li>
              <li>• <strong>File/source information</strong> - Shows where the error occurred</li>
              <li>• <strong>Helpful suggestions</strong> - What you can do to fix it</li>
              <li>• <strong>Copy error details</strong> - Button to copy technical info for support</li>
              <li>• <strong>Technical details</strong> - Expandable section for developers</li>
            </ul>
          </div>

          <div className="mt-6 p-4 bg-green-50 rounded-lg border border-green-200">
            <h3 className="font-semibold text-green-800 mb-2">
              💡 For Non-Technical Users:
            </h3>
            <p className="text-green-700 text-sm">
              When you see an error popup, don't panic! Read the "What happened?" and "What can you do?" sections. 
              If you need help, click "Copy Error Details for Support" and send that information to your technical team.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ErrorTestPage;