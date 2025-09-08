import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { batchesAPI, emailsAPI, tenantsAPI, authAPI, recipientsAPI, contactGroupsAPI } from '../../utils/api';
import { istToDatetimeLocal, getCurrentISTString, isInPastIST } from '../../utils/timezone';
import { TimezoneNote } from '../common/TimezoneIndicator';
import { XMarkIcon, CalendarIcon, EnvelopeIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../../context/AuthContext';
import toast from 'react-hot-toast';

export default function BatchModal({ batch, mode, onClose, onSuccess }) {
  const { user } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [groups, setGroups] = useState([]);
  const [recipients, setRecipients] = useState([]);
  const [contactGroups, setContactGroups] = useState([]);
  const [emailConfigurations, setEmailConfigurations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [recipientSelectionMode, setRecipientSelectionMode] = useState('legacy'); // 'legacy', 'new_recipients', 'new_groups'

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm();

  const selectedGroups = watch('group_ids', []);
  const selectedRecipients = watch('recipient_ids', []);
  const selectedContactGroups = watch('contact_group_ids', []);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (batch && mode === 'edit') {
      setValue('name', batch.name);
      setValue('description', batch.description);
      setValue('template', batch.template);
      setValue('email_configuration', batch.email_configuration);
      setValue('start_time', istToDatetimeLocal(batch.start_time));
      if (batch.end_time) {
        setValue('end_time', istToDatetimeLocal(batch.end_time));
      }
      setValue('interval_type', batch.interval_display || 'none');
      setValue('email_support_fields', JSON.stringify(batch.email_support_fields || {}, null, 2));
      setValue('group_ids', batch.batch_groups?.map(bg => bg.group) || []);
      setValue('recipient_ids', batch.batch_recipients?.map(br => br.recipient) || []);
      setValue('contact_group_ids', batch.contact_group_ids || []);
      
      // Sub-cycle fields
      setValue('sub_cycle_enabled', batch.sub_cycle_enabled || false);
      setValue('sub_cycle_interval_type', batch.sub_cycle_interval_type || 'daily');
      setValue('sub_cycle_custom_minutes', batch.sub_cycle_interval_minutes || 1440);
      setValue('auto_complete_on_all_received', batch.auto_complete_on_all_received !== false);
      
      // Determine which selection mode to use based on existing data
      if (batch.batch_recipients?.length > 0) {
        setRecipientSelectionMode('new_recipients');
      } else if (batch.contact_group_ids?.length > 0) {
        setRecipientSelectionMode('new_groups');
      } else {
        setRecipientSelectionMode('legacy');
      }
    }
  }, [batch, mode, setValue]);

  const fetchData = async () => {
    try {
      // Use different email configurations API based on user role
      const emailConfigsPromise = (user?.role === 'staff_admin' || user?.role === 'staff') 
        ? authAPI.getTenantEmailConfigurations()
        : authAPI.getEmailConfigurations();

      const [templatesResponse, groupsResponse, recipientsResponse, contactGroupsResponse, emailConfigsResponse] = await Promise.all([
        emailsAPI.getTemplates(),
        tenantsAPI.getGroups(),
        recipientsAPI.list(),
        contactGroupsAPI.list(),
        emailConfigsPromise
      ]);
      
      setTemplates(templatesResponse.data.results || templatesResponse.data || []);
      setGroups(groupsResponse.data.results || groupsResponse.data || []);
      setRecipients(recipientsResponse.data.results || recipientsResponse.data || []);
      setContactGroups(contactGroupsResponse.data.results || contactGroupsResponse.data || []);
      setEmailConfigurations(Array.isArray(emailConfigsResponse.data) ? emailConfigsResponse.data : (emailConfigsResponse.data?.results || []));
      
      // Set default email configuration if creating new batch
      if (mode === 'create') {
        const emailConfigsArray = Array.isArray(emailConfigsResponse.data) ? emailConfigsResponse.data : (emailConfigsResponse.data?.results || []);
        const defaultConfig = emailConfigsArray.find(config => config.is_default && config.is_active);
        if (defaultConfig) {
          setValue('email_configuration', defaultConfig.id);
        }
      }
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    try {
      // Validate recipient selection
      const groupsArray = Array.isArray(selectedGroups) ? selectedGroups : [];
      const recipientsArray = Array.isArray(selectedRecipients) ? selectedRecipients : [];
      const contactGroupsArray = Array.isArray(selectedContactGroups) ? selectedContactGroups : [];
      
      if (recipientSelectionMode === 'legacy' && groupsArray.length === 0) {
        toast.error('Please select at least one group');
        setIsSubmitting(false);
        return;
      }
      
      if (recipientSelectionMode === 'new_recipients' && recipientsArray.length === 0) {
        toast.error('Please select at least one recipient');
        setIsSubmitting(false);
        return;
      }
      
      if (recipientSelectionMode === 'new_groups' && contactGroupsArray.length === 0) {
        toast.error('Please select at least one contact group');
        setIsSubmitting(false);
        return;
      }
      
      // Parse email support fields
      let emailSupportFields = {};
      if (data.email_support_fields) {
        try {
          emailSupportFields = JSON.parse(data.email_support_fields);
        } catch (e) {
          toast.error('Invalid JSON in email support fields');
          setIsSubmitting(false);
          return;
        }
      }

      const batchData = {
        ...data,
        email_support_fields: emailSupportFields,
        group_ids: groupsArray.map(id => parseInt(id)),
        recipient_ids: recipientsArray.map(id => parseInt(id)),
        contact_group_ids: contactGroupsArray.map(id => parseInt(id)),
        // Sub-cycle fields
        sub_cycle_enabled: data.sub_cycle_enabled || false,
        sub_cycle_interval_type: data.sub_cycle_interval_type || 'daily',
        sub_cycle_custom_minutes: data.sub_cycle_custom_minutes || null,
        auto_complete_on_all_received: data.auto_complete_on_all_received !== false
      };

      if (mode === 'create') {
        await batchesAPI.createBatch(batchData);
        toast.success('Batch created successfully');
      } else {
        // Check if this is an edit with document submissions
        const hasReceivedDocs = batch.documents_received_count > 0;
        const isTimeChanged = batch.start_time !== data.start_time;
        
        if (hasReceivedDocs && isTimeChanged) {
          // Show confirmation dialog for document reset
          const shouldResetDocs = window.confirm(
            `⚠️ IMPORTANT: This batch has ${batch.documents_received_count} recipients who have already submitted documents.\n\n` +
            `What would you like to do?\n\n` +
            `• Click "OK" to RESET all document statuses and send emails to ALL recipients\n` +
            `• Click "Cancel" to KEEP existing document statuses and only send emails to recipients who haven't submitted documents`
          );
          
          if (shouldResetDocs) {
            // Reset documents first
            try {
              await batchesAPI.resetDocuments(batch.id, { reset_documents: true });
              toast.success('Document statuses reset for all recipients');
            } catch (error) {
              console.error('Error resetting documents:', error);
              toast.error('Failed to reset document statuses');
            }
          }
        }
        
        await batchesAPI.updateBatch(batch.id, batchData);
        toast.success('Batch updated successfully');
      }
      onSuccess();
    } catch (error) {
      console.error('Batch creation error:', error.response?.data);
      let errorMsg = `Failed to ${mode} batch`;
      
      if (error.response?.data) {
        const data = error.response.data;
        if (data.detail) {
          errorMsg = data.detail;
        } else if (data.non_field_errors) {
          errorMsg = data.non_field_errors.join(', ');
        } else if (typeof data === 'object') {
          // Handle field-specific errors
          const fieldErrors = Object.entries(data)
            .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(', ') : errors}`)
            .join('; ');
          if (fieldErrors) {
            errorMsg = fieldErrors;
          }
        }
      }
      
      toast.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 overflow-y-auto">
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-recalliq-600"></div>
        </div>
      </div>
    );
  }

  const totalRecipients = (() => {
    let total = 0;
    
    // Ensure values are arrays
    const groupsArray = Array.isArray(selectedGroups) ? selectedGroups : [];
    const recipientsArray = Array.isArray(selectedRecipients) ? selectedRecipients : [];
    const contactGroupsArray = Array.isArray(selectedContactGroups) ? selectedContactGroups : [];
    
    // Legacy groups
    if (recipientSelectionMode === 'legacy') {
      total += groupsArray.reduce((sum, groupId) => {
        const group = (groups || []).find(g => g.id === parseInt(groupId));
        return sum + (group?.email_count || 0);
      }, 0);
    }
    
    // New recipient system - individual recipients
    if (recipientSelectionMode === 'new_recipients') {
      total += recipientsArray.length;
    }
    
    // New recipient system - contact groups
    if (recipientSelectionMode === 'new_groups') {
      total += contactGroupsArray.reduce((sum, groupId) => {
        const group = (contactGroups || []).find(g => g.id === parseInt(groupId));
        return sum + (group?.recipient_count || 0);
      }, 0);
    }
    
    return total;
  })();

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />

        <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="card-header">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  {mode === 'create' ? 'Create' : 'Edit'} Email Batch
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
                <div className="space-y-4">
                  <div>
                    <label className="form-label">Batch Name</label>
                    <input
                      {...register('name', { required: 'Batch name is required' })}
                      type="text"
                      className="form-input"
                      placeholder="Enter batch name"
                    />
                    {errors.name && (
                      <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="form-label">Description</label>
                    <textarea
                      {...register('description')}
                      rows={3}
                      className="form-input"
                      placeholder="Enter batch description (optional)"
                    />
                  </div>

                  <div>
                    <label className="form-label">
                      <EnvelopeIcon className="h-4 w-4 inline mr-1" />
                      Email Configuration
                    </label>
                    <select
                      {...register('email_configuration', { required: 'Please select an email configuration' })}
                      className="form-input"
                    >
                      <option value="">Select email configuration</option>
                      {(emailConfigurations || []).filter(config => config.is_active).map((config) => (
                        <option key={config.id} value={config.id}>
                          {config.name} ({config.from_email})
                          {config.is_default ? ' - Default' : ''}
                        </option>
                      ))}
                    </select>
                    {errors.email_configuration && (
                      <p className="mt-1 text-sm text-red-600">{errors.email_configuration.message}</p>
                    )}
                    {(emailConfigurations || []).length === 0 && (
                      <p className="mt-1 text-sm text-yellow-600">
                        {(user?.role === 'staff_admin' || user?.role === 'staff') 
                          ? 'No email configurations available. Please ask your tenant admin to set up email configurations.'
                          : 'No email configurations available. Please create one in your profile settings.'
                        }
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="form-label">Email Template</label>
                    <select
                      {...register('template', { required: 'Please select a template' })}
                      className="form-input"
                    >
                      <option value="">Select a template</option>
                      {templates.map((template) => (
                        <option key={template.id} value={template.id}>
                          {template.name}
                        </option>
                      ))}
                    </select>
                    {errors.template && (
                      <p className="mt-1 text-sm text-red-600">{errors.template.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="form-label">Recipients Selection</label>
                    
                    {/* Selection Mode Toggle */}
                    <div className="mb-4">
                      <div className="flex space-x-4">
                        <label className="flex items-center">
                          <input
                            type="radio"
                            name="recipient_mode"
                            value="legacy"
                            checked={recipientSelectionMode === 'legacy'}
                            onChange={(e) => setRecipientSelectionMode(e.target.value)}
                            className="form-radio text-recalliq-600"
                          />
                          <span className="ml-2 text-sm text-gray-700">Legacy Groups</span>
                        </label>
                        <label className="flex items-center">
                          <input
                            type="radio"
                            name="recipient_mode"
                            value="new_recipients"
                            checked={recipientSelectionMode === 'new_recipients'}
                            onChange={(e) => setRecipientSelectionMode(e.target.value)}
                            className="form-radio text-recalliq-600"
                          />
                          <span className="ml-2 text-sm text-gray-700">Individual Recipients</span>
                        </label>
                        <label className="flex items-center">
                          <input
                            type="radio"
                            name="recipient_mode"
                            value="new_groups"
                            checked={recipientSelectionMode === 'new_groups'}
                            onChange={(e) => setRecipientSelectionMode(e.target.value)}
                            className="form-radio text-recalliq-600"
                          />
                          <span className="ml-2 text-sm text-gray-700">Contact Groups</span>
                        </label>
                      </div>
                    </div>

                    {/* Legacy Groups Selection */}
                    {recipientSelectionMode === 'legacy' && (
                      <div className="space-y-2 max-h-32 overflow-y-auto border border-gray-300 rounded-lg p-3">
                        {groups.map((group) => (
                          <label key={group.id} className="flex items-center">
                            <input
                              type="checkbox"
                              value={group.id}
                              checked={Array.isArray(selectedGroups) && selectedGroups.includes(group.id.toString())}
                              onChange={(e) => {
                                const currentGroups = Array.isArray(selectedGroups) ? selectedGroups : [];
                                const groupId = e.target.value;
                                let newGroups;
                                
                                if (e.target.checked) {
                                  newGroups = [...currentGroups, groupId];
                                } else {
                                  newGroups = currentGroups.filter(id => id !== groupId);
                                }
                                
                                setValue('group_ids', newGroups);
                              }}
                              className="rounded border-gray-300 text-recalliq-600 focus:ring-recalliq-500"
                            />
                            <span className="ml-2 text-sm text-gray-700">
                              {group.name} ({group.email_count} contacts)
                            </span>
                          </label>
                        ))}
                        {groups.length === 0 && (
                          <p className="text-sm text-gray-500">No legacy groups available</p>
                        )}
                      </div>
                    )}

                    {/* Individual Recipients Selection */}
                    {recipientSelectionMode === 'new_recipients' && (
                      <div className="space-y-2 max-h-32 overflow-y-auto border border-gray-300 rounded-lg p-3">
                        {recipients.map((recipient) => (
                          <label key={recipient.id} className="flex items-center">
                            <input
                              type="checkbox"
                              value={recipient.id}
                              checked={Array.isArray(selectedRecipients) && selectedRecipients.includes(recipient.id.toString())}
                              onChange={(e) => {
                                const currentRecipients = Array.isArray(selectedRecipients) ? selectedRecipients : [];
                                const recipientId = e.target.value;
                                let newRecipients;
                                
                                if (e.target.checked) {
                                  newRecipients = [...currentRecipients, recipientId];
                                } else {
                                  newRecipients = currentRecipients.filter(id => id !== recipientId);
                                }
                                
                                setValue('recipient_ids', newRecipients);
                              }}
                              className="rounded border-gray-300 text-recalliq-600 focus:ring-recalliq-500"
                            />
                            <span className="ml-2 text-sm text-gray-700">
                              {recipient.name} ({recipient.email}) - {recipient.organization_name}
                            </span>
                          </label>
                        ))}
                        {recipients.length === 0 && (
                          <p className="text-sm text-gray-500">No recipients available. Please create some recipients first.</p>
                        )}
                      </div>
                    )}

                    {/* Contact Groups Selection */}
                    {recipientSelectionMode === 'new_groups' && (
                      <div className="space-y-2 max-h-32 overflow-y-auto border border-gray-300 rounded-lg p-3">
                        {contactGroups.map((group) => (
                          <label key={group.id} className="flex items-center">
                            <input
                              type="checkbox"
                              value={group.id}
                              checked={Array.isArray(selectedContactGroups) && selectedContactGroups.includes(group.id.toString())}
                              onChange={(e) => {
                                const currentGroups = Array.isArray(selectedContactGroups) ? selectedContactGroups : [];
                                const groupId = e.target.value;
                                let newGroups;
                                
                                if (e.target.checked) {
                                  newGroups = [...currentGroups, groupId];
                                } else {
                                  newGroups = currentGroups.filter(id => id !== groupId);
                                }
                                
                                setValue('contact_group_ids', newGroups);
                              }}
                              className="rounded border-gray-300 text-recalliq-600 focus:ring-recalliq-500"
                            />
                            <span className="ml-2 text-sm text-gray-700">
                              {group.name} ({group.recipient_count || 0} recipients)
                            </span>
                          </label>
                        ))}
                        {contactGroups.length === 0 && (
                          <p className="text-sm text-gray-500">No contact groups available. Please create some contact groups first.</p>
                        )}
                      </div>
                    )}

                    {/* Validation Errors */}
                    {recipientSelectionMode === 'legacy' && errors.group_ids && (
                      <p className="mt-1 text-sm text-red-600">{errors.group_ids.message}</p>
                    )}
                    {recipientSelectionMode === 'new_recipients' && errors.recipient_ids && (
                      <p className="mt-1 text-sm text-red-600">{errors.recipient_ids.message}</p>
                    )}
                    {recipientSelectionMode === 'new_groups' && errors.contact_group_ids && (
                      <p className="mt-1 text-sm text-red-600">{errors.contact_group_ids.message}</p>
                    )}

                    {/* Total Recipients Display */}
                    {totalRecipients > 0 && (
                      <p className="mt-1 text-sm text-recalliq-600">
                        Total recipients: {totalRecipients}
                      </p>
                    )}
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="form-label">
                      <CalendarIcon className="h-4 w-4 inline mr-1" />
                      Start Time
                    </label>
                    <input
                      {...register('start_time', { required: 'Start time is required' })}
                      type="datetime-local"
                      className="form-input"
                      min={istToDatetimeLocal(getCurrentISTString())}
                    />
                    <TimezoneNote className="mt-1" />
                    {errors.start_time && (
                      <p className="mt-1 text-sm text-red-600">{errors.start_time.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="form-label">End Time (Optional)</label>
                    <input
                      {...register('end_time')}
                      type="datetime-local"
                      className="form-input"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Leave empty for one-time batch or set for recurring batches (IST)
                    </p>
                  </div>

                  <div>
                    <label className="form-label">Repeat Frequency</label>
                    <select
                      {...register('interval_type')}
                      className="form-input"
                    >
                      <option value="none">No Repeat (One-time)</option>
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                      <option value="yearly">Yearly</option>
                    </select>
                    <p className="mt-1 text-xs text-gray-500">
                      Choose how often this batch should repeat
                    </p>
                    {errors.interval_type && (
                      <p className="mt-1 text-sm text-red-600">{errors.interval_type.message}</p>
                    )}
                  </div>

                  {/* Sub-cycle Email Settings */}
                  <div className="space-y-4 p-4 border border-blue-200 rounded-lg bg-blue-50">
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        {...register('sub_cycle_enabled')}
                        className="rounded border-gray-300 text-recalliq-600 focus:ring-recalliq-500"
                      />
                      <label className="ml-2 text-sm font-medium text-gray-700">
                        Enable Reminder Emails
                      </label>
                    </div>
                    <p className="text-xs text-gray-600">
                      Send repeated emails until documents are received from each recipient for given start time and end time.
                    </p>

                    {watch('sub_cycle_enabled') && (
                      <div className="space-y-3 pl-6 border-l-2 border-blue-300">
                        <div>
                          <label className="form-label">Reminder Frequency</label>
                          <select
                            {...register('sub_cycle_interval_type')}
                            className="form-input"
                          >
                            <option value="daily">Daily</option>
                            <option value="weekly">Weekly</option>
                            <option value="monthly">Monthly</option>
                            <option value="custom">Custom</option>
                          </select>
                        </div>

                        {watch('sub_cycle_interval_type') === 'custom' && (
                          <div>
                            <label className="form-label">Custom Interval (minutes)</label>
                            <input
                              type="number"
                              {...register('sub_cycle_custom_minutes', { min: 60 })}
                              className="form-input"
                              placeholder="1440 (24 hours)"
                              min="60"
                            />
                            <p className="mt-1 text-xs text-gray-500">
                              Minimum 60 minutes between reminders
                            </p>
                          </div>
                        )}

                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            {...register('auto_complete_on_all_received')}
                            defaultChecked={true}
                            className="rounded border-gray-300 text-recalliq-600 focus:ring-recalliq-500"
                          />
                          <label className="ml-2 text-sm text-gray-700">
                            Auto-complete when all documents received
                          </label>
                        </div>
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="form-label">Custom Fields (JSON)</label>
                    <textarea
                      {...register('email_support_fields')}
                      rows={4}
                      className="form-input font-mono text-sm"
                      placeholder='{"company": "RecallIQ", "year": "2024"}'
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      JSON object for template variables. Use {"{"}"key": "value"{"}"} format.
                    </p>
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
                  mode === 'create' ? 'Create Batch' : 'Update Batch'
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