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

  // Helper to map package items to a given day
  const getItemsForDay = (day: TimelineDay): PackageItem[] => {
    const dayDate = day.date ? day.date.slice(0, 10) : '';

    return items.filter((it) => {
      // Direct date match if available
      if (it.start && it.start.startsWith(dayDate)) return true;

      // Match item_id from timeline events
      if (day.events && day.events.some((ev) => ev.item_id === it.item_id)) {
        return true;
      }

      // Hotel items span multiple nights
      if (it.type === 'hotel') {
        const hotelStart = it.start ? it.start.slice(0, 10) : '';
        const hotelEnd = it.end ? it.end.slice(0, 10) : '';
        if (hotelStart && hotelEnd && dayDate >= hotelStart && dayDate < hotelEnd) {
          // Show hotel card on the first night or every night
          return dayDate === hotelStart;
        }
      }

      return false;
    });
  };

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
        // Find city associated with day
        const city = cities[Math.min(cities.length - 1, Math.floor((day.day_number - 1) / 4))];

        return (
          <DayCard
            key={day.day_number}
            day={day}
            items={dayItems.length > 0 ? dayItems : items.slice(0, 2)}
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
