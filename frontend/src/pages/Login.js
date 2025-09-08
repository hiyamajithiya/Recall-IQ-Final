import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useForm } from 'react-hook-form';
import { EyeIcon, EyeSlashIcon, BellAlertIcon, ClockIcon, CalendarDaysIcon, EnvelopeIcon, PhoneIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import '../styles/login-animations.css';

// Load Google OAuth script
const loadGoogleScript = () => {
  return new Promise((resolve) => {
    if (typeof window.google !== 'undefined') {
      resolve();
      return;
    }
    
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.onload = resolve;
    document.head.appendChild(script);
  });
};

export default function Login() {
  const { login, googleOAuthSignup, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [activeFeature, setActiveFeature] = useState(0);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: {
      login: '',
      password: ''
    }
  });

  const from = location.state?.from?.pathname || '/';

  // Google OAuth callback handler for Login
  const handleGoogleCallback = async (response) => {
    console.log('Google OAuth login callback received:', response);
    
    setIsSubmitting(true);
    try {
      console.log('Attempting Google OAuth login...');
      // For login, we don't need tenant data - just authenticate with the credential
      const result = await googleOAuthSignup(response.credential, null);
      console.log('Google OAuth login result:', result);
      
      if (result.success) {
        toast.success('Login successful with Google!');
        navigate(from, { replace: true });
      } else {
        toast.error(result.error || 'Google login failed');
      }
    } catch (error) {
      console.error('Google login error:', error);
      toast.error('Google login failed: ' + (error.message || 'Unknown error'));
    } finally {
      setIsSubmitting(false);
    }
  };

  // Initialize Google OAuth
  useEffect(() => {
    const clientId = process.env.REACT_APP_GOOGLE_OAUTH_CLIENT_ID || '589523695138-m7j8tq6lpls2l60jbn1di8aqo6qkk31e.apps.googleusercontent.com';
    
    console.log('Login - Google OAuth Client ID:', clientId);
    
    loadGoogleScript().then(() => {
      if (window.google && clientId) {
        console.log('Login - Initializing Google OAuth with client ID:', clientId);
        
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: handleGoogleCallback,
        });
        
        setTimeout(() => {
          const buttonElement = document.getElementById('google-signin-button-login');
          if (buttonElement) {
            window.google.accounts.id.renderButton(
              buttonElement,
              {
                theme: 'outline',
                size: 'large',
                text: 'signin_with',
                width: '100%',
                shape: 'rectangular',
              }
            );
            
            // Apply custom styling to match submit button
            setTimeout(() => {
              const googleBtn = buttonElement.querySelector('div[role="button"]');
              if (googleBtn) {
                googleBtn.style.borderRadius = '0.75rem'; // Same as rounded-xl (12px)
                googleBtn.style.height = '42px'; // Match submit button height
              }
            }, 100);
            
            console.log('Login - Google Sign-In button rendered successfully');
          } else {
            console.error('Login - Google sign-in button element not found');
          }
        }, 100);
      } else {
        console.error('Login - Google script not loaded or Client ID missing:', {
          googleLoaded: !!window.google,
          clientId: clientId
        });
      }
    }).catch(error => {
      console.error('Login - Failed to load Google script:', error);
    });
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveFeature((prev) => (prev + 1) % 3);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    try {
      const result = await login(data);
      if (result.success) {
        toast.success('Login successful!');
        navigate(from, { replace: true });
      } else {
        toast.error(result.error);
      }
    } catch (error) {
      toast.error('An error occurred during login');
    } finally {
      setIsSubmitting(false);
    }
  };

  const features = [
    {
      icon: BellAlertIcon,
      title: "Smart Reminders",
      description: "Automated follow-ups that never miss",
      gradient: "from-yellow-400 to-orange-500",
      delay: "0"
    },
    {
      icon: ClockIcon,
      title: "Perfect Timing",
      description: "Schedule reminders at optimal times",
      gradient: "from-green-400 to-emerald-500",
      delay: "100"
    },
    {
      icon: CalendarDaysIcon,
      title: "Recurring Tasks",
      description: "Set once, remind forever",
      gradient: "from-purple-400 to-pink-500",
      delay: "200"
    },
    {
      icon: EnvelopeIcon,
      title: "Multi-Channel",
      description: "Email, SMS & in-app notifications",
      gradient: "from-blue-400 to-indigo-500",
      delay: "300"
    },
    {
      icon: ChartBarIcon,
      title: "Track Success",
      description: "Monitor response & engagement rates",
      gradient: "from-teal-400 to-cyan-500",
      delay: "400"
    },
    {
      icon: PhoneIcon,
      title: "Voice Calls",
      description: "Automated voice reminder system",
      gradient: "from-rose-400 to-red-500",
      delay: "500"
    }
  ];

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 p-4 overflow-auto">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-yellow-500 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-2000"></div>
        <div className="absolute top-40 left-40 w-80 h-80 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-4000"></div>
      </div>

      {/* Blurred Background for Edges */}
      <div className="absolute inset-0">
        <div className="absolute top-0 left-0 right-0 h-24 bg-gradient-to-b from-black/20 to-transparent backdrop-blur-sm"></div>
        <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-black/20 to-transparent backdrop-blur-sm"></div>
        <div className="absolute top-0 bottom-0 left-0 w-24 bg-gradient-to-r from-black/20 to-transparent backdrop-blur-sm"></div>
        <div className="absolute top-0 bottom-0 right-0 w-24 bg-gradient-to-l from-black/20 to-transparent backdrop-blur-sm"></div>
      </div>

      {/* Centered Card Container */}
      <div className="relative z-10 w-full max-w-6xl bg-white/10 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/30 animate-fade-in-up">
        <div className="flex flex-col lg:flex-row h-full">
          {/* Left Column - Features */}
          <div className="lg:w-1/2 p-6 lg:pr-2 lg:pl-20 flex flex-col justify-center">
            <div className="mb-6 animate-fade-in-down text-center lg:text-left">
              <p className="text-gray-200 text-base font-light">Automated Reminder System</p>
              <h2 className="text-xl font-bold text-white">Never Miss Important Follow-ups</h2>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {features.map((feature, index) => (
                <div 
                  key={index} 
                  className={`group relative bg-white/10 backdrop-blur-lg rounded-2xl p-4 border border-white/20 hover:bg-white/20 transition-all duration-500 hover:scale-105 hover:-translate-y-1 animate-fade-in-up flex flex-col justify-between min-h-[120px]`}
                  style={{ animationDelay: `${feature.delay}ms` }}
                >
                  <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-10 rounded-2xl transition-opacity duration-500`}></div>
                  <div className="relative flex flex-col h-full">
                    <div className={`inline-flex p-2 bg-gradient-to-br ${feature.gradient} rounded-xl mb-2 group-hover:scale-110 transition-transform duration-300 w-fit`}>
                      <feature.icon className="h-5 w-5 text-white" />
                    </div>
                    <h3 className="text-white font-bold text-sm mb-1">{feature.title}</h3>
                    <p className="text-gray-300 text-xs leading-relaxed flex-1">{feature.description}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Copyright Notice */}
            <div className="mt-8 text-center">
              <p className="text-gray-400 text-xs">
                © {new Date().getFullYear()} All Rights Reserved by Chinmay Technosoft Pvt Ltd
              </p>
            </div>
          </div>

          {/* Right Column - Login Form */}
          <div className="lg:w-1/2 p-6 lg:pl-1 lg:pr-4 flex items-center justify-center">
            <div className="max-w-sm w-full">
              <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl p-6 space-y-4 border border-white/50">
                <div className="text-center">
                  <div className="inline-flex p-3 bg-white rounded-2xl mb-3 shadow-lg">
                    <BellAlertIcon className="h-8 w-8 text-purple-600" />
                  </div>
                  <h1 className="text-xl font-black text-gray-900 mb-1 bg-clip-text text-transparent bg-gradient-to-r from-purple-600 to-indigo-600">
                    RecallIQ
                  </h1>
                  <h2 className="text-lg font-bold text-gray-900">
                    Welcome Back!
                  </h2>
                  <p className="mt-1 text-sm text-gray-500">
                    Access your reminder dashboard
                  </p>
                </div>
                
                <form className="space-y-3" onSubmit={handleSubmit(onSubmit)}>
                  <div className="space-y-3">
                    <div className="group">
                      <label htmlFor="login" className="block text-xs font-semibold text-gray-700 mb-1 uppercase tracking-wider">
                        Username / Email
                      </label>
                      <div className="relative">
                        <input
                          {...register('login', { 
                            required: 'Username or Email is required'
                          })}
                          id="login"
                          type="text"
                          autoComplete="username"
                          className="appearance-none relative block w-full px-3 py-2 border-2 border-gray-200 placeholder-gray-400 text-gray-900 rounded-xl focus:outline-none focus:ring-0 focus:border-purple-500 transition-all duration-300 hover:border-gray-300 text-sm"
                          placeholder="Enter your credentials"
                        />
                      </div>
                      {errors.login && (
                        <p className="mt-1 text-xs text-red-500 animate-shake">{errors.login.message}</p>
                      )}
                    </div>
                    
                    <div className="group">
                      <label htmlFor="password" className="block text-xs font-semibold text-gray-700 mb-1 uppercase tracking-wider">
                        Password
                      </label>
                      <div className="relative">
                        <input
                          {...register('password', { required: 'Password is required' })}
                          type={showPassword ? 'text' : 'password'}
                          className="appearance-none relative block w-full px-3 py-2 pr-10 border-2 border-gray-200 placeholder-gray-400 text-gray-900 rounded-xl focus:outline-none focus:ring-0 focus:border-purple-500 transition-all duration-300 hover:border-gray-300 text-sm"
                          placeholder="Enter your password"
                          autoComplete="current-password"
                        />
                        <button
                          type="button"
                          className="absolute inset-y-0 right-0 pr-3 flex items-center group"
                          onClick={() => setShowPassword(!showPassword)}
                          tabIndex={-1}
                        >
                          {showPassword ? (
                            <EyeSlashIcon className="h-4 w-4 text-gray-400 group-hover:text-purple-500 transition-colors" />
                          ) : (
                            <EyeIcon className="h-4 w-4 text-gray-400 group-hover:text-purple-500 transition-colors" />
                          )}
                        </button>
                      </div>
                      {errors.password && (
                        <p className="mt-1 text-xs text-red-500 animate-shake">{errors.password.message}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center">
                      <input
                        id="remember-me"
                        name="remember-me"
                        type="checkbox"
                        className="h-3 w-3 text-purple-600 focus:ring-purple-500 border-gray-300 rounded transition-all duration-200"
                      />
                      <label htmlFor="remember-me" className="ml-2 text-gray-600 text-xs">
                        Remember me
                      </label>
                    </div>

                    <Link
                      to="/forgot-password"
                      className="font-medium text-purple-600 hover:text-purple-500 transition-colors text-xs"
                    >
                      Forgot password?
                    </Link>
                  </div>

                  <button
                    type="submit"
                    disabled={isSubmitting || loading}
                    className="relative w-full flex justify-center py-2.5 px-4 border border-transparent text-sm font-bold rounded-xl text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] shadow-lg hover:shadow-xl"
                  >
                    {isSubmitting ? (
                      <div className="flex items-center">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Signing in...
                      </div>
                    ) : (
                      <span className="flex items-center">
                        Sign In
                        <svg className="ml-2 w-4 h-4 animate-bounce-x" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                        </svg>
                      </span>
                    )}
                  </button>

                  {/* Divider */}
                  <div className="relative my-4 flex items-center">
                    <div className="flex-grow border-t border-gray-350"></div>
                    <span className="px-1.5 text-gray-500 font-semibold text-xs uppercase">OR</span>
                    <div className="flex-grow border-t border-gray-350"></div>
                  </div>

                  {/* Google Sign In Button */}
                  <div className="mb-4">
                    <div id="google-signin-button-login" className="flex justify-center"></div>
                  </div>

                  <div className="text-center">
                    <span className="text-xs text-gray-600">
                      New to RecallIQ?{' '}
                      <Link
                        to="/register"
                        className="font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 transition-all"
                      >
                        Create Account
                      </Link>
                    </span>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}