import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { tenantsAPI } from '../../utils/api';
import { XMarkIcon, CalendarIcon, BuildingOfficeIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function TenantModal({ tenant, mode, onClose, onSuccess }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [displayTrialEndDate, setDisplayTrialEndDate] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
    trigger,
  } = useForm();

  useEffect(() => {
    if (tenant && mode === 'edit') {
      setValue('name', tenant.name);
      setValue('plan', tenant.plan);
      setValue('status', tenant.status);
      setValue('monthly_email_limit', tenant.monthly_email_limit);
      setValue('company_address', tenant.company_address);
      setValue('contact_person', tenant.contact_person);
      setValue('contact_email', tenant.contact_email);
      setValue('contact_phone', tenant.contact_phone);
      setValue('billing_email', tenant.billing_email);
      setValue('payment_method', tenant.payment_method);
      // User limit fields
      setValue('max_tenant_admins', tenant.max_tenant_admins || 1);
      setValue('max_staff_admins', tenant.max_staff_admins || 1);
      setValue('max_staff_users', tenant.max_staff_users || 3);
      setValue('max_total_users', tenant.max_total_users || 5);
      if (tenant.subscription_start_date) {
        setValue('subscription_start_date', new Date(tenant.subscription_start_date).toISOString().slice(0, 16));
      }
      if (tenant.subscription_end_date) {
        setValue('subscription_end_date', new Date(tenant.subscription_end_date).toISOString().slice(0, 16));
      }
      if (tenant.trial_end_date) {
        setValue('trial_end_date', new Date(tenant.trial_end_date).toISOString().slice(0, 16));
      }
    }
  }, [tenant, mode, setValue]);

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    try {
      const tenantData = {
        ...data,
        is_active: true
      };

      if (mode === 'create') {
        await tenantsAPI.createTenant(tenantData);
        toast.success('Tenant created successfully with a 30-day trial.');
      } else {
        await tenantsAPI.updateTenant(tenant.id, tenantData);
        toast.success('Tenant updated successfully');
      }
      onSuccess();
    } catch (error) {
      let errorMsg = `Failed to ${mode} tenant. Please check the details.`;
      if (error.response?.data) {
          const errorDetails = Object.entries(error.response.data)
              .map(([key, value]) => `${key}: ${value}`)
              .join('\n');
          if (errorDetails) {
              errorMsg = errorDetails;
          }
      }
      toast.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const planLimits = {
    starter: 1000,
    professional: 10000,
    enterprise: 50000,
    custom: 0
  };

  const selectedPlan = watch('plan');
  const contactEmail = watch('contact_email');
  const billingEmail = watch('billing_email');
  const trialEndDate = watch('trial_end_date');
  const subscriptionStartDate = watch('subscription_start_date');
  
  useEffect(() => {
    if (selectedPlan && mode === 'create') {
      if (selectedPlan === 'custom') {
        setValue('monthly_email_limit', '');
      } else if (planLimits[selectedPlan]) {
        setValue('monthly_email_limit', planLimits[selectedPlan]);
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedPlan, setValue, mode]);

  useEffect(() => {
    if (contactEmail && !billingEmail) {
      setValue('billing_email', contactEmail);
    }
  }, [contactEmail, billingEmail, setValue]);

  useEffect(() => {
    if (mode === 'create') {
      const trialEndDate = new Date();
      trialEndDate.setDate(trialEndDate.getDate() + 30);
      setDisplayTrialEndDate(trialEndDate.toISOString().slice(0, 16));
    }
  }, [mode]);

  const getCurrentDateTime = () => {
    const now = new Date();
    return now.toISOString().slice(0, 16);
  };

  useEffect(() => {
    if (trialEndDate) {
      trigger('subscription_start_date');
    }
  }, [trialEndDate, trigger]);

  useEffect(() => {
    if (subscriptionStartDate) {
      trigger('subscription_end_date');
    }
  }, [subscriptionStartDate, trigger]);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />

        <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="card-header">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  <BuildingOfficeIcon className="h-6 w-6 inline mr-2" />
                  {mode === 'create' ? 'Create New Tenant' : 'Edit Tenant'}
                </h3>
                <button
                  type="button"
                  onClick={onClose}
                  className="action-button"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
            </div>

            <div className="px-6 py-4 max-h-96 overflow-y-auto">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left Column - Basic Info */}
                <div className="space-y-4">
                  <div>
                    <label className="form-label">Company Name *</label>
                    <input
                      {...register('name', { required: 'Company name is required' })}
                      type="text"
                      className="form-input"
                      placeholder="Enter company name"
                    />
                    {errors.name && (
                      <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="form-label">Subscription Plan *</label>
                    <select
                      {...register('plan', { required: 'Please select a plan' })}
                      className="form-input"
                    >
                      <option value="">Select a plan</option>
                      <option value="starter">Starter Plan (1,000 emails/month)</option>
                      <option value="professional">Professional Plan (10,000 emails/month)</option>
                      <option value="enterprise">Enterprise Plan (50,000 emails/month)</option>
                      <option value="custom">Custom Plan</option>
                    </select>
                    {errors.plan && (
                      <p className="mt-1 text-sm text-red-600">{errors.plan.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="form-label">Status</label>
                    <select
                      {...register('status')}
                      className="form-input"
                    >
                      <option value="trial">Trial</option>
                      <option value="active">Active</option>
                      <option value="suspended">Suspended</option>
                      <option value="cancelled">Cancelled</option>
                      <option value="expired">Expired</option>
                    </select>
                  </div>

                  <div>
                    <label className="form-label">Monthly Email Limit</label>
                    <input
                      {...register('monthly_email_limit', { 
                        required: 'Email limit is required',
                        min: { value: 0, message: 'Cannot be negative' }
                      })}
                      type="number"
                      className="form-input"
                      placeholder={selectedPlan === 'custom' ? 'Enter custom limit' : '1000'}
                    />
                    {errors.monthly_email_limit && (
                      <p className="mt-1 text-sm text-red-600">{errors.monthly_email_limit.message}</p>
                    )}
                    {selectedPlan === 'custom' && (
                      <p className="mt-1 text-xs text-gray-500">Enter 0 for unlimited emails</p>
                    )}
                  </div>

                  {/* User Limits Section */}
                  <div className="space-y-4 border-t pt-4">
                    <h4 className="text-sm font-medium text-gray-900 flex items-center">
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
                      </svg>
                      User Limits
                    </h4>
                    <p className="text-xs text-gray-500">Manually configure user limits for this tenant</p>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="form-label">Max Tenant Admins</label>
                        <input
                          {...register('max_tenant_admins', { 
                            required: 'Required',
                            min: { value: 1, message: 'Must be at least 1' },
                            valueAsNumber: true
                          })}
                          type="number"
                          min="1"
                          className="form-input"
                          placeholder="1"
                        />
                        {errors.max_tenant_admins && (
                          <p className="mt-1 text-xs text-red-600">{errors.max_tenant_admins.message}</p>
                        )}
                      </div>

                      <div>
                        <label className="form-label">Max Staff Admins</label>
                        <input
                          {...register('max_staff_admins', { 
                            required: 'Required',
                            min: { value: 0, message: 'Cannot be negative' },
                            valueAsNumber: true
                          })}
                          type="number"
                          min="0"
                          className="form-input"
                          placeholder="1"
                        />
                        {errors.max_staff_admins && (
                          <p className="mt-1 text-xs text-red-600">{errors.max_staff_admins.message}</p>
                        )}
                      </div>

                      <div>
                        <label className="form-label">Max Staff Users</label>
                        <input
                          {...register('max_staff_users', { 
                            required: 'Required',
                            min: { value: 0, message: 'Cannot be negative' },
                            valueAsNumber: true
                          })}
                          type="number"
                          min="0"
                          className="form-input"
                          placeholder="3"
                        />
                        {errors.max_staff_users && (
                          <p className="mt-1 text-xs text-red-600">{errors.max_staff_users.message}</p>
                        )}
                      </div>

                      <div>
                        <label className="form-label">Max Total Users</label>
                        <input
                          {...register('max_total_users', { 
                            required: 'Required',
                            min: { value: 1, message: 'Must be at least 1' },
                            valueAsNumber: true
                          })}
                          type="number"
                          min="1"
                          className="form-input"
                          placeholder="5"
                        />
                        {errors.max_total_users && (
                          <p className="mt-1 text-xs text-red-600">{errors.max_total_users.message}</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right Column - Contact & Billing */}
                <div className="space-y-4">
                  <div>
                    <label className="form-label">Contact Person *</label>
                    <input
                      {...register('contact_person', { required: 'Contact person is required' })}
                      type="text"
                      className="form-input"
                      placeholder="Enter contact person name"
                    />
                    {errors.contact_person && (
                      <p className="mt-1 text-sm text-red-600">{errors.contact_person.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="form-label">Contact Email *</label>
                    <input
                      {...register('contact_email', {
                        required: 'Contact email is required',
                        pattern: {
                          value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                          message: 'Invalid email address'
                        }
                      })}
                      type="email"
                      className="form-input"
                      placeholder="contact@company.com"
                    />
                    {errors.contact_email && (
                      <p className="mt-1 text-sm text-red-600">{errors.contact_email.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="form-label">Contact Phone *</label>
                    <input
                      {...register('contact_phone', { required: 'Contact phone is required' })}
                      type="tel"
                      className="form-input"
                      placeholder="+1 (555) 123-4567"
                    />
                    {errors.contact_phone && (
                      <p className="mt-1 text-sm text-red-600">{errors.contact_phone.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="form-label">Company Address *</label>
                    <textarea
                      {...register('company_address', { required: 'Company address is required' })}
                      rows={3}
                      className="form-input"
                      placeholder="Enter company address"
                    />
                    {errors.company_address && (
                      <p className="mt-1 text-sm text-red-600">{errors.company_address.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="form-label">Billing Email</label>
                    <input
                      {...register('billing_email', {
                        pattern: {
                          value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                          message: 'Invalid email address'
                        }
                      })}
                      type="email"
                      className="form-input"
                      placeholder="billing@company.com (will auto-fill with contact email)"
                    />
                    {errors.billing_email && (
                      <p className="mt-1 text-sm text-red-600">{errors.billing_email.message}</p>
                    )}
                    <p className="mt-1 text-xs text-gray-500">Leave empty to automatically use contact email</p>
                  </div>
                </div>
              </div>

              {/* Subscription Dates */}
              <div className="mt-6">
                <h4 className="text-md font-medium text-gray-900 mb-2">Subscription Timeline</h4>
                <p className="text-xs text-gray-500 mb-4">
                  Subscription end date must be after subscription start date.
                </p>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                  
                  {mode === 'create' && (
                    <div>
                      <label className="form-label">
                        <CalendarIcon className="h-4 w-4 inline mr-1" />
                        Trial End Date (Auto)
                      </label>
                      <input
                        type="datetime-local"
                        value={displayTrialEndDate}
                        disabled 
                        className="form-input bg-gray-100 cursor-not-allowed"
                      />
                    </div>
                  )}

                  {mode === 'edit' && tenant?.trial_end_date && (
                    <div>
                      <label className="form-label">
                        <CalendarIcon className="h-4 w-4 inline mr-1" />
                        Trial End Date (One Monthly Free)
                      </label>
                      <input
                        {...register('trial_end_date')}
                        type="datetime-local"
                        disabled 
                        className="form-input bg-gray-100 cursor-not-allowed"
                      />
                    </div>
                  )}

                  <div>
                    <label className="form-label">
                      <CalendarIcon className="h-4 w-4 inline mr-1" />
                      Subscription Start
                    </label>
                    <input
                      {...register('subscription_start_date')}
                      type="datetime-local"
                      className="form-input"
                    />
                    {errors.subscription_start_date && (
                      <p className="mt-1 text-sm text-red-600">{errors.subscription_start_date.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="form-label">
                      <CalendarIcon className="h-4 w-4 inline mr-1" />
                      Subscription End
                    </label>
                    <input
                      {...register('subscription_end_date')}
                      type="datetime-local"
                      min={subscriptionStartDate || getCurrentDateTime()}
                      className="form-input"
                    />
                    {errors.subscription_end_date && (
                      <p className="mt-1 text-sm text-red-600">{errors.subscription_end_date.message}</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 px-6 py-4 sm:flex sm:flex-row-reverse border-t border-gray-200">
              <button
                type="submit"
                disabled={isSubmitting}
                className="btn-primary sm:ml-3 sm:w-auto w-full"
              >
                {isSubmitting ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mx-auto"></div>
                ) : (
                  mode === 'create' ? 'Create Tenant' : 'Update Tenant'
                )}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="btn-secondary mt-3 sm:mt-0 sm:w-auto w-full"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
