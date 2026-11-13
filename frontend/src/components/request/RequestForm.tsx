import React, { useState, useEffect } from 'react';
import { ChildAgesInput } from './ChildAgesInput';
import { calculateReturnDate, formatINR } from '../../utils/format';
import type { TripRequest, MetaResponse } from '../../api/types';

interface RequestFormProps {
  meta: MetaResponse | null;
  onSubmit: (payload: TripRequest) => Promise<void>;
  loading: boolean;
  onApplyPreset?: (preset: 'golden' | 'hokkaido' | 'kansai') => void;
  initialValues?: Partial<TripRequest>;
}

export const RequestForm: React.FC<RequestFormProps> = ({
  meta,
  onSubmit,
  loading,
  initialValues,
}) => {
  const [departureCity, setDepartureCity] = useState<string>('BOM');
  const [destinationCountry, setDestinationCountry] = useState<string>('Japan');
  const [startDate, setStartDate] = useState<string>('2027-04-05');
  const [nights, setNights] = useState<number>(8);
  const [adults, setAdults] = useState<number>(2);
  const [children, setChildren] = useState<number>(1);
  const [childAges, setChildAges] = useState<number[]>([7]);
  const [budgetStr, setBudgetStr] = useState<string>('4,50,000');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Initialize or update from metadata or initialValues
  useEffect(() => {
    if (meta?.departure_cities && meta.departure_cities.length > 0) {
      const cityCodes = meta.departure_cities.map((c) =>
        typeof c === 'string' ? c : c.airport || c.code || c.city || ''
      );
      if (departureCity && !cityCodes.includes(departureCity)) {
        if (cityCodes[0]) setDepartureCity(cityCodes[0]);
      }
    }
  }, [meta]);

  useEffect(() => {
    if (initialValues) {
      if (initialValues.departure_city) setDepartureCity(initialValues.departure_city);
      if (initialValues.destination_country) setDestinationCountry(initialValues.destination_country);
      if (initialValues.start_date) setStartDate(initialValues.start_date);
      if (initialValues.nights !== undefined) setNights(initialValues.nights);
      if (initialValues.adults !== undefined) setAdults(initialValues.adults);
      if (initialValues.children !== undefined) setChildren(initialValues.children);
      if (initialValues.child_ages) setChildAges(initialValues.child_ages);
      if (initialValues.budget !== undefined) {
        setBudgetStr(Math.round(initialValues.budget).toLocaleString('en-IN'));
      }
    }
  }, [initialValues]);

  const rawBudget = parseInt(budgetStr.replace(/[^0-9]/g, ''), 10) || 0;

  // Budget adequacy gauge
  const gaugePercent = Math.min(100, Math.max(15, (rawBudget / 650000) * 100));
  let tierName = 'Comfort / 4-Star Tier';
  let tierClass =
    'px-2 py-0.5 rounded-full bg-primary-fixed text-on-primary-fixed font-label-sm text-label-sm uppercase font-semibold';
  if (rawBudget < 320000) {
    tierName = 'Economy / Compact Tier';
    tierClass =
      'px-2 py-0.5 rounded-full bg-surface-container-high text-on-surface-variant font-label-sm text-label-sm uppercase font-semibold';
  } else if (rawBudget > 520000) {
    tierName = 'Signature / 5-Star Luxury';
    tierClass =
      'px-2 py-0.5 rounded-full bg-tertiary-fixed text-on-tertiary-fixed font-label-sm text-label-sm uppercase font-semibold';
  }

  const adjustNights = (delta: number) => {
    const next = Math.max(3, Math.min(10, nights + delta));
    setNights(next);
  };

  const adjustAdults = (delta: number) => {
    const next = Math.max(1, Math.min(8, adults + delta));
    setAdults(next);
  };

  const handleBudgetChange = (val: string) => {
    const digits = val.replace(/[^0-9]/g, '');
    if (!digits) {
      setBudgetStr('');
      return;
    }
    const num = parseInt(digits, 10);
    setBudgetStr(num.toLocaleString('en-IN'));
  };

  const setRecommendedBudget = () => {
    setBudgetStr('4,50,000');
  };

  const validate = (): boolean => {
    const errors: Record<string, string> = {};
    if (!departureCity) errors.departure_city = 'Please select a departure city';
    if (!destinationCountry) errors.destination_country = 'Please select a destination country';
    if (!startDate) {
      errors.start_date = 'Please select a start date';
    } else {
      if (startDate < '2027-04-01' || startDate > '2027-04-20') {
        errors.start_date = 'Start date must be between 1 Apr 2027 and 20 Apr 2027';
      }
    }
    if (nights < 3 || nights > 10) {
      errors.nights = 'Duration must be between 3 and 10 nights';
    }
    if (adults < 1) errors.adults = 'At least 1 adult is required';
    if (adults + children > 9) {
      errors.adults = 'Max group size is 9 travelers';
    }
    if (rawBudget <= 0) {
      errors.budget = 'Please enter a valid budget in INR';
    }
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    onSubmit({
      departure_city: departureCity,
      destination_country: destinationCountry,
      start_date: startDate,
      nights,
      adults,
      children,
      child_ages: childAges.slice(0, children),
      budget: rawBudget,
      mode: 'default',
    });
  };

  const returnDateStr = calculateReturnDate(startDate, nights);

  // Available countries
  const rawCountries = meta?.destination_countries;
  const countryList: { code: string; name: string; label: string }[] =
    Array.isArray(rawCountries) && rawCountries.length > 0
      ? rawCountries
          .map((c: any) => {
            if (typeof c === 'string') {
              const name = c.trim();
              if (!name) return null;
              const lower = name.toLowerCase();
              const label = lower.includes('japan')
                ? '🇯🇵 Japan (Tokyo, Kyoto, Osaka)'
                : lower.includes('uae')
                ? '🇦🇪 UAE (Dubai, Abu Dhabi)'
                : name;
              return { code: name, name, label };
            }
            if (c && typeof c === 'object') {
              const name = String(c.name || c.country || '').trim();
              if (!name) return null;
              const code = String(c.code || name);
              const lower = name.toLowerCase();
              const label = lower.includes('japan')
                ? '🇯🇵 Japan (Tokyo, Kyoto, Osaka)'
                : lower.includes('uae')
                ? '🇦🇪 UAE (Dubai, Abu Dhabi)'
                : name;
              return { code, name, label };
            }
            return null;
          })
          .filter((item): item is { code: string; name: string; label: string } => item !== null)
      : [];

  const safeCountryList = countryList.length > 0
    ? countryList
    : [
        { code: 'Japan', name: 'Japan', label: '🇯🇵 Japan (Tokyo, Kyoto, Osaka)' },
        { code: 'UAE', name: 'UAE', label: '🇦🇪 UAE (Dubai, Abu Dhabi)' },
      ];

  // Available departure cities
  const rawDepartureCities = meta?.departure_cities;
  const departureCityList: { code: string; label: string }[] =
    Array.isArray(rawDepartureCities) && rawDepartureCities.length > 0
      ? rawDepartureCities
          .map((c: any) => {
            if (typeof c === 'string') {
              const code = c.trim();
              if (!code) return null;
              const label =
                code === 'BOM'
                  ? 'Mumbai (BOM) — Chhatrapati Shivaji Maharaj Intl'
                  : code === 'DEL'
                  ? 'New Delhi (DEL) — Indira Gandhi Intl'
                  : code === 'BLR'
                  ? 'Bengaluru (BLR) — Kempegowda Intl'
                  : code === 'MAA'
                  ? 'Chennai (MAA) — Chennai Intl'
                  : `${code} Intl Airport`;
              return { code, label };
            }
            if (c && typeof c === 'object') {
              const code = String(c.airport || c.code || c.city || '').trim();
              if (!code) return null;
              const cityName = String(c.city || c.name || code).trim();
              const label = `${cityName} (${code}) — ${
                code === 'BOM'
                  ? 'Chhatrapati Shivaji Maharaj'
                  : code === 'DEL'
                  ? 'Indira Gandhi'
                  : code === 'BLR'
                  ? 'Kempegowda'
                  : code === 'MAA'
                  ? 'Chennai'
                  : cityName
              } Intl`;
              return { code, label };
            }
            return null;
          })
          .filter((item): item is { code: string; label: string } => item !== null)
      : [];

  const safeDepartureCityList = departureCityList.length > 0
    ? departureCityList
    : [
        { code: 'BOM', label: 'Mumbai (BOM) — Chhatrapati Shivaji Maharaj Intl' },
        { code: 'DEL', label: 'New Delhi (DEL) — Indira Gandhi Intl' },
        { code: 'BLR', label: 'Bengaluru (BLR) — Kempegowda Intl' },
        { code: 'MAA', label: 'Chennai (MAA) — Chennai Intl' },
      ];

  return (
    <div className="bg-surface-container-lowest rounded-xl shadow-md p-space-lg lg:p-space-xl relative overflow-hidden">
      {/* Top Subtle Status Indicator */}
      <div className="flex items-center justify-between pb-space-md mb-space-lg bg-surface-container-low/50 -mx-space-lg lg:-mx-space-xl -mt-space-lg lg:-mt-space-xl px-space-lg lg:px-space-xl py-space-sm">
        <div className="flex items-center gap-space-sm">
          <span className="material-symbols-outlined text-[18px] text-primary">tune</span>
          <span className="font-headline-sm text-headline-sm text-on-surface">
            Precision Parameter Configuration
          </span>
        </div>
        <div className="flex items-center gap-space-xs font-label-sm text-label-sm text-primary">
          <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
          <span>Zero Booking Fee Protocol</span>
        </div>
      </div>

      <form className="space-y-space-lg" onSubmit={handleSubmit}>
        {/* Row 1: Departure & Destination */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-space-md">
          {/* Field 1: Departure City */}
          <div className="flex flex-col gap-space-xs">
            <label
              className="flex items-center justify-between font-label-md text-label-md text-on-surface font-medium"
              htmlFor="departureCity"
            >
              <span className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[18px] text-primary">
                  flight_takeoff
                </span>
                Departure City
              </span>
              <span className="text-on-surface-variant font-label-sm text-label-sm">Primary Hub</span>
            </label>
            <div className="relative">
              <select
                id="departureCity"
                value={departureCity}
                onChange={(e) => setDepartureCity(e.target.value)}
                className="w-full h-11 px-space-md bg-surface-container-low hover:bg-surface-container text-on-surface rounded-lg font-body-md text-body-md focus:bg-surface-container-lowest focus:outline-none focus:ring-2 focus:ring-primary transition-colors cursor-pointer appearance-none"
              >
                {safeDepartureCityList.map((city) => (
                  <option key={city.code} value={city.code}>
                    {city.label}
                  </option>
                ))}
              </select>
              <span className="material-symbols-outlined absolute right-3 top-2.5 pointer-events-none text-on-surface-variant text-[20px]">
                expand_more
              </span>
            </div>
            {fieldErrors.departure_city && (
              <span className="text-error font-body-sm text-body-sm">{fieldErrors.departure_city}</span>
            )}
            <span className="font-body-sm text-body-sm text-on-surface-variant">
              Non-stop &amp; 1-stop verified connections included
            </span>
          </div>

          {/* Field 2: Destination Country */}
          <div className="flex flex-col gap-space-xs">
            <label
              className="flex items-center justify-between font-label-md text-label-md text-on-surface font-medium"
              htmlFor="destinationCountry"
            >
              <span className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[18px] text-primary">explore</span>
                Destination Country
              </span>
              <span className="text-primary font-label-sm text-label-sm">Verified Corridor</span>
            </label>
            <div className="relative">
              <select
                id="destinationCountry"
                value={destinationCountry}
                onChange={(e) => setDestinationCountry(e.target.value)}
                className="w-full h-11 pl-space-md pr-10 bg-surface-container-low hover:bg-surface-container text-on-surface rounded-lg font-body-md text-body-md focus:bg-surface-container-lowest focus:outline-none focus:ring-2 focus:ring-primary transition-colors cursor-pointer appearance-none"
              >
                {safeCountryList.map((c) => (
                  <option key={c.name} value={c.name}>
                    {c.label}
                  </option>
                ))}
              </select>
              <span className="material-symbols-outlined absolute right-3 top-2.5 pointer-events-none text-on-surface-variant text-[20px]">
                expand_more
              </span>
            </div>
            {fieldErrors.destination_country && (
              <span className="text-error font-body-sm text-body-sm">{fieldErrors.destination_country}</span>
            )}
            <span className="font-body-sm text-body-sm text-on-surface-variant">
              Multi-city routing and intercity transit dynamically arranged
            </span>
          </div>
        </div>

        {/* Row 2: Dates & Duration */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-space-md">
          {/* Field 3: Start Date */}
          <div className="md:col-span-5 flex flex-col gap-space-xs">
            <label
              className="flex items-center justify-between font-label-md text-label-md text-on-surface font-medium"
              htmlFor="holidayDate"
            >
              <span className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[18px] text-primary">
                  calendar_today
                </span>
                Holiday Start Date
              </span>
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-tertiary-fixed text-on-tertiary-fixed font-label-sm text-label-sm">
                <span className="material-symbols-outlined text-[12px]">sunny</span>
                1–20 Apr 2027 Season
              </span>
            </label>
            <div className="relative">
              <input
                id="holidayDate"
                type="date"
                min="2027-04-01"
                max="2027-04-20"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full h-11 px-space-md bg-surface-container-low text-on-surface rounded-lg font-body-md text-body-md focus:bg-surface-container-lowest focus:outline-none focus:ring-2 focus:ring-primary transition-colors cursor-pointer"
              />
            </div>
            {fieldErrors.start_date && (
              <span className="text-error font-body-sm text-body-sm">{fieldErrors.start_date}</span>
            )}
            <div className="flex items-center justify-between font-body-sm text-body-sm text-on-surface-variant">
              <span>Return: {returnDateStr || 'Calculating...'}</span>
              <span className="text-primary font-medium">Optimal Transit Windows</span>
            </div>
          </div>

          {/* Field 4: Number of Nights & Suggested Route */}
          <div className="md:col-span-7 flex flex-col gap-space-xs">
            <label className="flex items-center justify-between font-label-md text-label-md text-on-surface font-medium">
              <span className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[18px] text-primary">hotel</span>
                Duration &amp; City Split
              </span>
              <span className="font-currency-md text-currency-md text-primary">
                {nights} Nights
              </span>
            </label>
            <div className="flex items-center gap-space-sm">
              <div className="flex items-center bg-surface-container-low rounded-lg p-1">
                <button
                  type="button"
                  onClick={() => adjustNights(-1)}
                  disabled={nights <= 3}
                  className="w-9 h-9 rounded bg-surface-container-lowest hover:bg-surface-container text-on-surface flex items-center justify-center transition-colors shadow-sm disabled:opacity-40"
                >
                  <span className="material-symbols-outlined text-[18px]">remove</span>
                </button>
                <input
                  type="text"
                  readOnly
                  value={nights}
                  className="w-12 text-center bg-transparent font-currency-md text-currency-md text-on-surface focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => adjustNights(1)}
                  disabled={nights >= 10}
                  className="w-9 h-9 rounded bg-surface-container-lowest hover:bg-surface-container text-on-surface flex items-center justify-center transition-colors shadow-sm disabled:opacity-40"
                >
                  <span className="material-symbols-outlined text-[18px]">add</span>
                </button>
              </div>

              {/* Route Splitting Pill Block */}
              <div className="flex-1 flex items-center gap-space-xs bg-surface-container-low px-space-md py-2 rounded-lg overflow-x-auto">
                <span className="font-label-sm text-label-sm text-on-surface-variant uppercase whitespace-nowrap">
                  Estimated Split:
                </span>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container-lowest text-on-surface font-label-md text-label-md shadow-sm whitespace-nowrap">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
                  {(destinationCountry || '').toLowerCase().includes('uae') ? 'Dubai' : 'Tokyo'} (
                  {Math.ceil(nights / 2)}N)
                </span>
                <span className="text-outline-variant font-label-sm">+</span>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container-lowest text-on-surface font-label-md text-label-md shadow-sm whitespace-nowrap">
                  <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
                  {(destinationCountry || '').toLowerCase().includes('uae') ? 'Abu Dhabi' : 'Kyoto'} (
                  {Math.floor(nights / 2)}N)
                </span>
              </div>
            </div>
            {fieldErrors.nights && (
              <span className="text-error font-body-sm text-body-sm">{fieldErrors.nights}</span>
            )}
            <span className="font-body-sm text-body-sm text-on-surface-variant">
              Backend optimizes city allocation and transfers automatically
            </span>
          </div>
        </div>

        {/* Row 3: Party Composition (Adults & Dynamic Children) */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-space-md bg-surface-container-low/40 p-space-md rounded-xl">
          {/* Field 5: Adults Stepper */}
          <div className="md:col-span-4 flex flex-col gap-space-xs">
            <label className="flex items-center justify-between font-label-md text-label-md text-on-surface font-medium">
              <span className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[18px] text-primary">groups</span>
                Adults (Age 12+)
              </span>
              <span className="text-on-surface-variant font-label-sm text-label-sm">
                Standard Occupancy
              </span>
            </label>
            <div className="flex items-center justify-between bg-surface-container-lowest rounded-lg p-1.5 shadow-sm">
              <span className="font-headline-sm text-headline-sm text-on-surface pl-2">
                {adults} {adults === 1 ? 'Adult' : 'Adults'}
              </span>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => adjustAdults(-1)}
                  disabled={adults <= 1}
                  className="w-8 h-8 rounded bg-surface-container-low hover:bg-surface-container text-on-surface flex items-center justify-center transition-colors disabled:opacity-40"
                >
                  <span className="material-symbols-outlined text-[16px]">remove</span>
                </button>
                <span className="w-8 text-center font-currency-md text-currency-md text-on-surface">
                  {adults}
                </span>
                <button
                  type="button"
                  onClick={() => adjustAdults(1)}
                  disabled={adults + children >= 9}
                  className="w-8 h-8 rounded bg-surface-container-low hover:bg-surface-container text-on-surface flex items-center justify-center transition-colors disabled:opacity-40"
                >
                  <span className="material-symbols-outlined text-[16px]">add</span>
                </button>
              </div>
            </div>
            {fieldErrors.adults && (
              <span className="text-error font-body-sm text-body-sm">{fieldErrors.adults}</span>
            )}
            <span className="font-body-sm text-body-sm text-on-surface-variant">
              Room allocation adjusted for adult occupancy
            </span>
          </div>

          {/* Field 6: Children with Age Verification Stepper */}
          <ChildAgesInput
            childrenCount={children}
            childAges={childAges}
            onChange={(count, ages) => {
              setChildren(count);
              setChildAges(ages);
            }}
            maxChildren={Math.max(0, 9 - adults)}
          />
        </div>

        {/* Row 4: Budget in INR & Dynamic Adequacy Indicator */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-space-md">
          {/* Field 7: Budget Input */}
          <div className="md:col-span-6 flex flex-col gap-space-xs">
            <div className="flex items-center justify-between">
              <label
                className="flex items-center gap-1.5 font-label-md text-label-md text-on-surface font-medium"
                htmlFor="budgetInput"
              >
                <span className="material-symbols-outlined text-[18px] text-primary">payments</span>
                Total Package Budget (INR)
              </label>
              <span className="font-label-sm text-label-sm text-on-surface-variant">
                All-Inclusive (Flights + Hotels + Rail)
              </span>
            </div>
            <div className="relative">
              <span className="absolute left-3.5 top-2.5 font-currency-md text-currency-md text-primary font-bold">
                ₹
              </span>
              <input
                id="budgetInput"
                type="text"
                value={budgetStr}
                onChange={(e) => handleBudgetChange(e.target.value)}
                className="w-full h-11 pl-9 pr-28 bg-surface-container-low text-on-surface rounded-lg font-currency-md text-currency-md focus:bg-surface-container-lowest focus:outline-none focus:ring-2 focus:ring-primary transition-colors"
              />
              <button
                type="button"
                onClick={setRecommendedBudget}
                className="absolute right-2 top-1.5 px-2 py-1 rounded bg-surface-container-lowest text-primary hover:bg-primary-fixed font-label-sm text-label-sm shadow-sm transition-colors"
              >
                Use Optimum
              </button>
            </div>
            {fieldErrors.budget && (
              <span className="text-error font-body-sm text-body-sm">{fieldErrors.budget}</span>
            )}
            <div className="flex items-center justify-between font-body-sm text-body-sm text-on-surface-variant">
              <span>
                Benchmark for {adults}A {children > 0 ? `+ ${children}C` : ''}:{' '}
                <strong className="text-on-surface font-semibold">₹3,80,000 – ₹5,20,000</strong>
              </span>
              <span className="text-primary font-medium">Taxes &amp; Surcharges inclusive</span>
            </div>
          </div>

          {/* Live Budget Tier & Feasibility Visualizer */}
          <div className="md:col-span-6 flex flex-col justify-between bg-surface-container-low/60 p-space-md rounded-xl">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-space-xs">
                <span className="material-symbols-outlined text-[18px] text-primary">insights</span>
                <span className="font-headline-sm text-headline-sm text-on-surface">
                  Budget Adequacy Analysis
                </span>
              </div>
              <span className={tierClass}>{tierName}</span>
            </div>

            {/* Segmented Gauge Bar */}
            <div className="w-full space-y-1 my-2">
              <div className="w-full h-2.5 bg-surface-container-highest rounded-full overflow-hidden flex">
                <div
                  className="h-full bg-primary rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${gaugePercent}%` }}
                ></div>
              </div>
              <div className="flex justify-between font-label-sm text-label-sm text-on-surface-variant">
                <span>Value (₹2.8L)</span>
                <span className="text-primary font-semibold">
                  Current: {formatINR(rawBudget)}
                </span>
                <span>Signature Luxe (₹6.5L+)</span>
              </div>
            </div>

            {/* Inclusions Snapshot */}
            <div className="flex flex-wrap items-center gap-space-md font-body-sm text-body-sm text-on-surface-variant pt-1">
              <span className="flex items-center gap-1 text-on-surface">
                <span className="material-symbols-outlined text-[15px] text-primary">check_circle</span>
                Premium Centric Stays
              </span>
              <span className="flex items-center gap-1 text-on-surface">
                <span className="material-symbols-outlined text-[15px] text-primary">check_circle</span>
                Intercity Transfers
              </span>
              <span className="flex items-center gap-1 text-on-surface">
                <span className="material-symbols-outlined text-[15px] text-primary">check_circle</span>
                Full Baggage Included
              </span>
            </div>
          </div>
        </div>

        {/* Master Submission & Safety Assurances */}
        <div className="pt-space-md flex flex-col sm:flex-row items-center justify-between gap-space-md">
          {/* Trust Indicators */}
          <div className="flex flex-wrap items-center gap-y-1 gap-x-space-md text-on-surface-variant font-body-sm text-body-sm">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
              Instant algorithmic compilation (3-4 secs)
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
              100% itemized price breakdown
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
              Modifiable post-generation
            </span>
          </div>

          {/* Main CTA */}
          <button
            type="submit"
            disabled={loading}
            className="w-full sm:w-auto min-w-[240px] h-12 px-space-lg rounded-lg bg-primary-container text-on-primary hover:bg-primary font-headline-sm text-headline-sm flex items-center justify-center gap-space-sm shadow-md transition-all active:scale-[0.99] disabled:opacity-60 cursor-pointer"
          >
            {loading ? (
              <>
                <span className="inline-block animate-spin material-symbols-outlined text-[18px]">
                  progress_activity
                </span>
                <span>Compiling Itinerary...</span>
              </>
            ) : (
              <>
                <span>Build My Holiday</span>
                <span className="material-symbols-outlined text-[20px] transition-transform group-hover:translate-x-1">
                  arrow_forward
                </span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
