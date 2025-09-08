import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useForm } from 'react-hook-form';
import { EyeIcon, EyeSlashIcon, BellAlertIcon } from '@heroicons/react/24/outline';
import { authAPI } from '../utils/api';
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

export default function Register() {
  const { register: registerUser, googleOAuthSignup, loginWithTokens, loading } = useAuth();
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [otpData, setOtpData] = useState(null);
  const [otpValue, setOtpValue] = useState('');

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm();

  const password = watch('password');

  const handleGoogleCallback = async (response) => {
    const formData = new FormData(document.getElementById('registration-form'));
    const tenantData = {
      company_name: formData.get('company_name'),
      company_address: formData.get('company_address'),
      contact_person: formData.get('contact_person'),
      contact_email: formData.get('contact_email'),
      contact_phone: formData.get('contact_phone'),
    };

    // Check if all required tenant data is provided
    const requiredFields = ['company_name', 'company_address', 'contact_person', 'contact_email', 'contact_phone'];
    const missingFields = requiredFields.filter(field => !tenantData[field]);
    
    if (missingFields.length > 0) {
      toast.error('Please fill in all company details before using Google sign up');
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await googleOAuthSignup(response.credential, tenantData);
      if (result.success) {
        toast.success('Registration successful with Google!');
        navigate('/');
      } else {
        toast.error(result.error);
      }
    } catch (error) {
      toast.error('Google sign up failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  React.useEffect(() => {
    const clientId = process.env.REACT_APP_GOOGLE_OAUTH_CLIENT_ID || '589523695138-m7j8tq6lpls2l60jbn1di8aqo6qkk31e.apps.googleusercontent.com';
    
    console.log('Google OAuth Client ID:', clientId);
    
    loadGoogleScript().then(() => {
      // Initialize Google Sign-In
      if (window.google && clientId) {
        console.log('Initializing Google OAuth with client ID:', clientId);
        
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: handleGoogleCallback,
        });
        
        // Wait for DOM element to be ready
        setTimeout(() => {
          const buttonElement = document.getElementById('google-signin-button');
          if (buttonElement) {
            window.google.accounts.id.renderButton(
              buttonElement,
              {
                theme: 'outline',
                size: 'large',
                text: 'continue_with',
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
            
            console.log('Google Sign-In button rendered successfully');
          } else {
            console.error('Google sign-in button element not found');
          }
        }, 100);
      } else {
        console.error('Google script not loaded or Client ID missing:', {
          googleLoaded: !!window.google,
          clientId: clientId
        });
      }
    }).catch(error => {
      console.error('Failed to load Google script:', error);
    });
  }, [handleGoogleCallback]);

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    try {
      // Request OTP for email verification
      await authAPI.requestSignupOTP(data);
      setOtpData(data);
      setCurrentStep(3);
      toast.success('OTP sent to your email address');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'An error occurred during registration');
    } finally {
      setIsSubmitting(false);
    }
  };

  const nextStep = () => setCurrentStep(2);
  const prevStep = () => setCurrentStep(1);
  const prevStepFromOtp = () => setCurrentStep(2);

  const handleOtpSubmit = async () => {
    if (!otpValue || otpValue.length !== 6) {
      toast.error('Please enter a valid 6-digit OTP');
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await authAPI.verifySignupOTP({
        email: otpData.email,
        otp: otpValue
      });
      
      // Check for successful response
      if (result.data.success) {
        toast.success('Registration completed successfully!');
        
        // Auto login the user with the returned tokens
        if (result.data.access && result.data.refresh && result.data.user) {
          const loginResult = await loginWithTokens(
            result.data.access,
            result.data.refresh,
            result.data.user
          );
          
          if (loginResult.success) {
            toast.success('Welcome to RecallIQ! Redirecting to dashboard...');
            setTimeout(() => {
              navigate('/');
            }, 1500);
          } else {
            toast.success('Account created successfully! Please login with your credentials.');
            setTimeout(() => {
              navigate('/login');
            }, 2000);
          }
        } else {
          // Fallback to login page
          toast.success('Account created successfully! Please login with your credentials.');
          setTimeout(() => {
            navigate('/login');
          }, 2000);
        }
      } else {
        toast.error(result.data.message || 'OTP verification failed');
      }
    } catch (error) {
      // Handle axios treating 201 as success but different response structure
      if (error.response?.status === 201 && error.response?.data?.success) {
        toast.success('Registration completed successfully!');
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      } else {
        toast.error(error.response?.data?.error || error.response?.data?.detail || 'OTP verification failed');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const resendOtp = async () => {
    if (!otpData) return;
    
    try {
      await authAPI.requestSignupOTP(otpData);
      toast.success('OTP resent to your email');
    } catch (error) {
      toast.error('Failed to resend OTP');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900">
      {/* Animated Background Elements */}
      <div className="fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-yellow-500 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-2000"></div>
        <div className="absolute top-40 left-40 w-80 h-80 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-blob animation-delay-4000"></div>
      </div>

      <div className="max-w-2xl mx-auto relative z-10 px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center mb-6 animate-fade-in-down">
          <div className="inline-flex p-3 bg-white rounded-xl mb-3 shadow-lg">
            <BellAlertIcon className="h-8 w-8 text-purple-600" />
          </div>
          <h1 className="text-3xl font-black text-white mb-2 bg-clip-text text-transparent bg-gradient-to-r from-pink-300 to-indigo-300">
            RecallIQ
          </h1>
          <h2 className="text-xl font-bold text-white">
            Start Your Reminder Journey
          </h2>
          <p className="mt-2 text-base text-gray-200">
            Set up your organization's automated reminder system
          </p>
        </div>

        {/* Step Indicator */}
        <div className="flex justify-center mb-6">
          <div className="flex items-center space-x-4 bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/20">
            <div className={`flex items-center justify-center w-10 h-10 rounded-full text-sm font-bold transition-all duration-300 ${currentStep >= 1 ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg' : 'bg-white/20 text-gray-300'}`}>
              1
            </div>
            <div className={`w-16 h-1 rounded-full transition-all duration-300 ${currentStep >= 2 ? 'bg-gradient-to-r from-purple-600 to-indigo-600' : 'bg-white/20'}`}></div>
            <div className={`flex items-center justify-center w-10 h-10 rounded-full text-sm font-bold transition-all duration-300 ${currentStep >= 2 ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg' : 'bg-white/20 text-gray-300'}`}>
              2
            </div>
            <div className={`w-16 h-1 rounded-full transition-all duration-300 ${currentStep >= 3 ? 'bg-gradient-to-r from-purple-600 to-indigo-600' : 'bg-white/20'}`}></div>
            <div className={`flex items-center justify-center w-10 h-10 rounded-full text-sm font-bold transition-all duration-300 ${currentStep >= 3 ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg' : 'bg-white/20 text-gray-300'}`}>
              3
            </div>
          </div>
        </div>

        <form id="registration-form" className="animate-fade-in-up" onSubmit={handleSubmit(onSubmit)}>
          {currentStep === 1 ? (
            // Step 1: Company Details
            <div className="bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl p-6 border border-white/50">
              <h3 className="text-xl font-bold text-gray-900 mb-4 text-center">Organization Setup</h3>
              <div className="space-y-4">
                <div>
                  <label htmlFor="company_name" className="block text-sm font-semibold text-gray-700 mb-2">
                    Organization Name *
                  </label>
                  <input
                    {...register('company_name', { required: 'Organization name is required' })}
                    type="text"
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-0 focus:border-purple-500 transition-all duration-300 hover:border-gray-300 text-base"
                    placeholder="Enter your organization name"
                  />
                  {errors.company_name && (
                    <p className="mt-2 text-sm text-red-500 animate-shake">{errors.company_name.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="company_address" className="block text-sm font-semibold text-gray-700 mb-2">
                    Organization Address *
                  </label>
                  <textarea
                    {...register('company_address', { required: 'Organization address is required' })}
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-0 focus:border-purple-500 transition-all duration-300 hover:border-gray-300 resize-none text-base"
                    rows="2"
                    placeholder="Enter your complete business address"
                  />
                  {errors.company_address && (
                    <p className="mt-2 text-sm text-red-500 animate-shake">{errors.company_address.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="contact_person" className="block text-sm font-semibold text-gray-700 mb-2">
                    Primary Contact Person *
                  </label>
                  <input
                    {...register('contact_person', { required: 'Contact person is required' })}
                    type="text"
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-0 focus:border-purple-500 transition-all duration-300 hover:border-gray-300 text-base"
                    placeholder="Full name of primary contact"
                  />
                  {errors.contact_person && (
                    <p className="mt-2 text-sm text-red-500 animate-shake">{errors.contact_person.message}</p>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="contact_email" className="block text-sm font-semibold text-gray-700 mb-2">
                      Business Email *
                    </label>
                    <input
                      {...register('contact_email', {
                        required: 'Business email is required',
                        pattern: {
                          value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                          message: 'Please enter a valid email address',
                        },
                      })}
                      type="email"
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-0 focus:border-purple-500 transition-all duration-300 hover:border-gray-300 text-base"
                      placeholder="business@company.com"
                    />
                    {errors.contact_email && (
                      <p className="mt-2 text-sm text-red-500 animate-shake">{errors.contact_email.message}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="contact_phone" className="block text-sm font-semibold text-gray-700 mb-2">
                      Business Phone *
                    </label>
                    <input
                      {...register('contact_phone', { required: 'Business phone is required' })}
                      type="tel"
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-0 focus:border-purple-500 transition-all duration-300 hover:border-gray-300 text-base"
                      placeholder="+1 (555) 123-4567"
                    />
                    {errors.contact_phone && (
                      <p className="mt-2 text-sm text-red-500 animate-shake">{errors.contact_phone.message}</p>
                    )}
                  </div>
                </div>

                {/* Google Sign Up Option */}
                <div className="pt-4 border-t border-gray-200">
                  <div id="google-signin-button" className="flex justify-center"></div>
                </div>
              </div>

              <div className="mt-6">
                <button
                  type="button"
                  onClick={nextStep}
                  className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg text-base font-bold text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] shadow-lg hover:shadow-xl"
                >
                  Continue to Admin Account
                  <svg className="ml-2 w-5 h-5 animate-bounce-x" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </button>
              </div>
            </div>
          ) : currentStep === 2 ? (
            // Step 2: User Account Details
            <div className="bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl p-6 border border-white/50">
              <h3 className="text-xl font-bold text-gray-900 mb-4 text-center">Admin Account Setup</h3>
              <div className="space-y-4">
                <div>
                  <label htmlFor="username" className="block text-sm font-semibold text-gray-700 mb-2">
                    Admin Username *
                  </label>
                  <input
                    {...register('username', {
                      required: 'Username is required',
                      minLength: { value: 3, message: 'Username must be at least 3 characters' },
                    })}
                    type="text"
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-0 focus:border-purple-500 transition-all duration-300 hover:border-gray-300 text-base"
                    placeholder="Choose a unique username"
                  />
                  {errors.username && (
                    <p className="mt-2 text-sm text-red-500 animate-shake">{errors.username.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-semibold text-gray-700 mb-2">
                    Admin Email Address *
                  </label>
                  <input
                    {...register('email', {
                      required: 'Email is required',
                      pattern: {
                        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                        message: 'Please enter a valid email address',
                      },
                    })}
                    type="email"
                    className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-0 focus:border-purple-500 transition-all duration-300 hover:border-gray-300 text-base"
                    placeholder="admin@yourcompany.com"
                  />
                  {errors.email && (
                    <p className="mt-2 text-sm text-red-500 animate-shake">{errors.email.message}</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="first_name" className="block text-sm font-semibold text-gray-700 mb-2">
                      First Name *
                    </label>
                    <input
                      {...register('first_name', { required: 'First name is required' })}
                      type="text"
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-0 focus:border-purple-500 transition-all duration-300 hover:border-gray-300 text-base"
                      placeholder="First name"
                    />
                    {errors.first_name && (
                      <p className="mt-2 text-sm text-red-500 animate-shake">{errors.first_name.message}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="last_name" className="block text-sm font-semibold text-gray-700 mb-2">
                      Last Name *
                    </label>
                    <input
                      {...register('last_name', { required: 'Last name is required' })}
                      type="text"
                      className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-0 focus:border-purple-500 transition-all duration-300 hover:border-gray-300 text-base"
                      placeholder="Last name"
                    />
                    {errors.last_name && (
                      <p className="mt-2 text-sm text-red-500 animate-shake">{errors.last_name.message}</p>
                    )}
                  </div>
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-semibold text-gray-700 mb-2">
                    Create Password *
                  </label>
                  <div className="relative">
                    <input
                      {...register('password', {
                        required: 'Password is required',
                        minLength: { value: 8, message: 'Password must be at least 8 characters' },
                      })}
                      type={showPassword ? 'text' : 'password'}
                      className="w-full px-4 py-3 pr-12 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-0 focus:border-purple-500 transition-all duration-300 hover:border-gray-300 text-base"
                      placeholder="Create a strong password"
                    />
                    <button
                      type="button"
                      className="absolute inset-y-0 right-0 pr-4 flex items-center"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? (
                        <EyeSlashIcon className="h-5 w-5 text-gray-400 hover:text-purple-500 transition-colors" />
                      ) : (
                        <EyeIcon className="h-5 w-5 text-gray-400 hover:text-purple-500 transition-colors" />
                      )}
                    </button>
                  </div>
                  {errors.password && (
                    <p className="mt-2 text-sm text-red-500 animate-shake">{errors.password.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="password_confirm" className="block text-sm font-semibold text-gray-700 mb-2">
                    Confirm Password *
                  </label>
                  <div className="relative">
                    <input
                      {...register('password_confirm', {
                        required: 'Please confirm your password',
                        validate: (value) => value === password || 'Passwords do not match',
                      })}
                      type={showConfirmPassword ? 'text' : 'password'}
                      className="w-full px-4 py-3 pr-12 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-0 focus:border-purple-500 transition-all duration-300 hover:border-gray-300 text-base"
                      placeholder="Confirm your password"
                    />
                    <button
                      type="button"
                      className="absolute inset-y-0 right-0 pr-4 flex items-center"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    >
                      {showConfirmPassword ? (
                        <EyeSlashIcon className="h-5 w-5 text-gray-400 hover:text-purple-500 transition-colors" />
                      ) : (
                        <EyeIcon className="h-5 w-5 text-gray-400 hover:text-purple-500 transition-colors" />
                      )}
                    </button>
                  </div>
                  {errors.password_confirm && (
                    <p className="mt-2 text-sm text-red-500 animate-shake">{errors.password_confirm.message}</p>
                  )}
                </div>
              </div>

              <div className="mt-6 flex space-x-4">
                <button
                  type="button"
                  onClick={prevStep}
                  className="flex-1 flex justify-center py-3 px-4 border-2 border-gray-300 rounded-lg text-base font-semibold text-gray-700 bg-white hover:bg-gray-50 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition-all duration-300"
                >
                  Back
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || loading}
                  className="flex-1 flex justify-center py-3 px-4 border border-transparent rounded-lg text-base font-bold text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] shadow-lg hover:shadow-xl"
                >
                  {isSubmitting ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Sending...
                    </div>
                  ) : (
                    <span className="flex items-center">
                      Send Code
                      <svg className="ml-2 w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 3.26a2 2 0 001.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                    </span>
                  )}
                </button>
              </div>
            </div>
          ) : (
            // Step 3: OTP Verification
            <div className="bg-white/95 backdrop-blur-xl rounded-2xl shadow-2xl p-6 border border-white/50">
              <h3 className="text-xl font-bold text-gray-900 mb-4 text-center">Email Verification</h3>
              <div className="text-center space-y-6">
                <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-gradient-to-br from-purple-100 to-indigo-100 animate-bounce-slow">
                  <svg
                    className="h-8 w-8 text-purple-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 8l7.89 3.26a2 2 0 001.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                    />
                  </svg>
                </div>
                <div>
                  <p className="text-gray-600 text-base">
                    We've sent a 6-digit verification code to
                  </p>
                  <p className="text-lg font-semibold text-gray-900 mt-2">
                    {otpData?.email}
                  </p>
                </div>
                
                <div>
                  <label htmlFor="otp" className="block text-sm font-semibold text-gray-700 mb-3">
                    Enter Verification Code
                  </label>
                  <input
                    type="text"
                    value={otpValue}
                    onChange={(e) => setOtpValue(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    className="w-full px-4 py-4 border-2 border-gray-200 rounded-lg focus:outline-none focus:ring-0 focus:border-purple-500 transition-all duration-300 text-center text-3xl tracking-[0.4em] font-bold text-gray-900 hover:border-gray-300"
                    placeholder="000000"
                    maxLength="6"
                  />
                </div>
                
                <div className="text-sm text-gray-600">
                  Didn't receive the code?{' '}
                  <button
                    type="button"
                    onClick={resendOtp}
                    className="font-semibold text-purple-600 hover:text-purple-500 transition-colors"
                  >
                    Resend Code
                  </button>
                </div>
              </div>

              <div className="mt-6 flex space-x-4">
                <button
                  type="button"
                  onClick={prevStepFromOtp}
                  className="flex-1 flex justify-center py-3 px-4 border-2 border-gray-300 rounded-lg text-base font-semibold text-gray-700 bg-white hover:bg-gray-50 hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition-all duration-300"
                >
                  Back
                </button>
                <button
                  type="button"
                  onClick={handleOtpSubmit}
                  disabled={isSubmitting || otpValue.length !== 6}
                  className="flex-1 flex justify-center py-3 px-4 border border-transparent rounded-lg text-base font-bold text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] shadow-lg hover:shadow-xl"
                >
                  {isSubmitting ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                      Creating Account...
                    </div>
                  ) : (
                    <span className="flex items-center">
                      Complete Setup
                      <svg className="ml-2 w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </span>
                  )}
                </button>
              </div>
            </div>
          )}

          <div className="text-center mt-6 animate-fade-in-up">
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/20">
              <p className="text-sm text-gray-200">
                Already have an account?{' '}
                <Link 
                  to="/login" 
                  className="font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-300 to-indigo-300 hover:from-pink-200 hover:to-indigo-200 transition-all"
                >
                  Sign in to your dashboard
                </Link>
              </p>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}