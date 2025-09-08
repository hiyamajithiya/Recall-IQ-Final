import React from 'react';
import { getTimezoneInfo, formatDateIST } from '../../utils/timezone';
import { ClockIcon } from '@heroicons/react/24/outline';

export default function TimezoneIndicator({ className = '' }) {
  const timezoneInfo = getTimezoneInfo();
  
  return (
    <div className={`flex items-center text-xs text-gray-500 ${className}`}>
      <ClockIcon className="h-3 w-3 mr-1" />
      <span>
        IST ({timezoneInfo.offset}) • {formatDateIST(new Date(), 'time')}
      </span>
    </div>
  );
}

export function TimezoneNote({ className = '' }) {
  return (
    <p className={`text-xs text-gray-500 ${className}`}>
      <ClockIcon className="h-3 w-3 inline mr-1" />
      All times are displayed in IST (Indian Standard Time)
    </p>
  );
}