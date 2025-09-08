import { useState, useCallback } from 'react';

const useErrorHandler = () => {
  const [error, setError] = useState(null);
  const [isErrorVisible, setIsErrorVisible] = useState(false);

  const handleError = useCallback((error) => {
    console.error('[ERROR] Error handled by useErrorHandler:', error);
    
    // Enhanced error logging
    const errorDetails = {
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      error: {
        name: error?.name,
        message: error?.message,
        stack: error?.stack,
        code: error?.code,
        response: error?.response ? {
          status: error.response.status,
          statusText: error.response.statusText,
          data: error.response.data,
          headers: error.response.headers
        } : null,
        request: error?.request ? {
          url: error.config?.url,
          method: error.config?.method,
          headers: error.config?.headers
        } : null
      }
    };

    // Send to error logging service if available
    if (window.errorLogger) {
      window.errorLogger.logError(errorDetails);
    }

    // Store error details in localStorage for debugging
    try {
      const errorHistory = JSON.parse(localStorage.getItem('recalliq_error_history') || '[]');
      errorHistory.push(errorDetails);
      // Keep only last 10 errors
      if (errorHistory.length > 10) {
        errorHistory.shift();
      }
      localStorage.setItem('recalliq_error_history', JSON.stringify(errorHistory));
    } catch (e) {
      console.warn('Could not save error to localStorage:', e);
    }

    setError(error);
    setIsErrorVisible(true);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
    setIsErrorVisible(false);
  }, []);

  const retryLastAction = useCallback(() => {
    // This can be enhanced to retry the last failed operation
    clearError();
    window.location.reload();
  }, [clearError]);

  // Wrapper for API calls with automatic error handling
  const withErrorHandling = useCallback((asyncFunction) => {
    return async (...args) => {
      try {
        return await asyncFunction(...args);
      } catch (error) {
        handleError(error);
        throw error; // Re-throw so calling code can handle it if needed
      }
    };
  }, [handleError]);

  return {
    error,
    isErrorVisible,
    handleError,
    clearError,
    retryLastAction,
    withErrorHandling
  };
};

export default useErrorHandler;