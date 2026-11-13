import React from 'react';
import { formatINR } from '../../utils/format';

interface BudgetBarProps {
  total: number;
  budget: number;
  className?: string;
}

/** How much of the budget the trip uses. */
export const BudgetBar: React.FC<BudgetBarProps> = ({ total, budget, className = '' }) => {
  if (!budget) return null;
  const pct = Math.round((total / budget) * 100);
  const over = total > budget;
  return (
    <div className={className}>
      <div className="flex justify-between text-sm">
        <span className="text-ink-soft">Budget {formatINR(budget)}</span>
        <span className={`font-semibold ${over ? 'text-warn' : 'text-ok'}`}>
          {over ? `${formatINR(total - budget)} over` : `${formatINR(budget - total)} left`}
        </span>
      </div>
      <div
        className="mt-1.5 h-2 rounded-full bg-canvas overflow-hidden"
        role="meter"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.min(100, pct)}
        aria-label={`Uses ${pct}% of budget`}
      >
        <div className={`h-full rounded-full ${over ? 'bg-warn' : 'bg-ok'}`} style={{ width: `${Math.min(100, pct)}%` }} />
      </div>
      <div className="mt-1 text-xs text-ink-mute">Uses {pct}% of your budget</div>
    </div>
  );
};
