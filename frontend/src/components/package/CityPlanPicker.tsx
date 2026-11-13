import React, { useState } from 'react';
import { Icon } from '../common/Icon';
import { formatINR } from '../../utils/format';
import type { CityPlan } from '../../api/types';

interface CityPlanPickerProps {
  cityPlans: CityPlan[];
  currentCities?: string[];
  currentNights?: Record<string, number>;
  currentTotal?: number;
  onSelectPlan: (plan: CityPlan) => void;
  loading?: boolean;
}

const SHOWN = 6;

/** Other ways to split the nights between cities, cheapest first, with the price difference. */
export const CityPlanPicker: React.FC<CityPlanPickerProps> = ({
  cityPlans,
  currentCities = [],
  currentNights = {},
  currentTotal,
  onSelectPlan,
  loading = false,
}) => {
  const [showAll, setShowAll] = useState(false);
  if (!cityPlans || cityPlans.length <= 1) return null;

  const isCurrent = (p: CityPlan) =>
    p.plan.length === currentCities.length &&
    p.plan.every((c, i) => c.city === currentCities[i] && c.nights === currentNights[c.city]);
  const valid = cityPlans.filter((p) => p.valid !== false);
  const ordered = [...valid, ...cityPlans.filter((p) => p.valid === false)];
  const visible = showAll ? ordered : ordered.slice(0, SHOWN);

  return (
    <section className="bg-white rounded-lg shadow-card p-4" aria-labelledby="city-splits">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="city-splits" className="text-lg font-bold text-ink flex items-center gap-2">
          <Icon name="alt_route" className="text-brand" />
          Try a different city split
        </h2>
        <span className="text-sm text-ink-mute">
          {valid.length} of {cityPlans.length} can be built · cheapest first
        </span>
      </div>
      <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
        {visible.map((plan, idx) => {
          const current = isCurrent(plan);
          const invalid = plan.valid === false;
          const diff = currentTotal != null && plan.total_inr != null ? plan.total_inr - currentTotal : null;
          return (
            <button
              key={(plan.label || '') + idx}
              type="button"
              disabled={loading || current || invalid}
              title={invalid ? plan.reason || 'This split cannot be built' : undefined}
              onClick={() => onSelectPlan(plan)}
              className={`p-3 rounded-md border text-left flex items-center justify-between gap-3 ${
                current
                  ? 'border-brand bg-brand-light cursor-default'
                  : invalid
                  ? 'border-line opacity-50 cursor-not-allowed'
                  : 'border-line hover:border-brand hover:bg-brand-light/50'
              }`}
            >
              <span className="min-w-0">
                <span className="block font-semibold text-ink truncate">
                  {plan.plan.map((c) => `${c.city} ${c.nights}N`).join(' → ')}
                </span>
                <span className="block text-xs text-ink-mute truncate">
                  {current ? 'Your current plan' : invalid ? plan.reason || 'Cannot be built' : `From ${formatINR(plan.total_inr)}`}
                </span>
              </span>
              {!current && !invalid && diff != null && (
                <span className={`text-sm font-semibold tabular-nums whitespace-nowrap ${diff > 0 ? 'text-ink-soft' : 'text-ok'}`}>
                  {diff === 0 ? 'Same price' : `${diff > 0 ? '+' : '−'}${formatINR(Math.abs(diff))}`}
                </span>
              )}
              {current && <Icon name="check_circle" filled className="text-brand" />}
            </button>
          );
        })}
      </div>
      {ordered.length > SHOWN && (
        <button
          type="button"
          onClick={() => setShowAll(!showAll)}
          className="mt-3 text-sm font-semibold text-brand hover:underline"
        >
          {showAll ? 'Show fewer' : `Show all ${ordered.length} splits`}
        </button>
      )}
    </section>
  );
};
