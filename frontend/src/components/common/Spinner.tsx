import React from 'react';

interface SpinnerProps {
  label?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const SIZES = { sm: 'w-4 h-4 border-2', md: 'w-6 h-6 border-[3px]', lg: 'w-10 h-10 border-4' };

export const Spinner: React.FC<SpinnerProps> = ({ label, size = 'md', className = '' }) => (
  <div className={`flex items-center justify-center gap-3 ${className}`} role="status">
    <span className={`${SIZES[size]} rounded-full border-brand/25 border-t-brand animate-spin`} />
    {label && <span className="text-sm font-medium text-ink-soft">{label}</span>}
  </div>
);
