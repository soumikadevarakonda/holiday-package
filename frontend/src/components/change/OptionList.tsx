import React from 'react';
import { PriceDiff } from './PriceDiff';
import { Photo } from '../common/Photo';
import { Icon } from '../common/Icon';
import { ScoreBadge } from '../common/ScoreBadge';
import type { ChangeOption } from '../../api/types';

interface OptionListProps {
  options: ChangeOption[];
  kind?: string;
  currentCatalogId?: string;
  onSelectOption: (option: ChangeOption) => void;
  loading?: boolean;
}

/** Alternatives for one part of the trip, each with its price difference and a Select button. */
export const OptionList: React.FC<OptionListProps> = ({ options, kind, currentCatalogId, onSelectOption, loading = false }) => {
  if (options.length === 0) {
    return <p className="p-6 text-center text-ink-mute">No options match.</p>;
  }

  return (
    <ul className="flex flex-col gap-3">
      {options.map((o) => {
        const current = o.current ?? o.catalog_id === currentCatalogId;
        const d = o.details || {};
        const notes: string[] = [...(d.side_effects || []), ...(d.warnings || [])];
        const showPhoto = kind === 'hotel' || kind === 'attraction';
        return (
          <li
            key={o.key || o.catalog_id}
            className={`rounded-lg border bg-white overflow-hidden flex ${current ? 'border-brand ring-1 ring-brand' : 'border-line'}`}
          >
            {showPhoto && (
              <Photo
                src={o.image}
                alt={o.name}
                fallbackType={kind === 'hotel' ? 'hotel' : 'attraction'}
                className="w-28 sm:w-36 object-cover shrink-0 self-stretch"
              />
            )}
            <div className="flex-1 p-3 flex flex-col gap-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  {current && (
                    <span className="inline-block mb-1 px-2 py-0.5 rounded text-xs font-semibold bg-brand text-white">
                      Your current choice
                    </span>
                  )}
                  <h3 className="font-bold text-brand leading-snug">{o.name}</h3>
                </div>
                {kind === 'hotel' && <ScoreBadge rating={o.rating} stars={d.stars} compact />}
              </div>

              {kind === 'hotel' && (
                <p className="text-sm text-ink-soft">
                  {o.room_type}
                  {d.refundable === true && <span className="text-ok"> · free cancellation</span>}
                </p>
              )}
              {kind === 'flight' && (
                <p className="text-sm text-ink-soft flex flex-wrap gap-x-3">
                  <span className="font-semibold text-ink tabular-nums">
                    {o.departure_time} → {o.arrival_time}
                  </span>
                  <span>{o.duration}</span>
                  <span className={d.stops ? 'text-warn' : 'text-ok'}>{d.stops ? `${d.stops} stop` : 'Direct'}</span>
                  {d.seats_left != null && <span>{d.seats_left} seats left</span>}
                </p>
              )}
              {kind === 'attraction' && (
                <p className="text-sm text-ink-soft">
                  {o.time_slot && <span className="font-semibold text-ink">Starts {o.time_slot}</span>}
                  {o.category ? ` · ${o.category.replace(/_/g, ' ').toLowerCase()}` : ''}
                  {d.visit_minutes ? ` · ${d.visit_minutes} min` : ''}
                  {d.child_friendly ? ' · good for kids' : ''}
                </p>
              )}
              {notes.length > 0 && (
                <p className="text-xs text-warn flex items-start gap-1">
                  <Icon name="info" className="!text-sm mt-px" />
                  {notes.join(' ')}
                </p>
              )}

              <div className="mt-auto pt-2 flex items-end justify-between gap-2">
                <div>
                  <PriceDiff diff={o.price_diff} />
                  <div className="text-xs text-ink-mute">
                    {o.price_inr === 0 ? 'Free' : `₹ ${Math.round(o.price_inr).toLocaleString('en-IN')} total`}
                  </div>
                </div>
                {!current && (
                  <button
                    type="button"
                    disabled={loading}
                    onClick={() => onSelectOption(o)}
                    className="h-10 px-4 rounded-md bg-brand hover:bg-brand-dark text-white font-semibold disabled:opacity-50"
                  >
                    {kind === 'attraction' ? 'Add' : 'Select'}
                  </button>
                )}
              </div>
            </div>
          </li>
        );
      })}
    </ul>
  );
};
