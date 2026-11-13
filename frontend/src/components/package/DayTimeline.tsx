import React, { useState } from 'react';
import { DayCard } from './DayCard';
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

export const DayTimeline: React.FC<DayTimelineProps> = ({
  timeline,
  items,
  cities = [],
  onChangeClick,
  onRemoveClick,
  onAddAttractionClick,
  readOnly = false,
}) => {
  const [selectedDayFilter, setSelectedDayFilter] = useState<number | 'all'>('all');

  // Filter timeline based on pill selection
  const filteredTimeline =
    selectedDayFilter === 'all'
      ? timeline
      : timeline.filter((d) => d.day_number === selectedDayFilter);

  // The backend's timeline lists, per day, the item_ids that happen on it (in time order).
  const byId = new Map(items.map((it) => [it.item_id, it]));
  const getItemsForDay = (day: TimelineDay): PackageItem[] =>
    (day.events || [])
      .map((ev) => (ev.item_id ? byId.get(ev.item_id) : undefined))
      .filter((it): it is PackageItem => Boolean(it));

  return (
    <div className="flex flex-col gap-space-xl">
      {/* Itinerary Quick Navigation Pill Bar */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        <button
          type="button"
          onClick={() => setSelectedDayFilter('all')}
          className={`px-3.5 py-1.5 rounded-full font-label-md text-label-md font-semibold whitespace-nowrap shadow-sm transition-colors cursor-pointer ${
            selectedDayFilter === 'all'
              ? 'bg-primary text-on-primary'
              : 'bg-surface-container-lowest text-on-surface-variant hover:text-on-surface'
          }`}
        >
          All Days
        </button>
        {timeline.map((d) => (
          <button
            key={d.day_number}
            type="button"
            onClick={() => setSelectedDayFilter(d.day_number)}
            className={`px-3.5 py-1.5 rounded-full font-label-md text-label-md whitespace-nowrap transition-colors cursor-pointer ${
              selectedDayFilter === d.day_number
                ? 'bg-primary text-on-primary font-semibold shadow-sm'
                : 'bg-surface-container-lowest text-on-surface-variant hover:text-on-surface'
            }`}
          >
            Day {d.day_number}
          </button>
        ))}
      </div>

      {/* Day Cards */}
      {filteredTimeline.map((day) => {
        const dayItems = getItemsForDay(day);
        const city = day.city || cities[0];

        return (
          <DayCard
            key={day.day_number}
            day={day}
            items={dayItems}
            city={city}
            onChangeClick={onChangeClick}
            onRemoveClick={onRemoveClick}
            onAddAttractionClick={onAddAttractionClick}
            readOnly={readOnly}
          />
        );
      })}
    </div>
  );
};
