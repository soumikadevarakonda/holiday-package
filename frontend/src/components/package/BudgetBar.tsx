import React from 'react';
import { formatINR } from '../../utils/format';

interface BudgetBarProps {
  total: number;
  budget: number;
  className?: string;
}

export const BudgetBar: React.FC<BudgetBarProps> = ({ total, budget, className = '' }) => {
  const percentage = Math.min(100, Math.round((total / (budget || 1)) * 100));
  const isOver = total > budget;

  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      <div className="flex justify-between items-center font-label-sm text-label-sm text-on-surface-variant">
        <span>Budget Utilization</span>
        <span className={isOver ? 'text-error font-semibold' : 'text-primary font-semibold'}>
          {percentage}% ({formatINR(total)} of {formatINR(budget)})
        </span>
      </div>
      <div className="w-full h-2 bg-surface-container-highest rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-300 ${
            isOver ? 'bg-error' : 'bg-primary'
          }`}
          style={{ width: `${Math.min(100, percentage)}%` }}
        />
      </div>
    </div>
  );
};
