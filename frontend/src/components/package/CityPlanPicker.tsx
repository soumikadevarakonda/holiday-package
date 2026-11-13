import React, { useState } from 'react';
import { formatINR } from '../../utils/format';
import type { CityPlan } from '../../api/types';

interface CityPlanPickerProps {
  cityPlans: CityPlan[];
  currentCities?: string[];
  currentNights?: Record<string, number>;
  onSelectPlan: (plan: CityPlan) => void;
  loading?: boolean;
}

const SHOWN = 6;

export const CityPlanPicker: React.FC<CityPlanPickerProps> = ({
  cityPlans,
  currentCities = [],
  currentNights = {},
  onSelectPlan,
  loading = false,
}) => {
  const [showAll, setShowAll] = useState(false);
  if (!cityPlans || cityPlans.length <= 1) return null;

  const isCurrent = (p: CityPlan) =>
    p.plan.length === currentCities.length &&
    p.plan.every((c, i) => c.city === currentCities[i] && c.nights === currentNights[c.city]);

  // Valid plans first (already ranked by price by the backend), then the ones that cannot be built.
  const ordered = [...cityPlans.filter((p) => p.valid !== false), ...cityPlans.filter((p) => p.valid === false)];
  const visible = showAll ? ordered : ordered.slice(0, SHOWN);

  return (
    <div className="bg-surface-container-low rounded-xl p-space-md flex flex-col gap-space-sm mb-space-md">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-primary text-[20px]">alt_route</span>
          <h4 className="font-headline-sm text-headline-sm text-on-surface">Other ways to split your nights</h4>
        </div>
        <span className="font-label-sm text-label-sm text-on-surface-variant">
          {cityPlans.filter((p) => p.valid !== false).length} of {cityPlans.length} plans can be built
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-space-xs">
        {visible.map((plan, idx) => {
          const current = isCurrent(plan);
          const invalid = plan.valid === false;
          const planStr = plan.label || plan.plan.map((c) => `${c.city} (${c.nights}N)`).join(' + ');
          return (
            <button
              key={planStr + idx}
              type="button"
              disabled={loading || current || invalid}
              title={invalid ? plan.reason || 'This plan cannot be built' : undefined}
              onClick={() => onSelectPlan(plan)}
              className={`p-space-sm rounded-lg text-left transition-colors border flex flex-col justify-between gap-1 ${
                current
                  ? 'bg-primary/10 border-primary/40 cursor-default'
                  : invalid
                  ? 'bg-surface-container-lowest border-outline-variant/30 opacity-50 cursor-not-allowed'
                  : 'bg-surface-container-lowest hover:bg-surface-container border-outline-variant/30 cursor-pointer'
              }`}
            >
              <span className="font-label-md text-label-md font-semibold text-on-surface">{planStr}</span>
              <span className="font-label-sm text-label-sm text-on-surface-variant">
                {current
                  ? 'Current plan'
                  : invalid
                  ? plan.reason || 'Cannot be built'
                  : plan.total_inr != null
                  ? `From ${formatINR(plan.total_inr)}`
                  : 'Rebuild on this plan'}
              </span>
            </button>
          );
        })}
      </div>
      {ordered.length > SHOWN && (
        <button
          type="button"
          onClick={() => setShowAll(!showAll)}
          className="self-start font-label-md text-label-md text-primary hover:underline cursor-pointer"
        >
          {showAll ? 'Show fewer' : `Show all ${ordered.length} plans`}
        </button>
      )}
    </div>
  );
};
