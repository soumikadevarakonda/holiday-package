import React, { useMemo, useState } from 'react';
import { DayCard } from './DayCard';
import { Icon } from '../common/Icon';
import type { TimelineDay, PackageItem } from '../../api/types';

interface DayTimelineProps {
  timeline: TimelineDay[];
  items: PackageItem[];
  cities?: string[];
  onChangeClick?: (item: PackageItem) => void;
  onRemoveClick?: (item: PackageItem) => void;
  onAddAttractionClick?: (day: TimelineDay) => void;
  readOnly?: boolean;
}

const TYPES = [
  { key: 'all', label: 'Everything', icon: 'list' },
  { key: 'flight', label: 'Flights', icon: 'flight' },
  { key: 'hotel', label: 'Stays', icon: 'hotel' },
  { key: 'transfer', label: 'Transfers', icon: 'directions_bus' },
  { key: 'attraction', label: 'Activities', icon: 'attractions' },
] as const;

/** Searchable text for an item: name, places, airline, hotel, room, category. */
const haystack = (it: PackageItem) =>
  [
    it.name, it.city, it.airline, it.flight_number, it.from_airport, it.to_airport, it.hotel_name, it.room_name,
    it.area, it.category, it.from_location, it.to_location, it.catalog_id,
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();

/** Day-by-day plan with a search box, type filter and day jump links. */
export const DayTimeline: React.FC<DayTimelineProps> = ({
  timeline,
  items,
  cities = [],
  onChangeClick,
  onRemoveClick,
  onAddAttractionClick,
  readOnly = false,
}) => {
  const [query, setQuery] = useState('');
  const [type, setType] = useState<string>('all');

  const byId = useMemo(() => new Map(items.map((it) => [it.item_id, it])), [items]);
  const counts = useMemo(() => {
    const c: Record<string, number> = { all: items.length };
    items.forEach((it) => (c[it.type] = (c[it.type] || 0) + 1));
    return c;
  }, [items]);

  const q = query.trim().toLowerCase();
  const filtering = q !== '' || type !== 'all';
  const matches = (it: PackageItem) => (type === 'all' || it.type === type) && (!q || haystack(it).includes(q));

  // The backend's timeline lists, per day, the item_ids that happen on it (in time order).
  const days = timeline.map((day) => {
    const dayItems = (day.events || [])
      .map((ev) => (ev.item_id ? byId.get(ev.item_id) : undefined))
      .filter((it): it is PackageItem => Boolean(it));
    return { day, items: dayItems.filter(matches) };
  });
  const visible = filtering ? days.filter((d) => d.items.length > 0) : days;
  const hits = days.reduce((s, d) => s + d.items.length, 0);

  return (
    <div className="flex flex-col gap-4">
      {/* Toolbar */}
      <div className="bg-white rounded-lg shadow-card p-3 flex flex-col gap-3 sticky top-0 z-10">
        <div className="relative">
          <Icon name="search" className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-mute" />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search your trip — hotel, airline, place, activity…"
            className="w-full h-11 pl-10 pr-3 rounded-md border border-line focus:outline-none focus:ring-2 focus:ring-brand"
            aria-label="Search your trip"
          />
        </div>
        <div className="flex items-center gap-2 overflow-x-auto no-scrollbar" role="group" aria-label="Show">
          {TYPES.map((t) => (
            <button
              key={t.key}
              type="button"
              onClick={() => setType(t.key)}
              aria-pressed={type === t.key}
              className={`h-9 px-3 rounded-full text-sm font-medium whitespace-nowrap flex items-center gap-1 border ${
                type === t.key ? 'bg-brand-light border-brand text-brand' : 'border-line text-ink-soft hover:border-ink-mute'
              }`}
            >
              <Icon name={t.icon} className="!text-base" />
              {t.label}
              <span className="text-xs opacity-70">{counts[t.key] || 0}</span>
            </button>
          ))}
        </div>
        {!filtering && timeline.length > 1 && (
          <nav className="flex items-center gap-1.5 overflow-x-auto no-scrollbar text-sm" aria-label="Jump to day">
            <span className="text-ink-mute whitespace-nowrap mr-1">Jump to</span>
            {timeline.map((d) => (
              <a
                key={d.day_number}
                href={`#day-${d.day_number}`}
                className="h-8 px-2.5 rounded-md bg-canvas hover:bg-brand-light hover:text-brand flex items-center whitespace-nowrap"
              >
                Day {d.day_number}
                {d.city ? <span className="ml-1 text-ink-mute">· {d.city}</span> : null}
              </a>
            ))}
          </nav>
        )}
        {filtering && (
          <p className="text-sm text-ink-mute" aria-live="polite">
            {hits} result{hits === 1 ? '' : 's'}
            <button
              type="button"
              onClick={() => {
                setQuery('');
                setType('all');
              }}
              className="ml-2 text-brand font-semibold hover:underline"
            >
              Clear
            </button>
          </p>
        )}
      </div>

      {visible.length === 0 && (
        <p className="bg-white rounded-lg shadow-card p-6 text-center text-ink-mute">Nothing in your trip matches “{query}”.</p>
      )}

      {visible.map(({ day, items: dayItems }) => (
        <DayCard
          key={day.day_number}
          day={day}
          items={dayItems}
          city={day.city || cities[0]}
          onChangeClick={onChangeClick}
          onRemoveClick={onRemoveClick}
          onAddAttractionClick={onAddAttractionClick}
          readOnly={readOnly}
          filtered={filtering}
        />
      ))}
    </div>
  );
};
