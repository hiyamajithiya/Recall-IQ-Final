// Authentication utilities
export const checkAuthStatus = () => {
  const accessToken = localStorage.getItem('access_token');
  const refreshToken = localStorage.getItem('refresh_token');
  
  return {
    isAuthenticated: !!accessToken,
    hasRefreshToken: !!refreshToken,
    accessToken,
    refreshToken
  };
};

export const clearAuthTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  console.log('🔄 Authentication tokens cleared');
};

export const isTokenExpired = (token) => {
  if (!token) return true;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Date.now() / 1000;
    return payload.exp < currentTime;
  } catch (error) {
    console.error('❌ Error parsing token:', error);
    return true;
  }
};

export const handleAuthError = (error) => {
  const authStatus = checkAuthStatus();
  
  console.log('🔍 Handling auth error:', {
    status: error.response?.status,
    authStatus,
    url: error.config?.url
  });
  
  if (error.response?.status === 404 && !authStatus.isAuthenticated) {
    console.log('❌ 404 with no auth token - redirecting to login');
    clearAuthTokens();
    window.location.href = '/login';
    return true;
  }
  
  if (error.response?.status === 401) {
    console.log('❌ 401 Unauthorized - clearing tokens');
    clearAuthTokens();
    window.location.href = '/login';
    return true;
  }
  
  return false;
};