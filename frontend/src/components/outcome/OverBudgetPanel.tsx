import React from 'react';
import { Icon } from '../common/Icon';
import { formatINR } from '../../utils/format';

interface OverBudgetPanelProps {
  cheapestTotal?: number;
  overBy?: number;
  suggestion?: string;
  onModifyRequest: () => void;
  onAcceptCheapest?: () => void;
}

/** Shown when even the cheapest possible trip costs more than the budget. */
export const OverBudgetPanel: React.FC<OverBudgetPanelProps> = ({
  cheapestTotal,
  overBy,
  suggestion,
  onModifyRequest,
  onAcceptCheapest,
}) => (
  <section className="bg-white rounded-lg shadow-card border-l-4 border-warn p-5 sm:p-6" aria-live="polite">
    <div className="flex items-start gap-3">
      <span className="w-10 h-10 rounded-full bg-warn-light text-warn flex items-center justify-center shrink-0">
        <Icon name="account_balance_wallet" />
      </span>
      <div className="flex-1">
        <h2 className="text-lg font-bold text-ink">This trip doesn't fit your budget</h2>
        <p className="text-sm text-ink-soft mt-1">
          We found trips for your dates, but even the cheapest one costs more than you set.
        </p>
        <dl className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-4">
          {cheapestTotal !== undefined && (
            <div>
              <dt className="text-xs text-ink-mute">Cheapest trip</dt>
              <dd className="text-xl font-bold text-ink tabular-nums">{formatINR(cheapestTotal)}</dd>
            </div>
          )}
          {overBy !== undefined && overBy > 0 && (
            <div>
              <dt className="text-xs text-ink-mute">Over your budget by</dt>
              <dd className="text-xl font-bold text-warn tabular-nums">{formatINR(overBy)}</dd>
            </div>
          )}
        </dl>
        {suggestion && (
          <p className="mt-3 text-sm bg-canvas rounded-md p-3 text-ink">
            <Icon name="lightbulb" className="!text-base text-warn mr-1" />
            {suggestion}
          </p>
        )}
        <div className="mt-4 flex flex-wrap gap-2">
          {onAcceptCheapest && (
            <button
              type="button"
              onClick={onAcceptCheapest}
              className="h-10 px-4 rounded-md bg-brand hover:bg-brand-dark text-white font-semibold"
            >
              See the cheapest trip
            </button>
          )}
          <button
            type="button"
            onClick={onModifyRequest}
            className="h-10 px-4 rounded-md border border-brand text-brand font-semibold hover:bg-brand-light"
          >
            Change search
          </button>
        </div>
      </div>
    </div>
  </section>
);
