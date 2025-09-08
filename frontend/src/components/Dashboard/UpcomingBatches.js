import React from 'react';
import { CalendarIcon, UsersIcon } from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';

export default function UpcomingBatches({ batches = [] }) {
  if (!batches.length) {
    return (
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Upcoming Batches</h3>
        <div className="text-center py-8">
          <CalendarIcon className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2 text-gray-500">No upcoming batches scheduled</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Upcoming Batches</h3>
      <div className="space-y-4">
        {batches.map((batch) => (
          <div key={batch.id} className="flex items-center space-x-4 p-3 bg-gray-50 rounded-lg">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                <CalendarIcon className="w-5 h-5 text-primary-600" />
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {batch.name}
              </p>
              <p className="text-sm text-gray-500 truncate">
                Template: {batch.template_name}
              </p>
              <div className="flex items-center mt-1">
                <UsersIcon className="w-4 h-4 text-gray-400 mr-1" />
                <span className="text-xs text-gray-500">
                  {batch.total_recipients} recipients
                </span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-500">
                {formatDistanceToNow(new Date(batch.start_time), { addSuffix: true })}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}