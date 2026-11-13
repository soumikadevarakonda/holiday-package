import React, { useState } from 'react';

interface LookupBoxProps {
  onLookup: (reference: string) => void;
  loading?: boolean;
  notFoundRef?: string | null;
  activeRef?: string | null;
}

export const LookupBox: React.FC<LookupBoxProps> = ({
  onLookup,
  loading = false,
  notFoundRef = null,
  activeRef = null,
}) => {
  const [refInput, setRefInput] = useState<string>(notFoundRef || '');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = refInput.trim();
    if (clean) {
      onLookup(clean);
    }
  };

  return (
    <div className="mt-space-xl bg-surface-container-lowest rounded-xl shadow-sm p-space-lg lg:p-space-xl flex flex-col gap-space-lg">
      <div>
        <span className="font-label-sm text-label-sm uppercase tracking-wider text-primary font-bold">
          Portal Services
        </span>
        <h2 className="font-headline-xl text-headline-xl text-on-surface mt-1">
          Retrieve an Existing Reservation
        </h2>
        <p className="font-body-md text-body-md text-on-surface-variant">
          Lookup past itineraries, access confirmed records, or synchronize booking references from our reservation database.
        </p>
      </div>

      {/* Lookup Form */}
      <form
        onSubmit={handleSubmit}
        className="grid grid-cols-1 md:grid-cols-12 gap-space-sm items-center bg-surface-container-low p-space-md rounded-xl"
      >
        <div className="md:col-span-9 flex flex-col gap-1">
          <label
            className="font-label-sm text-label-sm text-on-surface-variant uppercase font-semibold"
            htmlFor="bookingRef"
          >
            10-Digit Reservation Reference
          </label>
          <div className="relative">
            <span className="material-symbols-outlined absolute left-3 top-3 text-[18px] text-outline-variant">
              tag
            </span>
            <input
              id="bookingRef"
              type="text"
              maxLength={10}
              placeholder="e.g. 7829410928"
              value={refInput}
              onChange={(e) => setRefInput(e.target.value.replace(/[^0-9]/g, ''))}
              required
              className="w-full bg-surface-container-lowest h-11 pl-10 pr-4 rounded font-currency-md text-currency-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary shadow-sm tracking-widest"
            />
          </div>
        </div>

        <div className="md:col-span-3 flex flex-col justify-end pt-1">
          <button
            type="submit"
            disabled={loading || refInput.trim().length !== 10}
            className="h-11 bg-primary text-on-primary hover:bg-secondary transition-all rounded font-headline-sm text-headline-sm flex items-center justify-center gap-2 shadow-sm disabled:opacity-50 cursor-pointer"
          >
            <span className="material-symbols-outlined text-[18px]">search</span>
            <span>{loading ? 'Searching...' : 'Find Reservation'}</span>
          </button>
        </div>
      </form>

      {/* Reservation Not Found Alert Box */}
      {notFoundRef && (
        <div className="bg-error-container/30 rounded-xl p-space-lg flex flex-col md:flex-row items-start gap-space-md transition-all">
          <div className="w-10 h-10 rounded-full bg-error text-on-error flex items-center justify-center shrink-0">
            <span className="material-symbols-outlined text-[20px]">warning</span>
          </div>
          <div className="flex flex-col gap-1 flex-1">
            <div className="flex flex-wrap items-center justify-between gap-space-sm">
              <h4 className="font-headline-md text-headline-md text-error">
                Reservation Not Found
              </h4>
              <span className="font-label-sm text-label-sm uppercase font-semibold bg-error/10 text-error px-2 py-0.5 rounded">
                Error Code: ERR_RES_EMPTY
              </span>
            </div>
            <p className="font-body-md text-body-md text-on-surface-variant mt-1">
              No booking matches reference{' '}
              <strong className="text-on-surface font-currency-md">#{notFoundRef}</strong>. Please check your 10-digit reservation number and try again.
            </p>
          </div>
        </div>
      )}

      {/* Active Record Located Indicator */}
      {activeRef && !notFoundRef && (
        <div className="bg-primary/10 rounded-xl p-space-lg flex flex-col md:flex-row items-start gap-space-md transition-all">
          <div className="w-10 h-10 rounded-full bg-primary text-on-primary flex items-center justify-center shrink-0">
            <span className="material-symbols-outlined text-[20px]">check_circle</span>
          </div>
          <div className="flex flex-col gap-1 flex-1">
            <h4 className="font-headline-md text-headline-md text-primary">
              Reservation Located &amp; Active
            </h4>
            <p className="font-body-md text-body-md text-on-surface-variant">
              Booking record <strong className="font-currency-md font-bold text-on-surface">{activeRef}</strong> is currently displayed above.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
