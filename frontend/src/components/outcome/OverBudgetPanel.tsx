import React from 'react';
import { formatINR } from '../../utils/format';

interface OverBudgetPanelProps {
  cheapestTotal?: number;
  overBy?: number;
  suggestion?: string;
  onModifyRequest: () => void;
  onAcceptCheapest?: () => void;
}

export const OverBudgetPanel: React.FC<OverBudgetPanelProps> = ({
  cheapestTotal,
  overBy,
  suggestion = 'Raise your budget or decrease duration by 1–2 nights to fit available inventory.',
  onModifyRequest,
  onAcceptCheapest,
}) => {
  return (
    <div className="bg-surface-container-lowest rounded-xl shadow-md p-space-lg lg:p-space-xl border border-tertiary/20 flex flex-col gap-space-md">
      <div className="flex items-start gap-space-md">
        <div className="w-12 h-12 rounded-xl bg-tertiary-fixed text-on-tertiary-fixed flex items-center justify-center shrink-0">
          <span className="material-symbols-outlined text-[26px]">account_balance_wallet</span>
        </div>
        <div className="flex-1">
          <div className="flex flex-wrap items-center justify-between gap-space-xs">
            <span className="px-2.5 py-0.5 rounded-full bg-tertiary-fixed text-on-tertiary-fixed font-label-sm text-label-sm uppercase font-semibold">
              Budget Constraint Advisory
            </span>
            {overBy && overBy > 0 && (
              <span className="font-currency-md text-currency-md font-bold text-tertiary">
                Over by {formatINR(overBy)}
              </span>
            )}
          </div>
          <h3 className="font-headline-lg text-headline-lg text-on-surface mt-1">
            Package Exceeds Requested Budget
          </h3>
          <p className="font-body-md text-body-md text-on-surface-variant mt-1">
            We discovered verified travel combinations matching your corridor and dates, but the lowest available airfare and accommodation tier exceeds your specified limit.
          </p>
        </div>
      </div>

      {/* Comparison metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-md bg-surface-container-low p-space-md rounded-xl">
        {cheapestTotal !== undefined && (
          <div className="flex flex-col">
            <span className="font-label-sm text-label-sm text-on-surface-variant uppercase">
              Cheapest Feasible Package Total
            </span>
            <span className="font-currency-display text-headline-lg text-primary font-bold mt-0.5">
              {formatINR(cheapestTotal)}
            </span>
            <span className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">
              Includes guaranteed return flights + base hotel stays
            </span>
          </div>
        )}
        <div className="flex flex-col justify-center">
          <span className="font-label-sm text-label-sm text-primary uppercase font-bold">
            Recommendation
          </span>
          <p className="font-body-md text-body-md text-on-surface font-medium mt-0.5">
            {suggestion}
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-end gap-space-sm pt-space-xs">
        <button
          type="button"
          onClick={onModifyRequest}
          className="px-space-md py-2.5 rounded-lg bg-surface-container-low hover:bg-surface-container text-on-surface font-headline-sm text-headline-sm transition-colors"
        >
          Adjust Trip Parameters
        </button>
        {onAcceptCheapest && (
          <button
            type="button"
            onClick={onAcceptCheapest}
            className="px-space-lg py-2.5 rounded-lg bg-primary hover:bg-primary-container text-on-primary font-headline-sm text-headline-sm transition-all shadow-sm"
          >
            Review Cheapest Package
          </button>
        )}
      </div>
    </div>
  );
};
