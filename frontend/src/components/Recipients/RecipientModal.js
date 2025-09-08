import React, { useState, useEffect } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { Fragment } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import api from '../../utils/api';

export default function RecipientModal({ recipient, groups, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    organization_name: '',
    title: '',
    phone_number: '',
    notes: '',
    group_ids: [],
    is_active: true
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (recipient) {
      setFormData({
        name: recipient.name || '',
        email: recipient.email || '',
        organization_name: recipient.organization_name || '',
        title: recipient.title || '',
        phone_number: recipient.phone_number || '',
        notes: recipient.notes || '',
        group_ids: recipient.groups?.map(g => g.id) || [],
        is_active: recipient.is_active ?? true
      });
    }
  }, [recipient]);

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }

    if (!formData.organization_name.trim()) {
      newErrors.organization_name = 'Organization name is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);
      
      const data = {
        ...formData,
        name: formData.name.trim(),
        email: formData.email.trim().toLowerCase(),
        organization_name: formData.organization_name.trim(),
        title: formData.title.trim() || null,
        phone_number: formData.phone_number.trim() || null,
        notes: formData.notes.trim() || null,
      };

      if (recipient) {
        await api.recipients.update(recipient.id, data);
        toast.success('Recipient updated successfully');
      } else {
        await api.recipients.create(data);
        toast.success('Recipient created successfully');
      }

      onSuccess();
    } catch (error) {
      console.error('Error saving recipient:', error);
      
      if (error.response?.data) {
        const errorData = error.response.data;
        
        if (errorData.email && errorData.email[0]?.includes('already exists')) {
          setErrors({ email: 'A recipient with this email already exists in your organization' });
        } else if (typeof errorData === 'object') {
          setErrors(errorData);
        } else {
          toast.error('Failed to save recipient');
        }
      } else {
        toast.error('Failed to save recipient');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: null
      }));
    }
  };

  const handleGroupChange = (groupId) => {
    setFormData(prev => ({
      ...prev,
      group_ids: prev.group_ids.includes(groupId)
        ? prev.group_ids.filter(id => id !== groupId)
        : [...prev.group_ids, groupId]
    }));
  };

  return (
    <Transition appear show={true} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <div className="flex items-center justify-between mb-6">
                  <Dialog.Title as="h3" className="text-lg font-medium leading-6 text-gray-900">
                    {recipient ? 'Edit Recipient' : 'Add New Recipient'}
                  </Dialog.Title>
                  <button
                    type="button"
                    className="text-gray-400 hover:text-gray-600"
                    onClick={onClose}
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Name */}
                    <div>
                      <label htmlFor="name" className="form-label">
                        Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        id="name"
                        name="name"
                        className={`form-input ${errors.name ? 'border-red-500' : ''}`}
                        value={formData.name}
                        onChange={handleChange}
                        placeholder="Enter full name"
                      />
                      {errors.name && (
                        <p className="mt-1 text-sm text-red-600">{errors.name}</p>
                      )}
                    </div>

                    {/* Email */}
                    <div>
                      <label htmlFor="email" className="form-label">
                        Email <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="email"
                        id="email"
                        name="email"
                        className={`form-input ${errors.email ? 'border-red-500' : ''}`}
                        value={formData.email}
                        onChange={handleChange}
                        placeholder="Enter email address"
                      />
                      {errors.email && (
                        <p className="mt-1 text-sm text-red-600">{errors.email}</p>
                      )}
                    </div>

                    {/* Organization Name */}
                    <div>
                      <label htmlFor="organization_name" className="form-label">
                        Organization <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        id="organization_name"
                        name="organization_name"
                        className={`form-input ${errors.organization_name ? 'border-red-500' : ''}`}
                        value={formData.organization_name}
                        onChange={handleChange}
                        placeholder="Enter organization name"
                      />
                      {errors.organization_name && (
                        <p className="mt-1 text-sm text-red-600">{errors.organization_name}</p>
                      )}
                    </div>

                    {/* Title */}
                    <div>
                      <label htmlFor="title" className="form-label">
                        Title
                      </label>
                      <input
                        type="text"
                        id="title"
                        name="title"
                        className="form-input"
                        value={formData.title}
                        onChange={handleChange}
                        placeholder="Enter job title"
                      />
                    </div>

                    {/* Phone Number */}
                    <div>
                      <label htmlFor="phone_number" className="form-label">
                        Phone Number
                      </label>
                      <input
                        type="tel"
                        id="phone_number"
                        name="phone_number"
                        className="form-input"
                        value={formData.phone_number}
                        onChange={handleChange}
                        placeholder="Enter phone number"
                      />
                    </div>

                    {/* Active Status */}
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="is_active"
                        name="is_active"
                        className="form-checkbox"
                        checked={formData.is_active}
                        onChange={handleChange}
                      />
                      <label htmlFor="is_active" className="ml-2 text-sm text-gray-700">
                        Active recipient
                      </label>
                    </div>
                  </div>

                  {/* Notes */}
                  <div>
                    <label htmlFor="notes" className="form-label">
                      Notes
                    </label>
                    <textarea
                      id="notes"
                      name="notes"
                      rows={3}
                      className="form-input"
                      value={formData.notes}
                      onChange={handleChange}
                      placeholder="Enter additional notes"
                    />
                  </div>

                  {/* Groups */}
                  {groups.length > 0 && (
                    <div>
                      <label className="form-label">Contact Groups</label>
                      <div className="mt-2 grid grid-cols-2 md:grid-cols-3 gap-2">
                        {groups.map((group) => (
                          <label key={group.id} className="flex items-center">
                            <input
                              type="checkbox"
                              className="form-checkbox"
                              checked={formData.group_ids.includes(group.id)}
                              onChange={() => handleGroupChange(group.id)}
                            />
                            <span className="ml-2 text-sm text-gray-700">
                              {group.name}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Form Actions */}
                  <div className="flex justify-end space-x-3 pt-6 border-t">
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={onClose}
                      disabled={loading}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="btn-primary"
                      disabled={loading}
                    >
                      {loading ? 'Saving...' : (recipient ? 'Update Recipient' : 'Create Recipient')}
                    </button>
                  </div>
                </form>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}