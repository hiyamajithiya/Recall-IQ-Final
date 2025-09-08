import React from 'react';
import ErrorPopup from './ErrorPopup';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null 
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details
    console.error('🚨 Application Error Caught by ErrorBoundary:', error);
    console.error('📍 Error Info:', errorInfo);
    
    // Create enhanced error object with more details
    const enhancedError = {
      name: error.name,
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      errorBoundary: true,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    this.setState({
      error: enhancedError,
      errorInfo: errorInfo
    });

    // Send error to logging service if available
    if (window.errorLogger) {
      window.errorLogger.logError(enhancedError);
    }
  }

  handleCloseError = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null 
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <>
          {/* Fallback UI */}
          <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
            <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6 text-center">
              <div className="mb-4">
                <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
                  <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Application Error
              </h2>
              <p className="text-gray-600 mb-6">
                The application encountered an unexpected error. Click below for more details.
              </p>
              <button
                onClick={() => this.setState({ showErrorPopup: true })}
                className="w-full bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition-colors font-medium mb-3"
              >
                View Error Details
              </button>
              <button
                onClick={() => window.location.reload()}
                className="w-full bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors font-medium"
              >
                Reload Application
              </button>
            </div>
          </div>

          {/* Error Popup */}
          {this.state.showErrorPopup && (
            <ErrorPopup
              error={this.state.error}
              onClose={() => this.setState({ showErrorPopup: false })}
              showDetails={true}
            />
          )}
        </>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;