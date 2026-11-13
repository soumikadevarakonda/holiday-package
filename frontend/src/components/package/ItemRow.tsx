import React from 'react';
import { Photo } from '../common/Photo';
import { formatDate, formatINR } from '../../utils/format';

function formatDuration(minutes?: number): string {
  if (!minutes) return '';
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h ? `${h}h${m ? ` ${m}m` : ''}` : `${m}m`;
}
import type { PackageItem } from '../../api/types';

interface ItemRowProps {
  item: PackageItem;
  city?: string;
  onChangeClick?: (item: PackageItem) => void;
  onRemoveClick?: (item: PackageItem) => void;
  readOnly?: boolean;
}

export const ItemRow: React.FC<ItemRowProps> = ({
  item,
  city,
  onChangeClick,
  onRemoveClick,
  readOnly = false,
}) => {
  const type = (item.type || '').toLowerCase();
  const price = item.price_inr ?? item.price ?? 0;

  // Flight Card
  if (type === 'flight') {
    const flightNo = item.flight_number || item.catalog_id || 'Flight';
    const airline = item.airline || item.name || 'Flight';
    const fromAirport = item.from_airport || '';
    const toAirport = item.to_airport || '';
    const departureTime = item.start ? item.start.slice(11, 16) : '';
    const arrivalTime = item.end ? item.end.slice(11, 16) : '';
    const depDate = item.start ? formatDate(item.start.slice(0, 10)) : '';
    const arrDate = item.end ? formatDate(item.end.slice(0, 10)) : '';
    const stopsLabel = item.stops ? `${item.stops} stop${item.stops > 1 ? 's' : ''}` : 'Non-stop';

    return (
      <div className="bg-surface-container-low rounded-lg p-space-md transition-all hover:shadow-md">
        <div className="flex flex-wrap items-center justify-between gap-space-xs mb-space-sm">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm font-semibold uppercase">
              {item.leg === 'return' ? 'Flight home' : 'Flight out'}
            </span>
            <span className="font-body-sm text-body-sm font-semibold text-on-surface">
              {airline} • {flightNo}
            </span>
          </div>
          <span className="font-currency-md text-currency-md font-bold text-primary">
            {formatINR(price)}{' '}
            <span className="font-body-sm text-label-sm text-on-surface-variant font-normal">
              included
            </span>
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-space-md items-center py-space-xs">
          <div className="md:col-span-8 flex items-center justify-between gap-space-md bg-surface-container-lowest p-space-sm rounded-lg">
            <div className="text-left">
              <div className="font-currency-md text-currency-md font-bold text-on-surface">
                {departureTime}
              </div>
              <div className="font-body-sm text-body-sm text-on-surface-variant">{fromAirport}</div>
              <div className="font-label-sm text-label-sm text-on-surface-variant">{depDate}</div>
            </div>
            <div className="flex flex-col items-center flex-1 px-space-xs">
              <span className="font-label-sm text-label-sm text-on-surface-variant">{stopsLabel}</span>
              <div className="w-full flex items-center gap-1 my-1">
                <span className="w-2 h-2 rounded-full bg-primary"></span>
                <div className="h-0.5 flex-1 bg-outline-variant"></div>
                <span className="material-symbols-outlined text-[16px] text-primary">
                  flight_takeoff
                </span>
                <div className="h-0.5 flex-1 bg-outline-variant"></div>
                <span className="w-2 h-2 rounded-full bg-primary"></span>
              </div>
              <span className="font-label-sm text-label-sm text-on-surface-variant">
                {formatDuration(item.duration_minutes)}
              </span>
            </div>
            <div className="text-right">
              <div className="font-currency-md text-currency-md font-bold text-on-surface">
                {arrivalTime}
              </div>
              <div className="font-body-sm text-body-sm text-on-surface-variant">{toAirport}</div>
              <div className="font-label-sm text-label-sm text-on-surface-variant">{arrDate}</div>
            </div>
          </div>

          <div className="md:col-span-4 flex flex-col justify-between h-full gap-2">
            <div className="flex flex-col gap-1 font-body-sm text-body-sm text-on-surface-variant">
              <span className="flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px] text-primary">
                  airline_seat_recline_normal
                </span>
                {item.quantity ?? 1} seat{(item.quantity ?? 1) > 1 ? 's' : ''}
                {item.details?.cabin ? ` • ${String(item.details.cabin).toLowerCase()}` : ''}
              </span>
              <span className="flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px] text-primary">schedule</span>
                Times are local
              </span>
            </div>
            {!readOnly && onChangeClick && (
              <button
                type="button"
                onClick={() => onChangeClick(item)}
                className="w-full py-1.5 px-3 rounded bg-surface-container-lowest text-on-surface hover:bg-surface-container-high transition-colors font-label-md text-label-md font-medium text-center shadow-sm cursor-pointer"
              >
                Change Flight
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Transfer Card
  if (type === 'transfer') {
    const isIntercity = Boolean(item.intercity);

    if (isIntercity) {
      return (
        <div className="bg-surface-container-low rounded-lg p-space-md transition-all hover:shadow-md">
          <div className="flex flex-wrap items-center justify-between gap-space-xs mb-space-sm">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm font-semibold uppercase">
                Intercity Rail
              </span>
              <span className="font-body-sm text-body-sm font-semibold text-on-surface">
                {item.name || 'High Speed Bullet Train'}
              </span>
            </div>
            <span className="font-currency-md text-currency-md font-bold text-primary">
              {formatINR(price)}{' '}
              <span className="font-body-sm text-label-sm text-on-surface-variant font-normal">
                included
              </span>
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-space-md items-center py-space-xs">
            <div className="md:col-span-8 flex items-center justify-between gap-space-md bg-surface-container-lowest p-space-sm rounded-lg">
              <div className="text-left">
                <div className="font-currency-md text-currency-md font-bold text-on-surface">
                  {item.start ? item.start.slice(11, 16) : ''}
                </div>
                <div className="font-body-sm text-body-sm text-on-surface-variant">
                  {item.from_location || ''}
                </div>
              </div>
              <div className="flex flex-col items-center flex-1 px-space-xs">
                <span className="font-label-sm text-label-sm text-on-surface-variant">
                  {formatDuration(item.duration_minutes)}
                </span>
                <div className="w-full flex items-center gap-1 my-1">
                  <span className="w-2 h-2 rounded-full bg-secondary"></span>
                  <div className="h-0.5 flex-1 bg-outline-variant"></div>
                  <span className="material-symbols-outlined text-[16px] text-secondary">train</span>
                  <div className="h-0.5 flex-1 bg-outline-variant"></div>
                  <span className="w-2 h-2 rounded-full bg-secondary"></span>
                </div>
                <span className="font-label-sm text-label-sm text-primary font-medium">
                  {(item.transfer_type || '').replace(/_/g, ' ').toLowerCase()}
                </span>
              </div>
              <div className="text-right">
                <div className="font-currency-md text-currency-md font-bold text-on-surface">
                  {item.end ? item.end.slice(11, 16) : ''}
                </div>
                <div className="font-body-sm text-body-sm text-on-surface-variant">
                  {item.to_location || ''}
                </div>
              </div>
            </div>

            <div className="md:col-span-4 flex flex-col justify-between h-full gap-2">
              <div className="flex flex-col gap-1 font-body-sm text-body-sm text-on-surface-variant">
                <span className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-[16px] text-primary">
                    confirmation_number
                  </span>
                  {item.quantity ?? 1} ticket{(item.quantity ?? 1) > 1 ? 's' : ''}
                </span>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="bg-surface-container-low rounded-lg p-space-md transition-all hover:shadow-md">
        <div className="flex flex-wrap items-center justify-between gap-space-xs mb-space-xs">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm font-semibold uppercase">
              Airport Transfer
            </span>
            <span className="font-body-sm text-body-sm font-semibold text-on-surface">
              {item.name || `${item.from_location || 'Airport'} → ${item.to_location || 'Hotel'}`}
            </span>
          </div>
          <span className="font-currency-md text-currency-md font-bold text-primary">
            {formatINR(price)}{' '}
            <span className="font-body-sm text-label-sm text-on-surface-variant font-normal">
              included
            </span>
          </span>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm pt-2">
          <div className="flex items-center gap-space-md">
            <div className="w-10 h-10 rounded-lg bg-surface-container-lowest flex items-center justify-center text-primary">
              <span className="material-symbols-outlined">directions_car</span>
            </div>
            <div>
              <div className="font-headline-sm text-headline-sm text-on-surface">
                {item.from_location && item.to_location
                  ? `${item.from_location} → ${item.to_location}`
                  : item.name}
              </div>
              <div className="font-body-sm text-body-sm text-on-surface-variant">
                {item.start ? `Pickup ${item.start.slice(11, 16)}` : ''}
                {item.duration_minutes ? ` • about ${formatDuration(item.duration_minutes)}` : ''}
                {item.quantity && item.quantity > 1 ? ` • ${item.quantity} vehicles/tickets` : ''}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-1 bg-surface-container-lowest text-primary rounded font-label-sm text-label-sm font-medium">
              {(item.transfer_type || 'Transfer').replace(/_/g, ' ').toLowerCase()}
            </span>
          </div>
        </div>
      </div>
    );
  }

  // Hotel Card
  if (type === 'hotel') {
    const hotelName = item.hotel_name || item.name || 'Accommodating Stay';
    const roomName = item.room_name || item.room_id || 'Room';
    const roomCount = item.quantity ?? 1;
    const cityLabel = city || item.city || 'Destination';

    return (
      <div className="bg-surface-container-low rounded-lg p-space-md transition-all hover:shadow-md">
        <div className="flex flex-wrap items-center justify-between gap-space-xs mb-space-sm">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-primary/10 text-primary font-label-sm text-label-sm font-semibold uppercase">
              Base Stay: {cityLabel}
            </span>
            {item.nights && (
              <span className="font-label-sm text-label-sm bg-surface-container-high text-on-surface-variant px-2 py-0.5 rounded">
                {item.nights} Nights Total
              </span>
            )}
          </div>
          <span className="font-currency-md text-currency-md font-bold text-primary">
            {formatINR(price)}{' '}
            <span className="font-body-sm text-label-sm text-on-surface-variant font-normal">
              included
            </span>
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-space-md items-center">
          <div className="md:col-span-4 h-32 rounded-lg overflow-hidden relative">
            <Photo
              src={item.image}
              alt={hotelName}
              fallbackType="hotel"
              className="w-full h-full object-cover"
            />
            {item.rating != null && (
              <div className="absolute bottom-2 left-2 bg-on-surface/80 text-surface px-2 py-0.5 rounded font-label-sm text-label-sm backdrop-blur-sm">
                {item.stars ? `${item.stars}★ • ` : ''}Guest rating {item.rating}/10
              </div>
            )}
          </div>

          <div className="md:col-span-5 flex flex-col justify-between h-full">
            <div>
              <h3 className="font-headline-md text-headline-md text-on-surface font-semibold">
                {hotelName}
              </h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                {item.area ? `${item.area}, ${cityLabel}` : cityLabel}
                {item.start && item.end ? ` • ${formatDate(item.start)} – ${formatDate(item.end)}` : ''}
              </p>
              <div className="mt-2 flex flex-wrap gap-1.5 font-label-sm text-label-sm text-on-surface-variant">
                <span className="bg-surface-container-lowest px-2 py-0.5 rounded">
                  {roomCount > 1 ? `${roomCount} × ` : ''}{roomName}
                </span>
                {item.details?.refundable != null && (
                  <span className="bg-surface-container-lowest px-2 py-0.5 rounded">
                    {item.details.refundable ? 'Refundable' : 'Non-refundable'}
                  </span>
                )}
              </div>
            </div>
            <div className="font-body-sm text-body-sm text-on-surface-variant mt-2">
              {item.details?.check_in_from ? `Check-in from ${item.details.check_in_from}` : ''}
              {item.details?.check_out_until ? ` • Check-out by ${item.details.check_out_until}` : ''}
            </div>
          </div>

          <div className="md:col-span-3 flex flex-col justify-end h-full gap-2">
            {!readOnly && onChangeClick && (
              <button
                type="button"
                onClick={() => onChangeClick(item)}
                className="w-full py-2 px-3 rounded-lg bg-surface-container-lowest text-primary hover:bg-primary hover:text-on-primary transition-all font-label-md text-label-md font-semibold text-center shadow-sm cursor-pointer"
              >
                Change Hotel
              </button>
            )}

          </div>
        </div>
      </div>
    );
  }

  // Attraction Card
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between p-space-md rounded-lg bg-surface-container-low transition-all hover:bg-surface-container-high/40 gap-space-md">
      <div className="flex items-start gap-space-md">
        <div className="w-16 h-16 rounded-lg overflow-hidden flex-shrink-0">
          <Photo
            src={item.image}
            alt={item.name || 'Attraction'}
            fallbackType="attraction"
            className="w-full h-full object-cover"
          />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-headline-sm text-headline-sm text-on-surface font-semibold">
              {item.name || item.attraction_name || 'City Excursion'}
            </h3>
            {item.time_slot && (
              <span className="font-label-sm text-label-sm px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant font-medium">
                {item.time_slot}
              </span>
            )}
          </div>
          <p className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">
            {[
              item.category ? item.category.replace(/_/g, ' ').toLowerCase() : null,
              item.details?.visit_minutes ? `about ${formatDuration(item.details.visit_minutes)}` : null,
              item.details?.open_from ? `open ${item.details.open_from}–${item.details.open_until}` : null,
              price === 0 ? 'free entry' : null,
            ]
              .filter(Boolean)
              .join(' • ')}
          </p>
        </div>
      </div>
      <div className="flex sm:flex-col items-center sm:items-end justify-between gap-space-xs">
        <span className="font-currency-md text-currency-md font-bold text-on-surface">
          {formatINR(price)}
        </span>
        {!readOnly && onRemoveClick && (
          <button
            type="button"
            onClick={() => onRemoveClick(item)}
            className="font-label-sm text-label-sm text-error hover:underline flex items-center gap-0.5 cursor-pointer"
          >
            <span className="material-symbols-outlined text-[14px]">delete</span>
            Remove Attraction
          </button>
        )}
      </div>
    </div>
  );
};
