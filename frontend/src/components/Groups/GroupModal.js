import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { tenantsAPI } from '../../utils/api';
import { XMarkIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

export default function GroupModal({ group, mode, onClose, onSuccess }) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    watch,
  } = useForm();

  useEffect(() => {
    if (group && mode === 'edit') {
      setValue('name', group.name);
      setValue('description', group.description);
      setValue('is_active', group.is_active);
    }
  }, [group, mode, setValue]);

  const onSubmit = async (data) => {
    setIsSubmitting(true);
    try {
      if (mode === 'create') {
        await tenantsAPI.createGroup(data);
        toast.success('Group created successfully');
      } else {
        await tenantsAPI.updateGroup(group.id, data);
        toast.success('Group updated successfully');
      }
      onSuccess();
    } catch (error) {
      let errorMsg = `Failed to ${mode} group`;
      if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail;
      } else if (error.response?.data?.error) {
        errorMsg = error.response.data.error;
      } else if (error.response?.data) {
        const fieldErrors = [];
        Object.keys(error.response.data).forEach(field => {
          if (Array.isArray(error.response.data[field])) {
            fieldErrors.push(`${field}: ${error.response.data[field][0]}`);
          } else if (typeof error.response.data[field] === 'string') {
            fieldErrors.push(`${field}: ${error.response.data[field]}`);
          }
        });
        if (fieldErrors.length > 0) {
          errorMsg = fieldErrors.join(', ');
        }
      }
      toast.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />

        <div className="inline-block align-bottom bg-white rounded-xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="card-header">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">
                  {mode === 'create' ? 'Create' : 'Edit'} Contact Group
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

            <div className="px-6 py-4">
              <div className="space-y-4">
                <div>
                  <label className="form-label">Group Name</label>
                  <input
                    {...register('name', { required: 'Group name is required' })}
                    type="text"
                    className="form-input"
                    placeholder="Enter group name"
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
                    placeholder="Enter group description (optional)"
                  />
                  {errors.description && (
                    <p className="mt-1 text-sm text-red-600">{errors.description.message}</p>
                  )}
                </div>

                <div className="flex items-center">
                  <input
                    {...register('is_active')}
                    type="checkbox"
                    defaultChecked={true}
                    className="rounded border-gray-300 text-recalliq-600 focus:ring-recalliq-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">Active</span>
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
                  mode === 'create' ? 'Create Group' : 'Update Group'
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