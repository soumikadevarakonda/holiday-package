import React, { useState } from 'react';
import { formatINR, formatDate } from '../../utils/format';
import { ItemRow } from '../package/ItemRow';
import type { ReservationResponse, PackageItem } from '../../api/types';

interface ReservationSummaryProps {
  reservation: ReservationResponse;
}

export const ReservationSummary: React.FC<ReservationSummaryProps> = ({ reservation }) => {
  const [copied, setCopied] = useState(false);
  const snapshot = reservation.snapshot || {};
  const items: PackageItem[] = reservation.items || snapshot.items || [];
  const travelers = snapshot.travelers || { adults: 0, children: 0, child_ages: [] };
  const cities = snapshot.cities || [];
  const country = snapshot.country || 'Destination';
  const startDateStr = formatDate(snapshot.start_date);
  const endDateStr = formatDate(snapshot.end_date);
  const total = reservation.total_price || snapshot.total_inr || 0;

  const ref10 = reservation.reference || reservation.reservation_reference || '';

  const handleCopy = () => {
    if (ref10) {
      navigator.clipboard.writeText(ref10);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const flights = items.filter((it) => it.type === 'flight');
  const hotels = items.filter((it) => it.type === 'hotel');
  const transfers = items.filter((it) => it.type === 'transfer');
  const attractions = items.filter((it) => it.type === 'attraction');

  return (
    <div className="flex flex-col gap-space-xl">
      {/* Top Banner: Success Confirmation Banner & Executive Manifest Bar */}
      <div className="relative bg-surface-container-lowest rounded-xl shadow-sm p-space-lg lg:p-space-xl overflow-hidden">
        <div className="absolute -right-16 -top-16 w-64 h-64 bg-primary/5 rounded-full blur-2xl pointer-events-none"></div>
        <div className="relative flex flex-col lg:flex-row lg:items-start lg:justify-between gap-space-lg">
          {/* Left details */}
          <div className="flex flex-col gap-space-md max-w-3xl">
            <div className="flex flex-wrap items-center gap-space-sm">
              <span className="inline-flex items-center gap-1.5 bg-primary/10 text-primary px-space-sm py-1 rounded-full font-label-sm text-label-sm uppercase tracking-wider font-semibold">
                <span className="material-symbols-outlined text-[16px]">check_circle</span>
                Reservation Confirmed &amp; Locked
              </span>
              <span className="inline-flex items-center gap-1 bg-surface-container text-on-surface-variant px-space-sm py-1 rounded-full font-label-sm text-label-sm">
                <span>Internal System Reference</span>
              </span>
            </div>

            <div>
              <div className="flex items-baseline gap-space-sm flex-wrap">
                <span className="font-display-lg text-display-lg text-on-surface tracking-tight font-bold">
                  {ref10}
                </span>
                <button
                  type="button"
                  onClick={handleCopy}
                  className="bg-surface-container-low hover:bg-surface-container text-primary font-label-sm text-label-sm px-space-sm py-1 rounded transition-colors uppercase tracking-wider cursor-pointer"
                >
                  {copied ? 'COPIED' : 'COPY REF'}
                </button>
              </div>
              <p className="font-headline-md text-headline-md text-on-surface-variant mt-1">
                {cities.join(' & ')}, {country}{' '}
                {startDateStr && endDateStr ? (
                  <>
                    <span className="text-outline-variant">•</span> {startDateStr} – {endDateStr}
                  </>
                ) : null}
              </p>
            </div>
          </div>

          {/* Right summary column */}
          <div className="lg:w-80 bg-surface-container-low rounded-xl p-space-md flex flex-col justify-between self-stretch">
            <div>
              <div className="flex items-center justify-between text-on-surface-variant font-label-md text-label-md">
                <span>Confirmation Status</span>
                <span className="text-primary font-bold">CONFIRMED</span>
              </div>
              <div className="mt-space-sm">
                <span className="font-body-sm text-body-sm text-on-surface-variant block">
                  Final Package Total
                </span>
                <span className="font-currency-display text-currency-display text-on-surface font-bold tracking-tight">
                  {formatINR(total)}
                </span>
              </div>
              <p className="font-body-sm text-body-sm text-on-surface-variant/80 mt-1">
                All flights, accommodations, intercity transit &amp; activities locked into package record.
              </p>
            </div>
            <div className="pt-space-md flex items-center gap-space-sm text-on-surface-variant font-body-sm text-body-sm">
              <span className="material-symbols-outlined text-[18px] text-primary">verified</span>
              <span>10-Digit Audit Trail Registered</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Grid: Dossier Stream vs Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-lg items-start">
        {/* Left Column (65%) */}
        <div className="lg:col-span-8 flex flex-col gap-space-lg">
          {/* Traveler Information Card */}
          <div className="bg-surface-container-lowest rounded-xl shadow-sm p-space-lg">
            <div className="flex items-center justify-between mb-space-md">
              <div className="flex items-center gap-space-xs">
                <span className="material-symbols-outlined text-primary text-[22px]">group</span>
                <h2 className="font-headline-lg text-headline-lg text-on-surface">
                  Traveler Manifest &amp; Party Composition
                </h2>
              </div>
              <span className="font-label-sm text-label-sm uppercase bg-surface-container-low text-primary px-space-sm py-1 rounded-full font-semibold">
                {travelers.adults + travelers.children} Passengers
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-space-md">
              {/* Primary Traveler */}
              <div className="bg-surface-container-low rounded-lg p-space-md flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-space-xs">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-primary font-bold">
                      Primary Traveler
                    </span>
                    <span className="inline-flex items-center gap-1 font-label-sm text-label-sm text-on-surface-variant">
                      <span className="w-1.5 h-1.5 rounded-full bg-primary"></span> Adult
                    </span>
                  </div>
                  <h3 className="font-headline-md text-headline-md text-on-surface">
                    {reservation.customer_name || 'Guest Traveler'}
                  </h3>
                  <div className="mt-space-sm space-y-1 font-body-md text-body-md text-on-surface-variant">
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-[18px]">mail</span>
                      <span>{reservation.customer_email || 'traveler@example.com'}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Accompanied Travelers */}
              <div className="bg-surface-container-low rounded-lg p-space-md flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-space-xs">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-bold">
                      Party Details
                    </span>
                    <span className="font-label-sm text-label-sm text-on-surface-variant">
                      {travelers.adults} Adults
                      {travelers.children > 0 ? `, ${travelers.children} Children` : ''}
                    </span>
                  </div>
                  <div className="space-y-space-sm mt-space-xs">
                    <div className="flex items-center justify-between bg-surface-container-lowest p-space-sm rounded">
                      <div>
                        <div className="font-headline-sm text-headline-sm text-on-surface">
                          Adult Travelers
                        </div>
                        <div className="font-body-sm text-body-sm text-on-surface-variant">
                          {travelers.adults} Adults • Full Fare Allocation
                        </div>
                      </div>
                      <span className="material-symbols-outlined text-primary text-[18px]">check</span>
                    </div>
                    {travelers.children > 0 && (
                      <div className="flex items-center justify-between bg-surface-container-lowest p-space-sm rounded">
                        <div>
                          <div className="font-headline-sm text-headline-sm text-on-surface">
                            Child Travelers
                          </div>
                          <div className="font-body-sm text-body-sm text-on-surface-variant">
                            {travelers.children} Child ({travelers.child_ages?.length ? `age ${travelers.child_ages.join(', ')}` : ''})
                          </div>
                        </div>
                        <span className="material-symbols-outlined text-primary text-[18px]">check</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Complete Itinerary Ledger */}
          <div className="bg-surface-container-lowest rounded-xl shadow-sm p-space-lg flex flex-col gap-space-lg">
            <div>
              <h2 className="font-headline-lg text-headline-lg text-on-surface">
                Confirmed Itinerary Items
              </h2>
              <p className="font-body-md text-body-md text-on-surface-variant">
                Complete schedule of flights, accommodations, transfers, and curated excursions.
              </p>
            </div>

            {/* Flights */}
            {flights.length > 0 && (
              <div className="flex flex-col gap-space-sm">
                <div className="flex items-center gap-space-xs font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">
                  <span className="material-symbols-outlined text-[18px] text-primary">
                    flight_takeoff
                  </span>
                  <span>Flight Allocations</span>
                </div>
                {flights.map((item, idx) => (
                  <ItemRow key={idx} item={item} readOnly />
                ))}
              </div>
            )}

            {/* Stays */}
            {hotels.length > 0 && (
              <div className="flex flex-col gap-space-sm">
                <div className="flex items-center gap-space-xs font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">
                  <span className="material-symbols-outlined text-[18px] text-primary">hotel</span>
                  <span>Accommodations</span>
                </div>
                {hotels.map((item, idx) => (
                  <ItemRow key={idx} item={item} readOnly />
                ))}
              </div>
            )}

            {/* Transfers */}
            {transfers.length > 0 && (
              <div className="flex flex-col gap-space-sm">
                <div className="flex items-center gap-space-xs font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">
                  <span className="material-symbols-outlined text-[18px] text-primary">
                    directions_subway
                  </span>
                  <span>Ground Logistics &amp; Transfers</span>
                </div>
                {transfers.map((item, idx) => (
                  <ItemRow key={idx} item={item} readOnly />
                ))}
              </div>
            )}

            {/* Attractions */}
            {attractions.length > 0 && (
              <div className="flex flex-col gap-space-sm">
                <div className="flex items-center gap-space-xs font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">
                  <span className="material-symbols-outlined text-[18px] text-primary">
                    local_activity
                  </span>
                  <span>Curated City Experiences</span>
                </div>
                {attractions.map((item, idx) => (
                  <ItemRow key={idx} item={item} readOnly />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column (35%): Sticky Cost Summary */}
        <div className="lg:col-span-4 flex flex-col gap-space-lg lg:sticky lg:top-20">
          <div className="bg-surface-container-lowest rounded-xl shadow-sm p-space-lg flex flex-col gap-space-md">
            <div className="flex items-center justify-between">
              <h3 className="font-headline-md text-headline-md text-on-surface">Cost Breakdown</h3>
              <span className="font-label-sm text-label-sm text-primary bg-primary/10 px-2 py-0.5 rounded font-semibold">
                Locked &amp; Confirmed
              </span>
            </div>

            <div className="space-y-space-sm font-body-md text-body-md text-on-surface-variant">
              <div className="flex justify-between items-center">
                <span>Flights</span>
                <span className="font-currency-md text-on-surface font-medium">
                  {formatINR(flights.reduce((s, it) => s + (it.price_inr ?? it.price ?? 0), 0))}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span>Accommodations</span>
                <span className="font-currency-md text-on-surface font-medium">
                  {formatINR(hotels.reduce((s, it) => s + (it.price_inr ?? it.price ?? 0), 0))}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span>Transfers</span>
                <span className="font-currency-md text-on-surface font-medium">
                  {formatINR(transfers.reduce((s, it) => s + (it.price_inr ?? it.price ?? 0), 0))}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span>Attractions &amp; Activities</span>
                <span className="font-currency-md text-on-surface font-medium">
                  {formatINR(attractions.reduce((s, it) => s + (it.price_inr ?? it.price ?? 0), 0))}
                </span>
              </div>
            </div>

            <div className="bg-surface-container-low p-space-md rounded-lg flex items-center justify-between">
              <span className="font-headline-sm text-headline-sm text-on-surface">Net Total</span>
              <span className="font-currency-display text-currency-display text-primary font-bold">
                {formatINR(total)}
              </span>
            </div>

            <div className="flex flex-col gap-space-xs text-body-sm text-body-sm text-on-surface-variant">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px] text-primary">check</span>
                <span>Fixed internal reservation quote</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-[16px] text-primary">check</span>
                <span>Reference #{ref10} archived in central database</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
