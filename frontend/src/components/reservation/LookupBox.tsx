import React, { useEffect, useState } from 'react';
import { Icon } from '../common/Icon';

interface LookupBoxProps {
  onLookup: (reference: string) => void;
  loading?: boolean;
  notFoundRef?: string | null;
  activeRef?: string | null;
  compact?: boolean;
}

/** Find a booking by its 10-digit number. */
export const LookupBox: React.FC<LookupBoxProps> = ({ onLookup, loading = false, notFoundRef = null, compact = false }) => {
  const [value, setValue] = useState(notFoundRef || '');
  useEffect(() => setValue(notFoundRef || ''), [notFoundRef]);

  const clean = value.replace(/\D/g, '');
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (clean.length === 10) onLookup(clean);
  };

  return (
    <section className={`bg-white rounded-lg shadow-card ${compact ? 'p-4' : 'p-6 sm:p-8'}`} aria-labelledby="lookup-title">
      <h2 id="lookup-title" className={`${compact ? 'text-lg' : 'text-2xl'} font-bold text-ink`}>
        {compact ? 'Look up another booking' : 'Find your booking'}
      </h2>
      {!compact && <p className="text-ink-mute mt-1">Enter the 10-digit booking number you got when you booked.</p>}
      <form onSubmit={submit} className="mt-4 flex flex-col sm:flex-row gap-2">
        <label className="flex-1">
          <span className="sr-only">Booking number</span>
          <input
            inputMode="numeric"
            autoComplete="off"
            maxLength={12}
            value={value}
            onChange={(e) => setValue(e.target.value.replace(/[^\d ]/g, ''))}
            placeholder="e.g. 4829175036"
            className="w-full h-12 px-4 rounded-md border border-line text-lg tracking-widest tabular-nums focus:outline-none focus:ring-2 focus:ring-brand"
          />
        </label>
        <button
          type="submit"
          disabled={loading || clean.length !== 10}
          className="h-12 px-6 rounded-md bg-brand hover:bg-brand-dark text-white font-bold flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <Icon name="search" />
          {loading ? 'Searching…' : 'Find booking'}
        </button>
      </form>
      {value && clean.length !== 10 && <p className="mt-2 text-sm text-ink-mute">{clean.length}/10 digits</p>}
      {notFoundRef && (
        <p className="mt-4 p-3 rounded-md bg-bad-light text-sm text-ink flex items-start gap-2" role="alert">
          <Icon name="error" filled className="text-bad !text-lg" />
          <span>
            <strong>Reservation not found.</strong> No booking has the number {notFoundRef}. Check the digits and try again.
          </span>
        </p>
      )}
    </section>
  );
};
