import React from 'react';
import { ItemRow } from './ItemRow';
import { Icon } from '../common/Icon';
import { formatINR, formatWeekdayDate } from '../../utils/format';
import type { TimelineDay, PackageItem } from '../../api/types';

interface DayCardProps {
  day: TimelineDay;
  items: PackageItem[];
  city?: string;
  onChangeClick?: (item: PackageItem) => void;
  onRemoveClick?: (item: PackageItem) => void;
  onAddAttractionClick?: (day: TimelineDay) => void;
  readOnly?: boolean;
  filtered?: boolean;
}

function dayTitle(items: PackageItem[], city?: string): string {
  if (items.some((i) => i.type === 'flight' && i.leg === 'arrival')) return `Arrive in ${city || 'your destination'}`;
  if (items.some((i) => i.type === 'flight' && i.leg === 'return')) return 'Fly home';
  if (items.some((i) => i.type === 'transfer' && i.intercity)) return `Travel to ${city || 'the next city'}`;
  if (items.length === 0) return city ? `Free day in ${city}` : 'Free day';
  return city ? `Explore ${city}` : 'Explore';
}

/** One day of the trip: header (day number, date, city) and what happens that day. */
export const DayCard: React.FC<DayCardProps> = ({
  day,
  items,
  city,
  onChangeClick,
  onRemoveClick,
  onAddAttractionClick,
  readOnly = false,
  filtered = false,
}) => {
  const subtotal = items.reduce((s, it) => s + (it.price_inr ?? it.price ?? 0), 0);

  return (
    <section id={`day-${day.day_number}`} className="scroll-mt-24" aria-labelledby={`day-${day.day_number}-title`}>
      <div className="flex items-end justify-between gap-3 mb-2">
        <div className="flex items-center gap-3">
          <span className="w-11 h-11 rounded-lg bg-navy text-white flex flex-col items-center justify-center leading-none shrink-0">
            <span className="text-[10px] uppercase tracking-wide opacity-80">Day</span>
            <span className="text-lg font-bold">{day.day_number}</span>
          </span>
          <div>
            <h3 id={`day-${day.day_number}-title`} className="text-lg font-bold text-ink leading-tight">
              {dayTitle(items, city)}
            </h3>
            <p className="text-sm text-ink-mute">
              {formatWeekdayDate(day.date)}
              {city ? ` · ${city}` : ''}
            </p>
          </div>
        </div>
        {subtotal > 0 && <span className="text-sm text-ink-mute tabular-nums whitespace-nowrap">{formatINR(subtotal)}</span>}
      </div>

      <div className="flex flex-col gap-2">
        {items.length === 0 && (
          <p className="text-sm text-ink-mute bg-white border border-dashed border-line rounded-lg p-4">
            {filtered ? 'Nothing matches your filter on this day.' : 'Nothing booked — time to explore on your own.'}
          </p>
        )}
        {items.map((item, idx) => (
          <ItemRow
            key={item.item_id || idx}
            item={item}
            city={city}
            onChangeClick={onChangeClick}
            onRemoveClick={onRemoveClick}
            readOnly={readOnly}
          />
        ))}
        {!readOnly && onAddAttractionClick && !filtered && (
          <button
            type="button"
            onClick={() => onAddAttractionClick(day)}
            className="self-start h-9 px-3 rounded-md text-sm font-semibold text-brand hover:bg-brand-light flex items-center gap-1"
          >
            <Icon name="add_circle" className="!text-lg" />
            Add an activity on day {day.day_number}
          </button>
        )}
      </div>
    </section>
  );
};
