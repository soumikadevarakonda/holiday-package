import React from 'react';
import { formatINR } from '../../utils/format';

interface PriceDiffProps {
  diff: number | null | undefined;
  className?: string;
}

/** "+ ₹1,344", "− ₹2,000" or "No change in price". */
export const PriceDiff: React.FC<PriceDiffProps> = ({ diff, className = '' }) => {
  if (!diff) return <span className={`text-sm font-semibold text-ink-soft ${className}`}>No change in price</span>;
  const up = diff > 0;
  return (
    <span className={`text-lg font-bold tabular-nums ${up ? 'text-ink' : 'text-ok'} ${className}`}>
      {up ? '+ ' : '− '}
      {formatINR(Math.abs(diff))}
    </span>
  );
};
