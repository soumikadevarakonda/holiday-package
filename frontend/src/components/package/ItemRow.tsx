import React from 'react';
import { Photo } from '../common/Photo';
import { formatINR } from '../../utils/format';
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
    const airline = item.airline || (flightNo.startsWith('AI') ? 'Air India' : flightNo.startsWith('EK') ? 'Emirates' : 'Airline');
    const fromAirport = item.from_airport || 'BOM (Mumbai)';
    const toAirport = item.to_airport || 'NRT (Tokyo)';
    const departureTime = item.start ? item.start.slice(11, 16) || '08:15' : '08:15';
    const arrivalTime = item.end ? item.end.slice(11, 16) || '19:40' : '19:40';

    return (
      <div className="bg-surface-container-low rounded-lg p-space-md transition-all hover:shadow-md">
        <div className="flex flex-wrap items-center justify-between gap-space-xs mb-space-sm">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm font-semibold uppercase">
              International Flight
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
            </div>
            <div className="flex flex-col items-center flex-1 px-space-xs">
              <span className="font-label-sm text-label-sm text-on-surface-variant">Non-stop / Direct</span>
              <div className="w-full flex items-center gap-1 my-1">
                <span className="w-2 h-2 rounded-full bg-primary"></span>
                <div className="h-0.5 flex-1 bg-outline-variant"></div>
                <span className="material-symbols-outlined text-[16px] text-primary">
                  flight_takeoff
                </span>
                <div className="h-0.5 flex-1 bg-outline-variant"></div>
                <span className="w-2 h-2 rounded-full bg-primary"></span>
              </div>
              <span className="font-label-sm text-label-sm text-on-surface-variant">Scheduled Service</span>
            </div>
            <div className="text-right">
              <div className="font-currency-md text-currency-md font-bold text-on-surface">
                {arrivalTime}
              </div>
              <div className="font-body-sm text-body-sm text-on-surface-variant">{toAirport}</div>
            </div>
          </div>

          <div className="md:col-span-4 flex flex-col justify-between h-full gap-2">
            <div className="flex flex-col gap-1 font-body-sm text-body-sm text-on-surface-variant">
              <span className="flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px] text-primary">
                  airline_seat_recline_normal
                </span>
                Standard Class Allocation
              </span>
              <span className="flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px] text-primary">luggage</span>
                Included Checked Baggage
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
    const isIntercity = item.name?.toLowerCase().includes('shinkansen') || item.transfer_type === 'train';

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
                  {item.start ? item.start.slice(11, 16) || '10:00' : '10:00'}
                </div>
                <div className="font-body-sm text-body-sm text-on-surface-variant">
                  {item.from_location || 'Origin Hub'}
                </div>
              </div>
              <div className="flex flex-col items-center flex-1 px-space-xs">
                <span className="font-label-sm text-label-sm text-on-surface-variant">Express Transit</span>
                <div className="w-full flex items-center gap-1 my-1">
                  <span className="w-2 h-2 rounded-full bg-secondary"></span>
                  <div className="h-0.5 flex-1 bg-outline-variant"></div>
                  <span className="material-symbols-outlined text-[16px] text-secondary">train</span>
                  <div className="h-0.5 flex-1 bg-outline-variant"></div>
                  <span className="w-2 h-2 rounded-full bg-secondary"></span>
                </div>
                <span className="font-label-sm text-label-sm text-primary font-medium">Reserved Corridor</span>
              </div>
              <div className="text-right">
                <div className="font-currency-md text-currency-md font-bold text-on-surface">
                  {item.end ? item.end.slice(11, 16) || '12:15' : '12:15'}
                </div>
                <div className="font-body-sm text-body-sm text-on-surface-variant">
                  {item.to_location || 'Destination Hub'}
                </div>
              </div>
            </div>

            <div className="md:col-span-4 flex flex-col justify-between h-full gap-2">
              <div className="flex flex-col gap-1 font-body-sm text-body-sm text-on-surface-variant">
                <span className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-[16px] text-primary">
                    confirmation_number
                  </span>
                  Ordinary Car Reservation
                </span>
                <span className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-[16px] text-primary">luggage</span>
                  Luggage space verified
                </span>
              </div>
              <span className="font-label-sm text-label-sm text-primary bg-primary/10 px-2 py-1 rounded text-center font-medium">
                Confirmed Corridor Schedule
              </span>
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
                {item.vehicle_type || 'Private Executive Transfer (Luggage Optimized)'}
              </div>
              <div className="font-body-sm text-body-sm text-on-surface-variant">
                Synchronized with flight arrival/departure window
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-1 bg-surface-container-lowest text-primary rounded font-label-sm text-label-sm font-medium">
              Confirmed Voucher
            </span>
          </div>
        </div>
      </div>
    );
  }

  // Hotel Card
  if (type === 'hotel') {
    const hotelName = item.hotel_name || item.name || 'Accommodating Stay';
    const roomName = item.room_name || 'Standard / Deluxe Room';
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
              src={item.image || 'https://lh3.googleusercontent.com/aida-public/AB6AXuAgFNJ1fGswugrHCzIUNu2VcjUtzdd90aVmXwFGzP-Jp956Sw7Hk1kLe1GkvNXWViVcC3tUFxXhzO8BdkC3JKIrGilIcKBnAHO-UGRgWuP1PXp_JdoPZgoCTy7-oqT1AcfRsOpP2SmFRRTSoVNFLzg0D7pf7U3ymNt7z-BRJaW1ATMEocFr0aqVMx31hl-bCLVHNLNuUFMIpjl15jVMupf6jAyFs0Fmk6SWXgMj-9o'}
              alt={hotelName}
              fallbackType="hotel"
              className="w-full h-full object-cover"
            />
            <div className="absolute bottom-2 left-2 bg-on-surface/80 text-surface px-2 py-0.5 rounded font-label-sm text-label-sm backdrop-blur-sm">
              ★ 4.5 / 5.0 High Rating
            </div>
          </div>

          <div className="md:col-span-5 flex flex-col justify-between h-full">
            <div>
              <h3 className="font-headline-md text-headline-md text-on-surface font-semibold">
                {hotelName}
              </h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                {cityLabel} Central Area • Close to transit hubs
              </p>
              <div className="mt-2 flex flex-wrap gap-1.5 font-label-sm text-label-sm text-on-surface-variant">
                <span className="bg-surface-container-lowest px-2 py-0.5 rounded">
                  {roomName}
                </span>
                <span className="bg-surface-container-lowest px-2 py-0.5 rounded">
                  Daily Breakfast Included
                </span>
              </div>
            </div>
            <div className="font-body-sm text-body-sm text-on-surface-variant mt-2">
              Check-in: 15:00 • Free High-Speed WiFi
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
            <span className="font-label-sm text-label-sm text-center text-on-surface-variant">
              Verified room occupancy
            </span>
          </div>
        </div>
      </div>
    );
  }

  // Attraction Card
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between p-space-md rounded-lg bg-surface-container-low transition-all hover:bg-surface-container-high/40 gap-space-md">
      <div className="flex items-start gap-space-md">
        <div className="w-12 h-12 rounded-lg bg-surface-container-lowest flex items-center justify-center text-primary flex-shrink-0">
          <span className="material-symbols-outlined text-[24px]">visibility</span>
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
            Confirmed e-Ticket passes • Fast-track entry included
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
