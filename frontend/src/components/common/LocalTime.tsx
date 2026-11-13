import React from 'react';

interface LocalTimeProps {
  timeStr: string | null | undefined;
  zone?: string;
  className?: string;
}

export const LocalTime: React.FC<LocalTimeProps> = ({ timeStr, zone, className = '' }) => {
  if (!timeStr) return null;
  let formatted = timeStr;
  if (timeStr.includes('T')) {
    formatted = timeStr.split('T')[1].slice(0, 5);
  } else if (timeStr.length > 5 && timeStr.includes(':')) {
    formatted = timeStr.slice(0, 5);
  }

  return (
    <span className={`font-currency-md text-currency-md font-bold text-on-surface ${className}`}>
      {formatted} {zone ? <span className="font-label-sm text-label-sm text-on-surface-variant font-normal">{zone}</span> : null}
    </span>
  );
};
