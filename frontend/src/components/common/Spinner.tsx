import React from 'react';

interface SpinnerProps {
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({
  label = 'Compiling Itinerary...',
  size = 'md',
  className = '',
}) => {
  const iconSize = size === 'sm' ? 'text-[18px]' : size === 'lg' ? 'text-[28px]' : 'text-[22px]';

  return (
    <div className={`flex items-center justify-center gap-space-sm text-primary ${className}`}>
      <span className={`material-symbols-outlined animate-spin ${iconSize}`}>
        progress_activity
      </span>
      {label && <span className="font-headline-sm text-headline-sm">{label}</span>}
    </div>
  );
};
