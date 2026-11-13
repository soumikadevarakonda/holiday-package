import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ItemRow } from '../package/ItemRow';
import { TravelTips } from '../package/TravelTips';
import { Icon } from '../common/Icon';
import { formatINR, formatDate, formatWeekdayDate } from '../../utils/format';
import type { ReservationResponse, PackageItem } from '../../api/types';

interface ReservationSummaryProps {
  reservation: ReservationResponse;
}

/** Booking confirmation: reference, who/when, the plan day by day and the price. */
export const ReservationSummary: React.FC<ReservationSummaryProps> = ({ reservation }) => {
  const [copied, setCopied] = useState(false);
  const snap = reservation.snapshot || ({} as ReservationResponse['snapshot']);
  const items: PackageItem[] = reservation.items || snap.items || [];
  const t = snap.travelers || { adults: 0, children: 0, child_ages: [] };
  const ref = reservation.reference || reservation.reservation_reference || '';
  const total = reservation.total_price || snap.total_inr || 0;
  const totals = snap.totals;
  const plan = (snap.cities || []).map((c) => `${c} ${snap.nights_per_city?.[c] ?? ''}N`);

  // Group by the date each item starts (the arrival flight that departs the night before goes on day 1)
  const days = useMemo(() => {
    const groups = new Map<string, PackageItem[]>();
    const sorted = [...items].sort((a, b) => (a.start || '').localeCompare(b.start || ''));
    sorted.forEach((it) => {
      let d = (it.start || '').slice(0, 10);
      if (snap.start_date && d < snap.start_date) d = snap.start_date;
      groups.set(d, [...(groups.get(d) || []), it]);
    });
    return [...groups.entries()];
  }, [items, snap.start_date]);

  const copy = () => {
    if (!ref) return;
    navigator.clipboard?.writeText(ref).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const rows = [
    ['Flights', totals?.flights],
    ['Stays', totals?.hotels],
    ['Transfers', totals?.transfers],
    ['Activities', totals?.attractions],
  ] as const;

  return (
    <div className="flex flex-col gap-6">
      {/* Confirmation banner */}
      <section className="bg-white rounded-lg shadow-card overflow-hidden">
        <div className="bg-ok text-white px-5 py-4 flex items-center gap-3">
          <Icon name="check_circle" filled className="!text-3xl" />
          <div>
            <h1 className="text-xl sm:text-2xl font-bold">Your trip is booked!</h1>
            <p className="text-white/90 text-sm">
              {reservation.customer_name ? `Thanks, ${reservation.customer_name}. ` : ''}
              {reservation.customer_email ? `Confirmation details are under ${reservation.customer_email}.` : ''}
            </p>
          </div>
        </div>
        <div className="p-5 grid grid-cols-1 sm:grid-cols-3 gap-5">
          <div>
            <div className="text-xs text-ink-mute">Booking number</div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-extrabold tracking-wider tabular-nums text-ink">{ref}</span>
              <button
                type="button"
                onClick={copy}
                className="no-print h-8 px-2 rounded-md text-sm font-semibold text-brand hover:bg-brand-light flex items-center gap-1"
                aria-label="Copy booking number"
              >
                <Icon name={copied ? 'check' : 'content_copy'} className="!text-base" />
                {copied ? 'Copied' : 'Copy'}
              </button>
            </div>
          </div>
          <div>
            <div className="text-xs text-ink-mute">Trip</div>
            <div className="font-semibold text-ink">{snap.country}</div>
            <div className="text-sm text-ink-soft">{plan.join(' → ')}</div>
          </div>
          <div>
            <div className="text-xs text-ink-mute">Dates</div>
            <div className="font-semibold text-ink">
              {formatDate(snap.start_date)} – {formatDate(snap.end_date)}
            </div>
            <div className="text-sm text-ink-soft">
              {t.adults} adult{t.adults === 1 ? '' : 's'}
              {t.children ? `, ${t.children} child${t.children === 1 ? '' : 'ren'}` : ''}
            </div>
          </div>
        </div>
        <div className="no-print px-5 pb-5 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => window.print()}
            className="h-10 px-4 rounded-md border border-brand text-brand font-semibold hover:bg-brand-light flex items-center gap-1"
          >
            <Icon name="print" /> Print
          </button>
          <a
            href={`/api/packages/${encodeURIComponent(reservation.package_id)}/export`}
            target="_blank"
            rel="noreferrer"
            className="h-10 px-4 rounded-md border border-brand text-brand font-semibold hover:bg-brand-light flex items-center gap-1"
          >
            <Icon name="download" /> Download trip
          </a>
          <Link to="/" className="h-10 px-4 rounded-md text-brand font-semibold hover:bg-brand-light flex items-center gap-1">
            <Icon name="add" /> Plan another trip
          </Link>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6 items-start">
        {/* Itinerary */}
        <section aria-labelledby="itinerary" className="flex flex-col gap-5 min-w-0">
          <h2 id="itinerary" className="text-xl font-bold text-ink">
            Your itinerary
          </h2>
          {days.map(([date, dayItems], i) => (
            <div key={date}>
              <h3 className="font-bold text-ink mb-2">
                Day {i + 1} · <span className="font-normal text-ink-mute">{formatWeekdayDate(date)}</span>
              </h3>
              <div className="flex flex-col gap-2">
                {dayItems.map((it) => (
                  <ItemRow key={it.item_id} item={it} readOnly />
                ))}
              </div>
            </div>
          ))}
        </section>

        {/* Price + traveler details */}
        <aside className="flex flex-col gap-4">
          <section className="bg-white rounded-lg shadow-card p-4">
            <h2 className="font-bold text-ink">Price paid</h2>
            {totals && (
              <dl className="mt-3 space-y-1.5 text-sm">
                {rows.map(([label, v]) => (
                  <div key={label} className="flex justify-between">
                    <dt className="text-ink-soft">{label}</dt>
                    <dd className="tabular-nums">{v === 0 ? 'Free' : formatINR(v)}</dd>
                  </div>
                ))}
              </dl>
            )}
            <div className="mt-3 pt-3 border-t border-line flex justify-between items-end">
              <span className="font-semibold">Total</span>
              <span className="text-2xl font-extrabold tabular-nums">{formatINR(total)}</span>
            </div>
          </section>
          <section className="bg-white rounded-lg shadow-card p-4 text-sm">
            <h2 className="font-bold text-ink text-base">Lead traveler</h2>
            <p className="mt-2 text-ink">{reservation.customer_name}</p>
            <p className="text-ink-soft">{reservation.customer_email}</p>
            <h2 className="font-bold text-ink text-base mt-4">Travelers</h2>
            <p className="mt-1 text-ink-soft">
              {t.adults} adult{t.adults === 1 ? '' : 's'}
              {t.children ? `, ${t.children} child${t.children === 1 ? '' : 'ren'} (age ${t.child_ages?.join(', ')})` : ''}
            </p>
            {reservation.created_at && <p className="mt-4 text-xs text-ink-mute">Booked on {formatDate(reservation.created_at)}</p>}
          </section>
          <TravelTips pkg={snap} items={items} />
        </aside>
      </div>
    </div>
  );
};