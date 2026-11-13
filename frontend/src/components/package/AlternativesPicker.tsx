import React from 'react';
import { Icon } from '../common/Icon';
import { formatINR } from '../../utils/format';
import type { AlternativeKey, AlternativeSummary } from '../../api/types';

interface AlternativesPickerProps {
  alternatives: Partial<Record<AlternativeKey, AlternativeSummary>>;
  budget?: number;
  onChoose: (packageId: string) => void;
}

const META: Record<AlternativeKey, { title: string; icon: string; why: string }> = {
  cheapest: { title: 'Cheapest', icon: 'savings', why: 'Lowest total price' },
  fastest: { title: 'Fastest', icon: 'bolt', why: 'Least time on planes and trains' },
  best_rated: { title: 'Best rated', icon: 'hotel_class', why: 'Most hotel stars within your budget' },
};
const ORDER: AlternativeKey[] = ['cheapest', 'fastest', 'best_rated'];

const hours = (m: number) => `${Math.floor(m / 60)}h${m % 60 ? ` ${m % 60}m` : ''}`;

/** G4: the three packages side by side; the traveler picks one. */
export const AlternativesPicker: React.FC<AlternativesPickerProps> = ({ alternatives, budget, onChoose }) => {
  const keys = ORDER.filter((k) => alternatives[k]);
  if (keys.length === 0) return null;

  return (
    <section aria-labelledby="three-options">
      <h2 id="three-options" className="text-2xl font-bold text-ink">
        Pick your trip
      </h2>
      <p className="text-ink-mute mt-1">
        Three ways to do this holiday. Every option is a complete trip — you can still change anything after choosing.
      </p>
      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        {keys.map((k) => {
          const a = alternatives[k]!;
          const m = META[k];
          const same = keys.filter((o) => alternatives[o]!.package_id === a.package_id && o !== k).map((o) => META[o].title);
          return (
            <article key={k} className="bg-white rounded-lg shadow-card border border-line flex flex-col overflow-hidden">
              <div className="px-4 py-3 bg-navy-light flex items-center gap-2">
                <Icon name={m.icon} filled className="text-navy" />
                <div>
                  <h3 className="font-bold text-navy leading-tight">{m.title}</h3>
                  <p className="text-xs text-navy/80">{m.why}</p>
                </div>
              </div>
              <div className="p-4 flex flex-col gap-3 flex-1">
                <div className="flex flex-wrap items-center gap-1.5">
                  {a.city_plan.map((c, i) => (
                    <React.Fragment key={c.city}>
                      {i > 0 && <Icon name="arrow_forward" className="!text-sm text-ink-mute" />}
                      <span className="px-2 py-0.5 rounded-full bg-canvas text-sm font-medium">
                        {c.city} <span className="text-ink-mute">{c.nights}N</span>
                      </span>
                    </React.Fragment>
                  ))}
                </div>
                <dl className="grid grid-cols-2 gap-2 text-sm">
                  <div className={k === 'fastest' ? 'text-ink font-semibold' : 'text-ink-soft'}>
                    <dt className="text-xs text-ink-mute font-normal">Travel time</dt>
                    <dd className="flex items-center gap-1">
                      <Icon name="schedule" className="!text-base" />
                      {hours(a.travel_minutes)}
                    </dd>
                  </div>
                  <div className={k === 'best_rated' ? 'text-ink font-semibold' : 'text-ink-soft'}>
                    <dt className="text-xs text-ink-mute font-normal">Hotels</dt>
                    <dd>
                      <span className="text-sun">★</span> {a.avg_stars.toFixed(1)} stars avg
                    </dd>
                  </div>
                </dl>
                {same.length > 0 && <p className="text-xs text-ink-mute">Also the {same.join(' and ').toLowerCase()} option.</p>}
                <div className="mt-auto pt-3 border-t border-line flex items-end justify-between gap-2">
                  <div>
                    <div className={`text-2xl font-extrabold tabular-nums ${k === 'cheapest' ? 'text-ok' : 'text-ink'}`}>
                      {formatINR(a.total_inr)}
                    </div>
                    <div className={`text-xs ${a.within_budget ? 'text-ok' : 'text-warn'}`}>
                      {budget
                        ? a.within_budget
                          ? `${formatINR(budget - a.total_inr)} under budget`
                          : `${formatINR(a.total_inr - budget)} over budget`
                        : a.within_budget
                        ? 'Within budget'
                        : 'Over budget'}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => onChoose(a.package_id)}
                    className="h-10 px-4 rounded-md bg-brand hover:bg-brand-dark text-white font-semibold"
                  >
                    Choose
                  </button>
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
};
