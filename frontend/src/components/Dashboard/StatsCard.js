import React from 'react';

export default function StatsCard({ title, value, change, changeType, icon: Icon }) {
  const getChangeColor = () => {
    if (changeType === 'increase') return 'text-green-600';
    if (changeType === 'decrease') return 'text-red-600';
    return 'text-gray-600';
  };

  const getChangeIcon = () => {
    if (changeType === 'increase') return '↗';
    if (changeType === 'decrease') return '↘';
    return '→';
  };

  return (
    <div className="stats-card">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-gradient-to-br from-primary-100 to-primary-200 rounded-xl flex items-center justify-center">
            <Icon className="h-7 w-7 text-primary-600" />
          </div>
        </div>
        <div className="ml-5 w-0 flex-1">
          <dl>
            <dt className="text-sm font-bold text-gray-600 uppercase tracking-wide break-words leading-tight">{title}</dt>
            <dd className="flex items-baseline">
              <div className="text-3xl font-bold bg-gradient-to-r from-primary-600 to-primary-700 bg-clip-text text-transparent">{value}</div>
              {change && (
                <div className={`ml-2 flex items-baseline text-sm font-bold ${getChangeColor()}`}>
                  <span className="sr-only">
                    {changeType === 'increase' ? 'Increased' : changeType === 'decrease' ? 'Decreased' : 'No change'}
                  </span>
                  {getChangeIcon()} {change}
                </div>
              )}
            </dd>
          </dl>
        </div>
      </div>
    </div>
  );
}