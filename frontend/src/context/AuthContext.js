import React, { createContext, useContext, useReducer, useEffect, useState } from 'react';
import { authAPI } from '../utils/api';
import useErrorHandler from '../hooks/useErrorHandler';
import ErrorPopup from '../components/ErrorHandler/ErrorPopup';

const AuthContext = createContext();

const initialState = {
  user: null,
  isAuthenticated: false,
  loading: true,
  error: null,
};

const authReducer = (state, action) => {
  switch (action.type) {
    case 'LOGIN_START':
      return { ...state, loading: true, error: null };
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        isAuthenticated: true,
        loading: false,
        error: null,
      };
    case 'LOGIN_FAILURE':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        loading: false,
        error: action.payload,
      };
    case 'LOGOUT':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        loading: false,
        error: null,
      };
    case 'LOAD_USER_START':
      return { ...state, loading: true };
    case 'LOAD_USER_SUCCESS':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        loading: false,
      };
    case 'LOAD_USER_FAILURE':
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        loading: false,
      };
    case 'UPDATE_USER':
      return {
        ...state,
        user: { ...state.user, ...action.payload },
      };
    default:
      return state;
  }
};

export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);
  const { error, isErrorVisible, handleError, clearError, withErrorHandling } = useErrorHandler();

  useEffect(() => {
    loadUser();
  }, []);

  const loadUser = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      dispatch({ type: 'LOAD_USER_FAILURE' });
      return;
    }

    try {
      dispatch({ type: 'LOAD_USER_START' });
      const response = await authAPI.getProfile();
      localStorage.setItem('user_info', JSON.stringify(response.data)); // Store user info for role-based routing
      dispatch({ type: 'LOAD_USER_SUCCESS', payload: response.data });
    } catch (error) {
      dispatch({ type: 'LOAD_USER_FAILURE' });
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_info'); // Clear user info on failure
    }
  };

  const login = async (credentials) => {
    try {
      dispatch({ type: 'LOGIN_START' });
      const response = await authAPI.login(credentials);
      const { access, refresh, user } = response.data;

      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      localStorage.setItem('user_info', JSON.stringify(user)); // Store user info for role-based routing

      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: { user },
      });

      return { success: true };
    } catch (error) {
      handleError(error); // Show user-friendly error popup
      const errorMsg = error.response?.data?.detail || 'Login failed';
      dispatch({ type: 'LOGIN_FAILURE', payload: errorMsg });
      return { success: false, error: errorMsg };
    }
  };

  const register = async (userData) => {
    try {
      dispatch({ type: 'LOGIN_START' });
      await authAPI.tenantAdminRegister(userData);
      
      const loginResult = await login({
        username: userData.username,
        password: userData.password,
      });
      
      return loginResult;
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.response?.data?.error || 'Registration failed';
      dispatch({ type: 'LOGIN_FAILURE', payload: errorMsg });
      return { success: false, error: errorMsg };
    }
  };

  const googleOAuthSignup = async (googleToken, tenantData) => {
    try {
      dispatch({ type: 'LOGIN_START' });
      const response = await authAPI.googleOAuthSignup({
        googleToken,
        tenantData
      });
      
      const { access, refresh, user } = response.data;

      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      localStorage.setItem('user_info', JSON.stringify(user));

      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: { user },
      });

      return { success: true };
    } catch (error) {
      const errorMsg = error.response?.data?.error || 'Google OAuth signup failed';
      dispatch({ type: 'LOGIN_FAILURE', payload: errorMsg });
      return { success: false, error: errorMsg };
    }
  };

  const loginWithTokens = async (access, refresh, user) => {
    try {
      localStorage.setItem('access_token', access);
      localStorage.setItem('refresh_token', refresh);
      localStorage.setItem('user_info', JSON.stringify(user));

      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: { user },
      });

      return { success: true };
    } catch (error) {
      dispatch({ type: 'LOGIN_FAILURE', payload: 'Failed to login with tokens' });
      return { success: false, error: 'Failed to login with tokens' };
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_info'); // Clear user info on logout
    dispatch({ type: 'LOGOUT' });
  };

  const updateUser = (userData) => {
    dispatch({ type: 'UPDATE_USER', payload: userData });
  };

  const value = {
    ...state,
    login,
    register,
    googleOAuthSignup,
    loginWithTokens,
    logout,
    loadUser,
    updateUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
      {/* Global Error Popup */}
      {isErrorVisible && (
        <ErrorPopup
          error={error}
          onClose={clearError}
          showDetails={true}
        />
      )}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};