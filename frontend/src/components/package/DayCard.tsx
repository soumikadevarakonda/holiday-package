import React from 'react';
import { ItemRow } from './ItemRow';
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
}

export const DayCard: React.FC<DayCardProps> = ({
  day,
  items,
  city,
  onChangeClick,
  onRemoveClick,
  onAddAttractionClick,
  readOnly = false,
}) => {
  // Compute day subtotal
  const daySubtotal = items.reduce((sum, it) => sum + (it.price_inr ?? it.price ?? 0), 0);

  // Pad day number (e.g. DAY 01)
  const dayLabel = `DAY ${String(day.day_number).padStart(2, '0')}`;
  const dateStr = formatWeekdayDate(day.date);

  // Day title from what actually happens that day
  const flights = items.filter((it) => it.type === 'flight');
  const intercity = items.find((it) => it.type === 'transfer' && it.intercity);
  let dayTitle = city ? `Exploring ${city}` : `Day ${day.day_number}`;
  if (flights.some((f) => f.leg === 'arrival')) {
    dayTitle = `Arrival in ${city || 'your destination'}`;
  } else if (flights.some((f) => f.leg === 'return')) {
    dayTitle = 'Departure & flight home';
  } else if (intercity) {
    dayTitle = `Travel to ${city || 'the next city'}`;
  } else if (items.length === 0) {
    dayTitle = city ? `Free day in ${city}` : 'Free day';
  }

  return (
    <div className="bg-surface-container-lowest rounded-xl shadow-sm p-space-lg flex flex-col gap-space-lg">
      {/* Day Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-space-sm gap-2">
        <div className="flex items-center gap-space-sm">
          <span className="bg-primary text-on-primary px-3 py-1 rounded font-label-md text-label-md font-bold tracking-tight">
            {dayLabel}
          </span>
          <div>
            <h2 className="font-headline-md text-headline-md text-on-surface font-semibold">
              {dayTitle}
            </h2>
            <p className="font-body-sm text-body-sm text-on-surface-variant">
              {dateStr} {city ? `• ${city}` : ''}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-space-xs text-right">
          <span className="font-label-sm text-label-sm text-on-surface-variant uppercase">
            Day Subtotal
          </span>
          <span className="font-currency-md text-currency-md text-on-surface font-bold">
            {formatINR(daySubtotal)}
          </span>
        </div>
      </div>

      {/* Item Rows */}
      <div className="flex flex-col gap-space-md">
        {items.length === 0 && (
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            Nothing booked — time to explore on your own.
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
      </div>

      {/* Add Attraction CTA */}
      {!readOnly && onAddAttractionClick && (
        <button
          type="button"
          onClick={() => onAddAttractionClick(day)}
          className="w-full py-3 rounded-lg bg-surface-container-low hover:bg-surface-container-high text-primary font-headline-sm text-headline-sm font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer"
        >
          <span className="material-symbols-outlined text-[20px]">add_circle</span>
          <span>+ Add Attraction to Day {day.day_number}</span>
        </button>
      )}
    </div>
  );
};
