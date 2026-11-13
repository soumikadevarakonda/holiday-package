import React from 'react';
import { formatINR } from '../../utils/format';

interface PriceDiffProps {
  diff: number | null | undefined;
  className?: string;
}

export const PriceDiff: React.FC<PriceDiffProps> = ({ diff, className = '' }) => {
  if (diff === null || diff === undefined || diff === 0) {
    return (
      <span className={`font-currency-md text-currency-md font-bold text-on-surface ${className}`}>
        Included
      </span>
    );
  }

  const isUpgrade = diff > 0;
  const colorClass = isUpgrade ? 'text-primary' : 'text-tertiary';
  const prefix = isUpgrade ? '+ ' : '- ';

  return (
    <span className={`font-currency-md text-currency-md font-bold ${colorClass} ${className}`}>
      {prefix}{formatINR(Math.abs(diff))}
    </span>
  );
};
