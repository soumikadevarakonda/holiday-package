import React from 'react';
import { formatINR } from '../../utils/format';
import type { Totals, PackageItem } from '../../api/types';

interface PriceBreakdownProps {
  totals?: Totals;
  items?: PackageItem[];
  totalPrice?: number;
  travelerCount?: number;
  onConfirm: () => void;
  confirming?: boolean;
}

export const PriceBreakdown: React.FC<PriceBreakdownProps> = ({
  totals,
  items = [],
  totalPrice,
  travelerCount = 3,
  onConfirm,
  confirming = false,
}) => {
  // Compute categorized sums if totals object is incomplete
  let flightSum = totals?.flights || 0;
  let hotelSum = totals?.hotels || 0;
  let transferSum = totals?.transfers || 0;
  let attractionSum = totals?.attractions || 0;

  if (!totals?.flights && !totals?.hotels && items.length > 0) {
    flightSum = items
      .filter((it) => it.type === 'flight')
      .reduce((sum, it) => sum + (it.price_inr ?? it.price ?? 0), 0);
    hotelSum = items
      .filter((it) => it.type === 'hotel')
      .reduce((sum, it) => sum + (it.price_inr ?? it.price ?? 0), 0);
    transferSum = items
      .filter((it) => it.type === 'transfer')
      .reduce((sum, it) => sum + (it.price_inr ?? it.price ?? 0), 0);
    attractionSum = items
      .filter((it) => it.type === 'attraction')
      .reduce((sum, it) => sum + (it.price_inr ?? it.price ?? 0), 0);
  }

  const grandTotal =
    totalPrice || totals?.total || flightSum + hotelSum + transferSum + attractionSum || 0;

  const perPerson = Math.round(grandTotal / (travelerCount || 1));

  return (
    <div className="lg:col-span-4 flex flex-col gap-space-lg">
      <div className="sticky top-20 flex flex-col gap-space-md">
        {/* Main Manifest Card */}
        <div className="bg-surface-container-lowest rounded-xl shadow-lg p-space-lg flex flex-col gap-space-md">
          <div className="flex items-center justify-between pb-space-xs">
            <div>
              <h3 className="font-headline-md text-headline-md text-on-surface font-bold">
                Holiday Manifest
              </h3>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                Live Consolidated Calculation
              </p>
            </div>
            <span className="px-2.5 py-1 bg-surface-container-low text-primary rounded-full font-label-sm text-label-sm font-semibold">
              ALL-INCLUSIVE
            </span>
          </div>

          {/* Price Breakdown Line Items */}
          <div className="flex flex-col gap-space-sm pt-space-xs font-body-md text-body-md">
            <div className="flex items-center justify-between">
              <span className="text-on-surface-variant flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[16px] text-primary">flight</span>
                Flights (Return Scheduled)
              </span>
              <span className="font-currency-md text-currency-md font-medium text-on-surface">
                {formatINR(flightSum)}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-on-surface-variant flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[16px] text-primary">apartment</span>
                Stays &amp; Accommodations
              </span>
              <span className="font-currency-md text-currency-md font-medium text-on-surface">
                {formatINR(hotelSum)}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-on-surface-variant flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[16px] text-primary">
                  directions_subway
                </span>
                Transfers &amp; Ground Transit
              </span>
              <span className="font-currency-md text-currency-md font-medium text-on-surface">
                {formatINR(transferSum)}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-on-surface-variant flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[16px] text-primary">
                  local_activity
                </span>
                Curated Experiences
              </span>
              <span className="font-currency-md text-currency-md font-medium text-on-surface">
                {formatINR(attractionSum)}
              </span>
            </div>

            <div className="flex items-center justify-between text-on-surface-variant">
              <span className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[16px] text-outline">receipt</span>
                GST, Fuel &amp; Surcharges
              </span>
              <span className="font-label-md text-label-md font-semibold text-primary">Included</span>
            </div>
          </div>

          <div className="h-px w-full bg-surface-container-high my-space-xs"></div>

          {/* Grand Dynamic Total */}
          <div className="flex items-baseline justify-between">
            <div>
              <span className="font-label-sm text-label-sm uppercase text-on-surface-variant font-bold">
                Total Payable (INR)
              </span>
              <div className="font-currency-display text-display-lg text-primary font-bold">
                {formatINR(grandTotal)}
              </div>
            </div>
            <div className="text-right">
              <span className="font-label-sm text-label-sm text-primary font-semibold">
                TCS compliant
              </span>
              <div className="font-body-sm text-body-sm text-on-surface-variant">
                {formatINR(perPerson)} / person
              </div>
            </div>
          </div>

          {/* Primary Action */}
          <button
            type="button"
            onClick={onConfirm}
            disabled={confirming}
            className="w-full py-3.5 rounded-lg bg-primary hover:bg-primary-container text-on-primary font-headline-sm text-headline-sm font-semibold flex items-center justify-center gap-2 transition-all shadow-md active:scale-95 disabled:opacity-60 cursor-pointer"
          >
            <span className="material-symbols-outlined text-[22px]">lock</span>
            <span>{confirming ? 'Locking Price...' : 'Lock Price & Confirm Holiday'}</span>
          </button>
          <p className="font-body-sm text-body-sm text-center text-on-surface-variant">
            Instant booking confirmation with 24-hour free cancellation grace period.
          </p>
        </div>

        {/* Trust & Concierge Guarantees */}
        <div className="bg-surface-container-lowest rounded-xl p-space-md shadow-sm flex flex-col gap-2">
          <div className="flex items-center gap-2 text-on-surface font-label-md text-label-md font-semibold">
            <span className="material-symbols-outlined text-primary text-[18px]">verified</span>
            <span>Build My Holiday Assurance</span>
          </div>
          <p className="font-body-sm text-body-sm text-on-surface-variant">
            Every package is audited for seamless inter-modal connections with at least 90 minutes buffer time between arrivals and check-ins.
          </p>
        </div>
      </div>
    </div>
  );
};
