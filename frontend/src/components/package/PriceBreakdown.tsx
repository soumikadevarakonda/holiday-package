import React from 'react';
import { BudgetBar } from './BudgetBar';
import { Icon } from '../common/Icon';
import { formatINR } from '../../utils/format';
import type { Totals, PackageItem } from '../../api/types';

interface PriceBreakdownProps {
  totals?: Totals;
  items?: PackageItem[];
  totalPrice?: number;
  travelerCount?: number;
  onConfirm: () => void;
  confirming?: boolean;
  booked?: boolean;
}

/** Sticky price summary with the book button. */
export const PriceBreakdown: React.FC<PriceBreakdownProps> = ({
  totals,
  items = [],
  totalPrice,
  travelerCount = 1,
  onConfirm,
  confirming = false,
  booked = false,
}) => {
  const count = (type: string) => items.filter((i) => i.type === type).length;
  const rows = [
    { label: 'Flights', icon: 'flight', amount: totals?.flights ?? 0, n: count('flight') },
    { label: 'Stays', icon: 'hotel', amount: totals?.hotels ?? 0, n: count('hotel') },
    { label: 'Transfers', icon: 'directions_bus', amount: totals?.transfers ?? 0, n: count('transfer') },
    { label: 'Activities', icon: 'attractions', amount: totals?.attractions ?? 0, n: count('attraction') },
  ];
  const total = totalPrice ?? totals?.total ?? rows.reduce((s, r) => s + r.amount, 0);

  return (
    <aside className="lg:sticky lg:top-4 flex flex-col gap-3" aria-label="Price summary">
      <div className="bg-white rounded-lg shadow-card border border-line overflow-hidden">
        <div className="p-4">
          <h2 className="text-lg font-bold text-ink">Price summary</h2>
          <dl className="mt-3 space-y-2 text-sm">
            {rows.map((r) => (
              <div key={r.label} className="flex items-center justify-between">
                <dt className="text-ink-soft flex items-center gap-2">
                  <Icon name={r.icon} className="!text-base text-ink-mute" />
                  {r.label}
                  <span className="text-ink-mute">({r.n})</span>
                </dt>
                <dd className="tabular-nums text-ink">{r.amount === 0 && r.n > 0 ? 'Free' : formatINR(r.amount)}</dd>
              </div>
            ))}
          </dl>
        </div>
        <div className="bg-brand-light p-4">
          <div className="flex items-end justify-between">
            <span className="font-semibold text-ink">Total</span>
            <span className="text-2xl font-extrabold text-ink tabular-nums">{formatINR(total)}</span>
          </div>
          <p className="text-right text-xs text-ink-mute mt-0.5">
            {formatINR(Math.round(total / (travelerCount || 1)))} per traveler · includes taxes
          </p>
          {totals?.budget ? <BudgetBar total={total} budget={totals.budget} className="mt-3" /> : null}
        </div>
        <div className="p-4">
          <button
            type="button"
            onClick={onConfirm}
            disabled={confirming}
            className={`w-full h-12 rounded-md font-bold text-white flex items-center justify-center gap-2 disabled:opacity-60 ${
              booked ? 'bg-ok hover:brightness-95' : 'bg-brand hover:bg-brand-dark'
            }`}
          >
            <Icon name={booked ? 'confirmation_number' : 'lock'} />
            {confirming ? 'Please wait…' : booked ? 'View your booking' : 'Book this trip'}
          </button>
          {!booked && (
            <ul className="mt-3 space-y-1 text-xs text-ink-soft">
              <li className="flex items-center gap-1.5">
                <Icon name="check" className="!text-sm text-ok" /> One booking number for everything
              </li>
              <li className="flex items-center gap-1.5">
                <Icon name="check" className="!text-sm text-ok" /> Seats and rooms are checked when you book
              </li>
            </ul>
          )}
        </div>
      </div>
    </aside>
  );
};
