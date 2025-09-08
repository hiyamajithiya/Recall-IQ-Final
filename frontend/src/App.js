import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import ErrorBoundary from './components/ErrorHandler/ErrorBoundary';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Dashboard from './pages/Dashboard';
import Templates from './pages/Templates';
import Groups from './pages/Groups';
import Recipients from './pages/Recipients';
import Batches from './pages/Batches';
import Logs from './pages/Logs';
import Analytics from './pages/Analytics';
import Users from './pages/Users';
import Tenants from './pages/Tenants';
import Profile from './pages/Profile';
import TenantUsers from './pages/TenantUsers';

// Component to handle role-based redirects
const RoleBasedRedirect = () => {
  const { user, loading, isAuthenticated } = useAuth();
  
  // Use actual user role
  const currentRole = user?.role;
  
  // Show loading while authentication is being checked
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }
  
  // If not authenticated, redirect to login will be handled by ProtectedRoute
  if (!isAuthenticated) {
    return null;
  }
  
  if (currentRole === 'super_admin' || currentRole === 'support_team') {
    return <Navigate to="/admin/dashboard" replace />;
  } else if (['tenant_admin', 'staff_admin', 'staff', 'sales_team'].includes(currentRole)) {
    return <Navigate to="/tenant-admin/dashboard" replace />;
  } else {
    return <Dashboard />;
  }
};

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router>
          <div className="App">
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                duration: 3000,
                theme: {
                  primary: '#4aed88',
                },
              },
            }}
          />
          
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            
            {/* Root redirect to appropriate dashboard */}
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <RoleBasedRedirect />
                </ProtectedRoute>
              } 
            />
            
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route path="templates" element={<Templates />} />
              <Route path="groups" element={<Groups />} />
              <Route path="recipients" element={<Recipients />} />
              <Route path="batches" element={<Batches />} />
              <Route path="logs" element={<Logs />} />
              <Route path="analytics" element={<Analytics />} />
              <Route path="profile" element={<Profile />} />
              <Route 
                path="tenant-users" 
                element={
                  <ProtectedRoute requiredRole="tenant_admin">
                    <TenantUsers />
                  </ProtectedRoute>
                } 
              />
              
              {/* Super Admin Routes */}
              <Route
                path="admin/*"
                element={
                  <ProtectedRoute requiredRole={["super_admin", "support_team"]}>
                    <Routes>
                      <Route index element={<Navigate to="/admin/dashboard" replace />} />
                      <Route path="dashboard" element={<Dashboard />} />
                      <Route path="users" element={<Users />} />
                      <Route path="tenants" element={<Tenants />} />
                      <Route path="logs" element={<Logs />} />
                      <Route path="analytics" element={<Analytics />} />
                      <Route path="profile" element={<Profile />} />
                    </Routes>
                  </ProtectedRoute>
                }
              />
              
              {/* Tenant Admin Routes */}
              <Route
                path="tenant-admin/*"
                element={
                  <ProtectedRoute requiredRole={["tenant_admin", "staff_admin", "staff", "sales_team"]}>
                    <Routes>
                      <Route index element={<Navigate to="/tenant-admin/dashboard" replace />} />
                      <Route path="dashboard" element={<Dashboard />} />
                      <Route path="templates" element={<Templates />} />
                      <Route path="groups" element={<Groups />} />
                      <Route path="recipients" element={<Recipients />} />
                      <Route path="batches" element={<Batches />} />
                      <Route path="logs" element={<Logs />} />
                      <Route path="analytics" element={<Analytics />} />
                      <Route path="users" element={<TenantUsers />} />
                      <Route path="profile" element={<Profile />} />
                    </Routes>
                  </ProtectedRoute>
                }
              />
              
              {/* Legacy Routes for backward compatibility */}
              <Route
                path="users"
                element={
                  <ProtectedRoute requiredRole={["super_admin", "support_team"]}>
                    <Users />
                  </ProtectedRoute>
                }
              />
              <Route
                path="tenants"
                element={
                  <ProtectedRoute requiredRole={["super_admin", "support_team"]}>
                    <Tenants />
                  </ProtectedRoute>
                }
              />
            </Route>
            
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
          </div>
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;