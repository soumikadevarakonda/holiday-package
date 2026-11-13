import React from 'react';
import { formatINR } from '../../utils/format';

interface MoneyProps {
  amount: number | null | undefined;
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

const SIZES = { sm: 'text-sm', md: 'text-base', lg: 'text-xl', xl: 'text-3xl' };

export const Money: React.FC<MoneyProps> = ({ amount, className = '', size = 'md' }) => (
  <span className={`tabular-nums font-bold ${SIZES[size]} ${className}`}>{formatINR(amount)}</span>
);
