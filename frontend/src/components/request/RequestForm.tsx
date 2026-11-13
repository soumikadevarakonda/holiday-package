import React, { useEffect, useRef, useState } from 'react';
import { ChildAgesInput, Stepper } from './ChildAgesInput';
import { Icon } from '../common/Icon';
import { calculateReturnDate } from '../../utils/format';
import type { TripRequest, MetaResponse } from '../../api/types';

interface RequestFormProps {
  meta: MetaResponse | null;
  onSubmit: (payload: TripRequest) => Promise<void>;
  loading: boolean;
  initialValues?: Partial<TripRequest>;
  /** Field errors from the backend (422), keyed by field name. */
  serverErrors?: Record<string, string>;
}

const FALLBACK_FROM = [
  { code: 'BLR', city: 'Bengaluru' },
  { code: 'BOM', city: 'Mumbai' },
  { code: 'DEL', city: 'Delhi' },
  { code: 'MAA', city: 'Chennai' },
];
const FALLBACK_TO = [
  { name: 'Japan', cities: ['Tokyo', 'Kyoto', 'Osaka'] },
  { name: 'United Arab Emirates', cities: ['Dubai', 'Abu Dhabi'] },
];
const MAX_TRAVELERS = 9;

/** One-line search bar: from, to, dates, travelers, budget. */
export const RequestForm: React.FC<RequestFormProps> = ({ meta, onSubmit, loading, initialValues, serverErrors = {} }) => {
  const [departureCity, setDepartureCity] = useState('BLR');
  const [destinationCountry, setDestinationCountry] = useState('Japan');
  const [startDate, setStartDate] = useState('2027-04-10');
  const [nights, setNights] = useState(6);
  const [adults, setAdults] = useState(2);
  const [children, setChildren] = useState(0);
  const [childAges, setChildAges] = useState<number[]>([]);
  const [budgetStr, setBudgetStr] = useState('3,50,000');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [travelersOpen, setTravelersOpen] = useState(false);
  const [compare, setCompare] = useState(true);
  const travelersRef = useRef<HTMLDivElement>(null);

  // Options from /api/meta (with a fallback so the form works even before it loads)
  const fromList = (meta?.departure_cities?.length ? meta.departure_cities : FALLBACK_FROM).map((c: any) =>
    typeof c === 'string' ? { code: c, city: c } : { code: c.airport || c.code || c.city, city: c.city || c.name || c.code }
  );
  const toList = (meta?.destination_countries?.length ? meta.destination_countries : FALLBACK_TO).map((c: any) =>
    typeof c === 'string' ? { name: c, cities: [] as string[] } : { name: c.name || c.country, cities: c.cities || [] }
  );

  useEffect(() => {
    const v = initialValues;
    if (!v) return;
    if (v.departure_city) {
      const match = fromList.find(
        (c) => c.code === v.departure_city || c.city.toLowerCase() === String(v.departure_city).toLowerCase()
      );
      setDepartureCity(match ? match.code : v.departure_city);
    }
    if (v.destination_country) {
      const d = String(v.destination_country).toLowerCase();
      const match = toList.find((c) => c.name.toLowerCase() === d || (d === 'uae' && c.name.includes('Emirates')));
      setDestinationCountry(match ? match.name : v.destination_country);
    }
    if (v.start_date) setStartDate(v.start_date);
    if (v.nights !== undefined) setNights(v.nights);
    if (v.adults !== undefined) setAdults(v.adults);
    if (v.child_ages) {
      setChildAges(v.child_ages);
      setChildren(v.child_ages.length);
    } else if (v.children !== undefined) setChildren(v.children);
    if (v.budget !== undefined) setBudgetStr(Math.round(v.budget).toLocaleString('en-IN'));
    setErrors({});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialValues]);

  // Close the travelers pop-over on outside click / Escape
  useEffect(() => {
    if (!travelersOpen) return;
    const onDown = (e: MouseEvent) => {
      if (travelersRef.current && !travelersRef.current.contains(e.target as Node)) setTravelersOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setTravelersOpen(false);
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [travelersOpen]);

  const budget = parseInt(budgetStr.replace(/[^0-9]/g, ''), 10) || 0;
  const returnDate = calculateReturnDate(startDate, nights);
  const cities = toList.find((c) => c.name === destinationCountry)?.cities || [];

  const validate = () => {
    const e: Record<string, string> = {};
    if (!startDate || startDate < '2027-04-01' || startDate > '2027-04-17') e.start_date = 'Choose a date from 1 to 17 April 2027';
    else {
      const ret = new Date(startDate);
      ret.setDate(ret.getDate() + nights);
      if (ret > new Date('2027-04-20')) e.nights = 'You must be back by 20 April 2027 — choose fewer nights or an earlier date';
    }
    if (adults + children > MAX_TRAVELERS) e.travelers = `At most ${MAX_TRAVELERS} travelers`;
    if (budget <= 0) e.budget = 'Enter your total budget';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const submit = (ev: React.FormEvent) => {
    ev.preventDefault();
    if (!validate()) return;
    onSubmit({
      departure_city: departureCity,
      destination_country: destinationCountry,
      start_date: startDate,
      nights,
      adults,
      children,
      child_ages: childAges.slice(0, children),
      budget,
      mode: compare ? 'three' : 'default',
    });
  };

  const allErrors = { ...serverErrors, ...errors };
  const travelersLabel = `${adults} adult${adults > 1 ? 's' : ''}${
    children ? ` · ${children} child${children > 1 ? 'ren' : ''}` : ''
  }`;

  const field = 'flex items-center gap-2 bg-white rounded-md px-3 h-14 min-w-0';
  const inputCls = 'w-full bg-transparent text-ink text-[15px] font-medium focus:outline-none';
  const caption = 'block text-[11px] font-semibold uppercase tracking-wide text-ink-mute leading-none mb-1';

  return (
    <form onSubmit={submit} noValidate>
      <div className="bg-sun p-1 rounded-lg shadow-pop grid grid-cols-1 md:grid-cols-2 lg:grid-cols-[1.35fr_1.15fr_1.75fr_1fr_0.95fr_auto] gap-1">
        {/* From */}
        <label className={field}>
          <Icon name="flight_takeoff" className="text-ink-mute" />
          <span className="min-w-0 flex-1">
            <span className={caption}>Leaving from</span>
            <select value={departureCity} onChange={(e) => setDepartureCity(e.target.value)} className={inputCls}>
              {fromList.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.city} ({c.code})
                </option>
              ))}
            </select>
          </span>
        </label>

        {/* To */}
        <label className={field}>
          <Icon name="location_on" className="text-ink-mute" />
          <span className="min-w-0 flex-1">
            <span className={caption}>Going to</span>
            <select value={destinationCountry} onChange={(e) => setDestinationCountry(e.target.value)} className={inputCls}>
              {toList.map((c) => (
                <option key={c.name} value={c.name}>
                  {c.name}
                </option>
              ))}
            </select>
          </span>
        </label>

        {/* Dates */}
        <div className={`${field} gap-3`}>
          <Icon name="calendar_month" className="text-ink-mute" />
          <label className="min-w-0 flex-1">
            <span className={caption}>Start date</span>
            <input
              type="date"
              min="2027-04-01"
              max="2027-04-17"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className={inputCls}
            />
          </label>
          <label className="w-16 shrink-0 border-l border-line pl-3">
            <span className={caption}>Nights</span>
            <select value={nights} onChange={(e) => setNights(Number(e.target.value))} className={inputCls}>
              {Array.from({ length: 8 }, (_, i) => i + 3).map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>
        </div>

        {/* Travelers */}
        <div className="relative" ref={travelersRef}>
          <button
            type="button"
            onClick={() => setTravelersOpen(!travelersOpen)}
            className={`${field} w-full text-left`}
            aria-expanded={travelersOpen}
            aria-haspopup="dialog"
          >
            <Icon name="group" className="text-ink-mute" />
            <span className="min-w-0 flex-1">
              <span className={caption}>Travelers</span>
              <span className="block truncate text-[15px] font-medium text-ink">{travelersLabel}</span>
            </span>
            <Icon name={travelersOpen ? 'expand_less' : 'expand_more'} className="text-ink-mute" />
          </button>
          {travelersOpen && (
            <div
              role="dialog"
              aria-label="Travelers"
              className="absolute z-30 mt-2 left-0 right-0 lg:left-auto lg:w-80 bg-white rounded-lg shadow-pop border border-line p-4"
            >
              <Stepper label="Adults" hint="Age 18+" value={adults} min={1} max={MAX_TRAVELERS - children} onChange={setAdults} />
              <ChildAgesInput
                childrenCount={children}
                childAges={childAges}
                maxChildren={MAX_TRAVELERS - adults}
                onChange={(n, ages) => {
                  setChildren(n);
                  setChildAges(ages);
                }}
              />
              <button
                type="button"
                onClick={() => setTravelersOpen(false)}
                className="mt-2 w-full h-10 rounded-md border border-brand text-brand font-semibold hover:bg-brand-light"
              >
                Done
              </button>
            </div>
          )}
        </div>

        {/* Budget */}
        <label className={field}>
          <span className="text-ink-mute font-semibold">₹</span>
          <span className="min-w-0 flex-1">
            <span className={caption}>Total budget</span>
            <input
              inputMode="numeric"
              value={budgetStr}
              onChange={(e) => {
                const d = e.target.value.replace(/[^0-9]/g, '');
                setBudgetStr(d ? parseInt(d, 10).toLocaleString('en-IN') : '');
              }}
              placeholder="3,50,000"
              className={inputCls}
              aria-label="Total budget in rupees"
            />
          </span>
        </label>

        <button
          type="submit"
          disabled={loading}
          className="h-14 px-6 rounded-md bg-brand hover:bg-brand-dark text-white text-lg font-semibold flex items-center justify-center gap-2 disabled:opacity-70 md:col-span-2 lg:col-span-1"
        >
          {loading ? (
            <span className="w-5 h-5 rounded-full border-2 border-white/40 border-t-white animate-spin" />
          ) : (
            <Icon name="search" />
          )}
          {loading ? 'Building…' : 'Search'}
        </button>
      </div>

      {/* Helper line + errors */}
      <label className="mt-3 inline-flex items-center gap-2 text-sm font-medium text-white cursor-pointer">
        <input
          type="checkbox"
          checked={compare}
          onChange={(e) => setCompare(e.target.checked)}
          className="w-4 h-4 accent-sun"
        />
        Compare 3 options: cheapest, fastest and best rated
      </label>
      <div className="mt-2 text-sm text-white/90 flex flex-wrap gap-x-4 gap-y-1">
        <span>
          <Icon name="event" className="!text-base mr-1" />
          Back on {returnDate || '—'}
        </span>
        {cities.length > 0 && (
          <span>
            <Icon name="map" className="!text-base mr-1" />
            {nights >= 6
              ? `Up to ${Math.min(cities.length, Math.max(1, Math.floor(nights / 3)))} of ${cities.join(', ')}`
              : `One of ${cities.join(', ')}`}{' '}
            — we pick the best split
          </span>
        )}
        {budget > 0 && (
          <span>
            <Icon name="savings" className="!text-base mr-1" />≈ ₹{(budget / 100000).toFixed(budget % 100000 ? 2 : 0)} lakh
          </span>
        )}
      </div>
      {Object.keys(allErrors).length > 0 && (
        <ul className="mt-3 bg-white rounded-md border border-bad/40 p-3 text-sm text-bad space-y-1" role="alert">
          {Object.entries(allErrors).map(([k, m]) => (
            <li key={k} className="flex items-start gap-2">
              <Icon name="error" filled className="!text-base mt-0.5" />
              <span>{m}</span>
            </li>
          ))}
        </ul>
      )}
    </form>
  );
};
