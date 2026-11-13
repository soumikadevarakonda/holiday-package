import React from 'react';
import { formatINR } from '../../utils/format';

interface MoneyProps {
  amount: number | null | undefined;
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export const Money: React.FC<MoneyProps> = ({ amount, className = '', size = 'md' }) => {
  const formatted = formatINR(amount);

  let fontClass = 'font-currency-md text-currency-md';
  if (size === 'sm') fontClass = 'font-label-md text-label-md';
  if (size === 'lg') fontClass = 'font-currency-display text-headline-lg';
  if (size === 'xl') fontClass = 'font-currency-display text-display-lg';

  return (
    <span className={`tabular-nums ${fontClass} ${className}`}>
      {formatted}
    </span>
  );
};
