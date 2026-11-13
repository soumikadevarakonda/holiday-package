import React from 'react';

interface LocalTimeProps {
  timeStr: string | null | undefined;
  zone?: string;
  className?: string;
}

/** Shows HH:MM from "YYYY-MM-DDTHH:MM" (catalog times are already local). */
export const LocalTime: React.FC<LocalTimeProps> = ({ timeStr, zone, className = '' }) => {
  if (!timeStr) return null;
  const t = timeStr.includes('T') ? timeStr.split('T')[1].slice(0, 5) : timeStr.slice(0, 5);
  return (
    <span className={`tabular-nums font-semibold ${className}`}>
      {t}
      {zone && <span className="ml-1 text-xs font-normal text-ink-mute">{zone}</span>}
    </span>
  );
};
