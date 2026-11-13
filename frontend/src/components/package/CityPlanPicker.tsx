import React from 'react';
import type { CityPlan } from '../../api/types';

interface CityPlanPickerProps {
  cityPlans: CityPlan[];
  selectedPlan?: CityPlan;
  onSelectPlan: (plan: CityPlan) => void;
  loading?: boolean;
}

export const CityPlanPicker: React.FC<CityPlanPickerProps> = ({
  cityPlans,
  onSelectPlan,
  loading = false,
}) => {
  if (!cityPlans || cityPlans.length <= 1) return null;

  return (
    <div className="bg-surface-container-low rounded-xl p-space-md flex flex-col gap-space-sm mb-space-md">
      <div className="flex items-center gap-2">
        <span className="material-symbols-outlined text-primary text-[20px]">alt_route</span>
        <h4 className="font-headline-sm text-headline-sm text-on-surface">
          Alternative City Route Allocations (G3)
        </h4>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-space-xs">
        {cityPlans.map((plan, idx) => {
          const planStr = Object.entries(plan.nights || {})
            .map(([c, n]) => `${c} (${n}N)`)
            .join(' + ');

          return (
            <button
              key={idx}
              type="button"
              disabled={loading}
              onClick={() => onSelectPlan(plan)}
              className="p-space-sm rounded-lg bg-surface-container-lowest hover:bg-surface-container text-left transition-colors text-body-sm text-body-sm border border-outline-variant/30 flex flex-col justify-between"
            >
              <span className="font-semibold text-on-surface">Option {idx + 1}</span>
              <span className="text-on-surface-variant font-label-sm text-label-sm mt-1">{planStr}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
