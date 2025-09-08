import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Footer from './Footer';
import {
  HomeIcon,
  UserGroupIcon,
  DocumentTextIcon,
  EnvelopeIcon,
  ClipboardDocumentListIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon,
  UserIcon,
  UsersIcon,
} from '@heroicons/react/24/outline';

const getNavigationForRole = (role) => {
  if (role === 'super_admin' || role === 'support_team') {
    return [
      { name: 'Dashboard', href: '/admin/dashboard', icon: HomeIcon },
      { name: 'Tenants', href: '/admin/tenants', icon: Cog6ToothIcon },
      { name: 'Users', href: '/admin/users', icon: UserGroupIcon },
      { name: 'Email Logs', href: '/admin/logs', icon: ClipboardDocumentListIcon },
      // { name: 'Analytics', href: '/admin/analytics', icon: ChartBarIcon },
    ];
  } else if (role === 'tenant_admin' || role === 'sales_team') {
    // Tenant admin gets full navigation including user management
    return [
      { name: 'Dashboard', href: '/tenant-admin/dashboard', icon: HomeIcon },
      { name: 'Email Templates', href: '/tenant-admin/templates', icon: DocumentTextIcon },
      { name: 'Contact Groups', href: '/tenant-admin/groups', icon: UserGroupIcon },
      { name: 'Recipients', href: '/tenant-admin/recipients', icon: UsersIcon },
      { name: 'Email Batches', href: '/tenant-admin/batches', icon: EnvelopeIcon },
      { name: 'Email Logs', href: '/tenant-admin/logs', icon: ClipboardDocumentListIcon },
      // { name: 'Analytics', href: '/tenant-admin/analytics', icon: ChartBarIcon },
      { name: 'Organization Users', href: '/tenant-admin/users', icon: UserIcon },
    ];
  } else if (role === 'staff_admin') {
    // Staff admin gets navigation without Organization Users tab
    return [
      { name: 'Dashboard', href: '/tenant-admin/dashboard', icon: HomeIcon },
      { name: 'Email Templates', href: '/tenant-admin/templates', icon: DocumentTextIcon },
      { name: 'Contact Groups', href: '/tenant-admin/groups', icon: UserGroupIcon },
      { name: 'Recipients', href: '/tenant-admin/recipients', icon: UsersIcon },
      { name: 'Email Batches', href: '/tenant-admin/batches', icon: EnvelopeIcon },
      { name: 'Email Logs', href: '/tenant-admin/logs', icon: ClipboardDocumentListIcon },
      // { name: 'Analytics', href: '/tenant-admin/analytics', icon: ChartBarIcon },
    ];
  } else if (role === 'staff') {
    // Staff users get navigation similar to tenant-admin but without Organization Users
    return [
      { name: 'Dashboard', href: '/tenant-admin/dashboard', icon: HomeIcon },
      { name: 'Email Templates', href: '/tenant-admin/templates', icon: DocumentTextIcon },
      { name: 'Contact Groups', href: '/tenant-admin/groups', icon: UserGroupIcon },
      { name: 'Recipients', href: '/tenant-admin/recipients', icon: UsersIcon },
      { name: 'Email Batches', href: '/tenant-admin/batches', icon: EnvelopeIcon },
      { name: 'Email Logs', href: '/tenant-admin/logs', icon: ClipboardDocumentListIcon },
      // { name: 'Analytics', href: '/tenant-admin/analytics', icon: ChartBarIcon },
    ];
  } else {
    // Regular users (tenant_member) - fallback for any other roles
    return [
      { name: 'Dashboard', href: '/', icon: HomeIcon },
      { name: 'Email Templates', href: '/templates', icon: DocumentTextIcon },
      { name: 'Contact Groups', href: '/groups', icon: UserGroupIcon },
      { name: 'Recipients', href: '/recipients', icon: UsersIcon },
      { name: 'Email Batches', href: '/batches', icon: EnvelopeIcon },
      { name: 'Email Logs', href: '/logs', icon: ClipboardDocumentListIcon },
      // { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
    ];
  }
};

function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (href) => {
    if (href === '/' || href === '/admin/dashboard' || href === '/tenant-admin/dashboard') {
      return location.pathname === href || 
             (href === '/' && location.pathname === '/') ||
             (href === '/admin/dashboard' && (location.pathname === '/admin' || location.pathname === '/admin/dashboard')) ||
             (href === '/tenant-admin/dashboard' && (location.pathname === '/tenant-admin' || location.pathname === '/tenant-admin/dashboard'));
    }
    return location.pathname.startsWith(href);
  };

  const allNavigation = getNavigationForRole(user?.role);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar */}
      <div className={`${sidebarOpen ? 'block' : 'hidden'} fixed inset-0 z-40 lg:hidden`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" aria-hidden="true" />
        <div className="relative flex w-64 flex-col bg-white shadow-xl">
          <div className="absolute top-0 right-0 -mr-12 pt-2">
            <button
              type="button"
              className="ml-1 flex h-10 w-10 items-center justify-center rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
              onClick={() => setSidebarOpen(false)}
            >
              <XMarkIcon className="h-6 w-6 text-white" aria-hidden="true" />
            </button>
          </div>
          <div className="h-0 flex-1 overflow-y-auto pt-5 pb-4">
            <div className="flex flex-shrink-0 items-center px-4">
              <h1 className="text-xl font-bold text-gray-900">RecallIQ</h1>
            </div>
            <nav className="mt-5 space-y-1 px-2">
              {allNavigation.map((item) => (
                <a
                  key={item.name}
                  href={item.href}
                  className={`sidebar-nav-item ${
                    isActive(item.href) ? 'sidebar-nav-item-active' : 'sidebar-nav-item-inactive'
                  }`}
                  onClick={(e) => {
                    e.preventDefault();
                    navigate(item.href);
                    setSidebarOpen(false);
                  }}
                >
                  <item.icon
                    className={`mr-4 flex-shrink-0 h-6 w-6 ${
                      isActive(item.href) ? 'text-recalliq-600' : 'text-gray-400 group-hover:text-recalliq-500'
                    }`}
                    aria-hidden="true"
                  />
                  {item.name}
                </a>
              ))}
            </nav>
          </div>
        </div>
      </div>

      {/* Static sidebar for desktop */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
        <div className="flex min-h-0 flex-1 flex-col bg-white shadow">
          <div className="flex h-16 flex-shrink-0 items-center gradient-bg px-4">
            <h1 className="text-xl font-bold text-white">RecallIQ</h1>
          </div>
          <div className="flex flex-1 flex-col overflow-y-auto pt-5 pb-4">
            <nav className="mt-5 flex-1 space-y-1 px-2">
              {allNavigation.map((item) => (
                <a
                  key={item.name}
                  href={item.href}
                  className={`sidebar-nav-item ${
                    isActive(item.href) ? 'sidebar-nav-item-active' : 'sidebar-nav-item-inactive'
                  }`}
                  onClick={(e) => {
                    e.preventDefault();
                    navigate(item.href);
                  }}
                >
                  <item.icon
                    className={`mr-3 flex-shrink-0 h-6 w-6 ${
                      isActive(item.href) ? 'text-recalliq-600' : 'text-gray-400 group-hover:text-recalliq-500'
                    }`}
                    aria-hidden="true"
                  />
                  {item.name}
                </a>
              ))}
            </nav>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <div className="sticky top-0 z-10 page-header">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
            <button
              type="button"
              className="-ml-0.5 -mt-0.5 inline-flex h-12 w-12 items-center justify-center rounded-md text-gray-500 hover:text-gray-900 lg:hidden"
              onClick={() => setSidebarOpen(true)}
            >
              <Bars3Icon className="h-6 w-6" aria-hidden="true" />
            </button>

            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                Welcome, <span className="font-medium">{user?.username}</span>
              </div>
              <div className={`text-xs px-2 py-1 rounded-full font-semibold ${
                user?.role === 'super_admin' || user?.role === 'support_team' ? 'text-red-700 bg-red-100' :
                user?.role === 'tenant_admin' || user?.role === 'staff_admin' || user?.role === 'staff' || user?.role === 'sales_team' ? 'text-blue-700 bg-blue-100' :
                'text-recalliq-600 bg-recalliq-100'
              }`}>
                {user?.role?.replace('_', ' ').toUpperCase()}
              </div>
              <button
                onClick={() => {
                  if (user?.role === 'super_admin' || user?.role === 'support_team') {
                    navigate('/admin/profile');
                  } else if (user?.role === 'tenant_admin' || user?.role === 'staff_admin' || user?.role === 'staff' || user?.role === 'sales_team') {
                    navigate('/tenant-admin/profile');
                  } else {
                    navigate('/profile');
                  }
                }}
                className="flex items-center text-gray-600 hover:text-gray-900"
                title="My Profile"
              >
                <UserIcon className="h-5 w-5" />
              </button>
              <button
                onClick={handleLogout}
                className="flex items-center text-gray-600 hover:text-gray-900"
                title="Logout"
              >
                <ArrowRightOnRectangleIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1">
          <div className="py-6 pb-16"> {/* Added pb-16 for footer space */}
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <Outlet />
            </div>
          </div>
        </main>
        <Footer />
      </div>
    </div>
  );
}