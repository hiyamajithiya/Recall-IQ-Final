import React from 'react';
import { formatDistanceToNow } from 'date-fns';

const getStatusBadge = (status) => {
  const statusClasses = {
    sent: 'badge badge-green',
    failed: 'badge badge-red',
    queued: 'badge badge-yellow',
    delivered: 'badge badge-blue',
  };

  return statusClasses[status] || 'badge badge-gray';
};

const getDirectionBadge = (direction) => {
  const directionClasses = {
    outgoing: 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800',  // Green for "Sent"
    incoming: 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800',   // Blue for "Received"
  };
  const directionLabels = {
    outgoing: 'sent',
    incoming: 'received',
  };
  return {
    className: directionClasses[direction] || 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800',
    label: directionLabels[direction] || direction
  };
};

export default function RecentActivity({ activities = [] }) {
  if (!activities.length) {
    return (
      <div className="card p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Email Activity</h3>
        <div className="text-center py-8">
          <p className="text-gray-500">No recent activity</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Email Activity</h3>
      <div className="flow-root">
        <ul className="-mb-8">
          {activities.map((activity, index) => (
            <li key={activity.id}>
              <div className="relative pb-8">
                {index !== activities.length - 1 && (
                  <span
                    className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                    aria-hidden="true"
                  />
                )}
                <div className="relative flex space-x-3">
                  <div>
                    <span className="h-8 w-8 rounded-full bg-primary-500 flex items-center justify-center ring-8 ring-white">
                      <span className="text-white text-xs font-bold">
                        {activity.email_type.charAt(0).toUpperCase()}
                      </span>
                    </span>
                  </div>
                  <div className="min-w-0 flex-1 pt-1.5">
                    <div className="flex justify-between items-start space-x-4">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-900 truncate">
                          Email to <span className="font-medium">{activity.to_email}</span>
                        </p>
                        <p className="text-sm text-gray-500 truncate">
                          {activity.subject}
                        </p>
                      </div>
                      <div className="text-right text-sm text-gray-500 flex flex-col items-end space-y-1 flex-shrink-0">
                        <div>
                          {activity.direction ? (
                            <span className={getDirectionBadge(activity.direction).className}>
                              {getDirectionBadge(activity.direction).label}
                            </span>
                          ) : (
                            <span className={getStatusBadge(activity.status)}>
                              {activity.status}
                            </span>
                          )}
                        </div>
                        <time dateTime={activity.created_at} className="text-xs">
                          {formatDistanceToNow(new Date(activity.created_at), { addSuffix: true })}
                        </time>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}