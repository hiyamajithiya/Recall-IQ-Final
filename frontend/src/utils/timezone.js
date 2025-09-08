/**
 * Timezone Utilities for IST (Indian Standard Time)
 * Handles all datetime conversions and formatting for the application
 */

const IST_TIMEZONE = 'Asia/Kolkata';

/**
 * Format date to IST with custom format
 * @param {string|Date} date - Date to format
 * @param {string} format - Format type: 'full', 'date', 'time', 'datetime', 'relative'
 * @returns {string} Formatted date string in IST
 */
export const formatDateIST = (date, format = 'datetime') => {
  if (!date) return '';
  
  const dateObj = new Date(date);
  
  // Check if date is valid
  if (isNaN(dateObj.getTime())) return '';
  
  const options = {
    timeZone: IST_TIMEZONE,
  };
  
  switch (format) {
    case 'full':
      return dateObj.toLocaleString('en-IN', {
        ...options,
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      });
      
    case 'date':
      return dateObj.toLocaleDateString('en-IN', {
        ...options,
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      });
      
    case 'time':
      return dateObj.toLocaleTimeString('en-IN', {
        ...options,
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      });
      
    case 'datetime':
      return dateObj.toLocaleString('en-IN', {
        ...options,
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      });
      
    case 'relative':
      return getRelativeTimeIST(dateObj);
      
    default:
      return dateObj.toLocaleString('en-IN', {
        ...options,
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
      });
  }
};

/**
 * Get relative time in IST (e.g., "2 hours ago", "in 3 days")
 * @param {Date} date - Date to compare
 * @returns {string} Relative time string
 */
export const getRelativeTimeIST = (date) => {
  if (!date) return '';
  
  const now = new Date();
  const diffMs = now.getTime() - new Date(date).getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (Math.abs(diffSeconds) < 60) {
    return 'Just now';
  } else if (Math.abs(diffMinutes) < 60) {
    const minutes = Math.abs(diffMinutes);
    if (diffMinutes < 0) {
      return `in ${minutes} minute${minutes > 1 ? 's' : ''}`;
    }
    return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
  } else if (Math.abs(diffHours) < 24) {
    const hours = Math.abs(diffHours);
    if (diffHours < 0) {
      return `in ${hours} hour${hours > 1 ? 's' : ''}`;
    }
    return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  } else if (Math.abs(diffDays) < 7) {
    const days = Math.abs(diffDays);
    if (diffDays < 0) {
      return `in ${days} day${days > 1 ? 's' : ''}`;
    }
    return `${days} day${days > 1 ? 's' : ''} ago`;
  } else {
    // For longer periods, show the actual date
    return formatDateIST(date, 'date');
  }
};

/**
 * Convert datetime-local input value to IST for display
 * @param {string} datetimeLocal - datetime-local input value
 * @returns {string} IST formatted datetime
 */
export const datetimeLocalToIST = (datetimeLocal) => {
  if (!datetimeLocal) return '';
  
  const date = new Date(datetimeLocal);
  return formatDateIST(date, 'datetime');
};

/**
 * Convert IST datetime to datetime-local input format
 * @param {string|Date} istDate - IST date
 * @returns {string} datetime-local format (YYYY-MM-DDTHH:MM)
 */
export const istToDatetimeLocal = (istDate) => {
  if (!istDate) return '';
  
  const date = new Date(istDate);
  
  // Convert to local timezone for datetime-local input
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  
  return `${year}-${month}-${day}T${hours}:${minutes}`;
};

/**
 * Get current IST datetime
 * @returns {Date} Current date in IST
 */
export const getCurrentIST = () => {
  return new Date();
};

/**
 * Get current IST datetime as ISO string
 * @returns {string} Current IST datetime as ISO string
 */
export const getCurrentISTString = () => {
  return getCurrentIST().toISOString();
};

/**
 * Check if a date is in the past (IST)
 * @param {string|Date} date - Date to check
 * @returns {boolean} True if date is in the past
 */
export const isInPastIST = (date) => {
  if (!date) return false;
  
  const now = getCurrentIST();
  const checkDate = new Date(date);
  
  return checkDate < now;
};

/**
 * Check if a date is in the future (IST)
 * @param {string|Date} date - Date to check
 * @returns {boolean} True if date is in the future
 */
export const isInFutureIST = (date) => {
  if (!date) return false;
  
  const now = getCurrentIST();
  const checkDate = new Date(date);
  
  return checkDate > now;
};

/**
 * Add time to a date in IST
 * @param {string|Date} date - Base date
 * @param {number} amount - Amount to add
 * @param {string} unit - Unit: 'minutes', 'hours', 'days', 'weeks'
 * @returns {Date} New date with added time
 */
export const addTimeIST = (date, amount, unit = 'minutes') => {
  if (!date) return null;
  
  const baseDate = new Date(date);
  const newDate = new Date(baseDate);
  
  switch (unit) {
    case 'minutes':
      newDate.setMinutes(newDate.getMinutes() + amount);
      break;
    case 'hours':
      newDate.setHours(newDate.getHours() + amount);
      break;
    case 'days':
      newDate.setDate(newDate.getDate() + amount);
      break;
    case 'weeks':
      newDate.setDate(newDate.getDate() + (amount * 7));
      break;
    default:
      throw new Error(`Unsupported time unit: ${unit}`);
  }
  
  return newDate;
};

/**
 * Get timezone info for IST
 * @returns {object} Timezone information
 */
export const getTimezoneInfo = () => {
  const now = new Date();
  const istTime = now.toLocaleString('en-IN', { timeZone: IST_TIMEZONE });
  const utcTime = now.toISOString();
  
  return {
    timezone: IST_TIMEZONE,
    name: 'Indian Standard Time',
    abbreviation: 'IST',
    offset: '+05:30',
    currentTime: istTime,
    utcTime: utcTime
  };
};

/**
 * Format duration in a human readable way
 * @param {number} minutes - Duration in minutes
 * @returns {string} Human readable duration
 */
export const formatDuration = (minutes) => {
  if (!minutes || minutes < 0) return '0 minutes';
  
  const days = Math.floor(minutes / (60 * 24));
  const hours = Math.floor((minutes % (60 * 24)) / 60);
  const mins = minutes % 60;
  
  const parts = [];
  
  if (days > 0) {
    parts.push(`${days} day${days > 1 ? 's' : ''}`);
  }
  if (hours > 0) {
    parts.push(`${hours} hour${hours > 1 ? 's' : ''}`);
  }
  if (mins > 0) {
    parts.push(`${mins} minute${mins > 1 ? 's' : ''}`);
  }
  
  if (parts.length === 0) {
    return '0 minutes';
  } else if (parts.length === 1) {
    return parts[0];
  } else if (parts.length === 2) {
    return parts.join(' and ');
  } else {
    return `${parts.slice(0, -1).join(', ')} and ${parts[parts.length - 1]}`;
  }
};

// Export default object with all functions
export default {
  formatDateIST,
  getRelativeTimeIST,
  datetimeLocalToIST,
  istToDatetimeLocal,
  getCurrentIST,
  getCurrentISTString,
  isInPastIST,
  isInFutureIST,
  addTimeIST,
  getTimezoneInfo,
  formatDuration,
  IST_TIMEZONE
};