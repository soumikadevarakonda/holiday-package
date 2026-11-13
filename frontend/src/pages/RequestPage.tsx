import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { RequestForm } from '../components/request/RequestForm';
import { QuickRequestBox } from '../components/request/QuickRequestBox';
import { OverBudgetPanel } from '../components/outcome/OverBudgetPanel';
import { NoPackagePanel } from '../components/outcome/NoPackagePanel';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { useMeta } from '../hooks/useMeta';
import { createPackage } from '../api/packages';
import type { TripRequest, PackageResponse } from '../api/types';

export const RequestPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: meta, loading: metaLoading, error: metaError } = useMeta();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [outcome, setOutcome] = useState<PackageResponse | null>(null);
  const [initialFormValues, setInitialFormValues] = useState<Partial<TripRequest>>({});

  const handleApplyPreset = (preset: 'golden' | 'hokkaido' | 'kansai') => {
    if (preset === 'golden') {
      setInitialFormValues({
        destination_country: 'Japan',
        departure_city: 'BOM',
        start_date: '2027-04-05',
        nights: 8,
        adults: 2,
        children: 1,
        child_ages: [7],
        budget: 450000,
      });
    } else if (preset === 'hokkaido') {
      setInitialFormValues({
        destination_country: 'Japan',
        departure_city: 'DEL',
        start_date: '2027-04-06',
        nights: 7,
        adults: 2,
        children: 0,
        child_ages: [],
        budget: 410000,
      });
    } else if (preset === 'kansai') {
      setInitialFormValues({
        destination_country: 'Japan',
        departure_city: 'BLR',
        start_date: '2027-04-07',
        nights: 6,
        adults: 2,
        children: 1,
        child_ages: [9],
        budget: 365000,
      });
    }
    setOutcome(null);
  };

  const handleParsed = (parsed: Partial<TripRequest>) => {
    setInitialFormValues((prev) => ({ ...prev, ...parsed }));
    setOutcome(null);
  };

  const handleSubmit = async (payload: TripRequest) => {
    try {
      setLoading(true);
      setError(null);
      setOutcome(null);
      const res = await createPackage(payload);

      if (res.outcome === 'PACKAGE' || (!res.outcome && res.package_id)) {
        // Success: navigate to active package customizer
        navigate(`/package/${res.package_id}`);
      } else if (res.outcome === 'OVER_BUDGET') {
        setOutcome(res);
      } else if (res.outcome === 'NO_PACKAGE') {
        setOutcome(res);
      } else {
        navigate(`/package/${res.package_id}`);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to compile holiday package');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-margin py-space-xl flex flex-col gap-space-lg">
      {/* Meta Dossier Bar */}
      <div className="flex flex-wrap items-center justify-between gap-space-sm mb-space-sm text-on-surface-variant font-label-sm text-label-sm uppercase tracking-wider">
        <div className="flex items-center gap-space-sm">
          <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-primary-container text-on-primary text-[10px] font-bold">
            01
          </span>
          <span className="text-on-surface font-semibold">Itinerary Parameters</span>
          <span className="text-outline-variant">/</span>
          <span className="text-on-surface-variant">Step 1 of 3: Trip Initialization</span>
        </div>
        <div className="flex items-center gap-space-md">
          <span className="flex items-center gap-1.5 text-primary font-medium">
            <span className="material-symbols-outlined text-[16px]">verified</span>
            Live Travel Catalogue Connected
          </span>
          <span className="hidden sm:inline-block px-2 py-0.5 rounded bg-surface-container-low text-on-surface-variant font-currency-md text-[11px]">
            BUILDER V2.4
          </span>
        </div>
      </div>

      {/* Editorial Header Block */}
      <div className="mb-space-md flex flex-col md:flex-row md:items-end justify-between gap-space-md">
        <div className="max-w-2xl">
          <h1 className="font-headline-xl text-headline-xl text-on-surface tracking-tight font-bold">
            Where would you like to go?
          </h1>
          <p className="mt-space-xs font-body-lg text-body-lg text-on-surface-variant">
            Enter your trip parameters. Our intelligent compiler dynamically orchestrates verified airfare, handpicked accommodations, high-speed rail transfers, and localized excursions.
          </p>
        </div>

        {/* Quick Route Suggestions Selector & Text Parser */}
        <QuickRequestBox
          onParsed={handleParsed}
          onApplyPreset={handleApplyPreset}
        />
      </div>

      {metaError && (
        <ErrorBanner
          title="Catalogue Metadata Warning"
          message={metaError}
          onDismiss={() => {}}
        />
      )}

      {error && (
        <ErrorBanner
          title="Compilation Failed"
          message={error}
          onDismiss={() => setError(null)}
        />
      )}

      {/* Outcomes if OVER_BUDGET or NO_PACKAGE */}
      {outcome?.outcome === 'OVER_BUDGET' && (
        <OverBudgetPanel
          cheapestTotal={outcome.cheapest_total}
          overBy={outcome.over_by}
          suggestion={outcome.suggestion}
          onModifyRequest={() => setOutcome(null)}
          onAcceptCheapest={
            outcome.package_id
              ? () => navigate(`/package/${outcome.package_id}`)
              : undefined
          }
        />
      )}

      {outcome?.outcome === 'NO_PACKAGE' && (
        <NoPackagePanel
          reason={outcome.reason}
          onModifyRequest={() => setOutcome(null)}
        />
      )}

      {/* Master Form Workspace Card */}
      <RequestForm
        meta={meta}
        onSubmit={handleSubmit}
        loading={loading || metaLoading}
        onApplyPreset={handleApplyPreset}
        initialValues={initialFormValues}
      />

      {/* Editorial Feature Dossier Grid: Why this engine works */}
      <div className="mt-space-xl grid grid-cols-1 md:grid-cols-3 gap-space-lg">
        <div className="p-space-lg rounded-xl bg-surface-container-low shadow-sm flex flex-col justify-between">
          <div className="space-y-space-xs">
            <div className="w-8 h-8 rounded-lg bg-primary text-on-primary flex items-center justify-center">
              <span className="material-symbols-outlined text-[18px]">hub</span>
            </div>
            <h3 className="font-headline-sm text-headline-sm text-on-surface">
              Dynamic Transit Matching
            </h3>
            <p className="font-body-md text-body-md text-on-surface-variant">
              Connects Mumbai, Delhi, Bengaluru &amp; Chennai flight schedules directly with destination transit schedules to eliminate disjointed layovers.
            </p>
          </div>
          <div className="mt-space-md pt-space-xs font-label-sm text-label-sm text-primary uppercase font-semibold">
            Automated Rail + Flight Sync
          </div>
        </div>

        <div className="p-space-lg rounded-xl bg-surface-container-low shadow-sm flex flex-col justify-between">
          <div className="space-y-space-xs">
            <div className="w-8 h-8 rounded-lg bg-primary text-on-primary flex items-center justify-center">
              <span className="material-symbols-outlined text-[18px]">receipt_long</span>
            </div>
            <h3 className="font-headline-sm text-headline-sm text-on-surface">
              Transparent Currency Index
            </h3>
            <p className="font-body-md text-body-md text-on-surface-variant">
              All prices locked in INR (₹). Hedged against volatile currency fluctuations and inclusive of all state tourist levies and taxes.
            </p>
          </div>
          <div className="mt-space-md pt-space-xs font-label-sm text-label-sm text-primary uppercase font-semibold">
            No Hidden Forex Margins
          </div>
        </div>

        <div className="p-space-lg rounded-xl bg-surface-container-low shadow-sm flex flex-col justify-between">
          <div className="space-y-space-xs">
            <div className="w-8 h-8 rounded-lg bg-primary text-on-primary flex items-center justify-center">
              <span className="material-symbols-outlined text-[18px]">family_restroom</span>
            </div>
            <h3 className="font-headline-sm text-headline-sm text-on-surface">
              Precision Family Sizing
            </h3>
            <p className="font-body-md text-body-md text-on-surface-variant">
              Children&apos;s exact ages trigger precise age-discount brackets on train networks and theme park excursion pass tiers.
            </p>
          </div>
          <div className="mt-space-md pt-space-xs font-label-sm text-label-sm text-primary uppercase font-semibold">
            Child Fare Calculation
          </div>
        </div>
      </div>
    </div>
  );
};
