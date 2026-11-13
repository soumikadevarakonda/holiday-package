import React, { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { RequestForm } from '../components/request/RequestForm';
import { QuickRequestBox } from '../components/request/QuickRequestBox';
import { OverBudgetPanel } from '../components/outcome/OverBudgetPanel';
import { NoPackagePanel } from '../components/outcome/NoPackagePanel';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { Photo } from '../components/common/Photo';
import { Icon } from '../components/common/Icon';
import { useMeta } from '../hooks/useMeta';
import { createPackage } from '../api/packages';
import { ApiError } from '../api/client';
import type { TripRequest, PackageResponse } from '../api/types';

interface Preset {
  title: string;
  subtitle: string;
  image: string;
  values: Partial<TripRequest>;
}

const PRESETS: Preset[] = [
  {
    title: 'Tokyo & Osaka',
    subtitle: 'Family of 3 from Bengaluru · 6 nights · ₹3.5 lakh',
    image: 'images/attractions/ATT-TYO-004.jpg',
    values: { departure_city: 'BLR', destination_country: 'Japan', start_date: '2027-04-10', nights: 6, adults: 2, children: 1, child_ages: [6], budget: 350000 },
  },
  {
    title: 'Japan, three cities',
    subtitle: 'Couple from Mumbai · 9 nights · ₹6 lakh',
    image: 'images/attractions/ATT-KYO-001.jpg',
    values: { departure_city: 'BOM', destination_country: 'Japan', start_date: '2027-04-05', nights: 9, adults: 2, children: 0, child_ages: [], budget: 600000 },
  },
  {
    title: 'Dubai & Abu Dhabi',
    subtitle: 'Couple from Delhi · 6 nights · ₹3 lakh',
    image: 'images/attractions/ATT-DXB-001.jpg',
    values: { departure_city: 'DEL', destination_country: 'United Arab Emirates', start_date: '2027-04-06', nights: 6, adults: 2, children: 0, child_ages: [], budget: 300000 },
  },
  {
    title: 'Dubai short break',
    subtitle: 'Family of 4 from Chennai · 4 nights · ₹4 lakh',
    image: 'images/attractions/ATT-DXB-002.jpg',
    values: { departure_city: 'MAA', destination_country: 'United Arab Emirates', start_date: '2027-04-12', nights: 4, adults: 2, children: 2, child_ages: [5, 9], budget: 400000 },
  },
];

const STEPS = [
  { icon: 'travel_explore', title: 'Search once', text: 'Tell us where, when, who and your budget.' },
  { icon: 'route', title: 'Get a full trip', text: 'Flights, hotels, transfers and a day-by-day plan that fit together.' },
  { icon: 'tune', title: 'Make it yours', text: 'Swap a hotel, flight or activity — times and prices update for you.' },
  { icon: 'verified', title: 'Book in one go', text: 'Confirm and get one 10-digit booking number for everything.' },
];

export const RequestPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: meta, error: metaError } = useMeta();
  const resultRef = useRef<HTMLDivElement>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [serverErrors, setServerErrors] = useState<Record<string, string>>({});
  const [outcome, setOutcome] = useState<PackageResponse | null>(null);
  const [initialValues, setInitialValues] = useState<Partial<TripRequest>>({});

  const fill = (values: Partial<TripRequest>) => {
    setInitialValues({ ...values });
    setOutcome(null);
    setError(null);
    setServerErrors({});
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSubmit = async (payload: TripRequest) => {
    try {
      setLoading(true);
      setError(null);
      setServerErrors({});
      setOutcome(null);
      const res = await createPackage(payload);
      if (res.outcome === 'OVER_BUDGET' || res.outcome === 'NO_PACKAGE') {
        setOutcome(res);
        setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50);
      } else {
        navigate(`/package/${res.package_id}`);
      }
    } catch (err: any) {
      const fe = err instanceof ApiError ? (err.details as any)?.field_errors : undefined;
      if (fe && typeof fe === 'object') setServerErrors(fe);
      else setError(err.message || 'Something went wrong while building your trip');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col">
      {/* Hero + search */}
      <section className="bg-navy pb-10 pt-8 sm:pt-12">
        <div className="max-w-6xl mx-auto px-4">
          <h1 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight">Your whole holiday, built for you</h1>
          <p className="mt-2 text-lg sm:text-xl text-white/90">
            Flights, hotels, transfers and things to do — in one trip, within your budget.
          </p>
          <div className="mt-6">
            <RequestForm
              meta={meta}
              onSubmit={handleSubmit}
              loading={loading}
              initialValues={initialValues}
              serverErrors={serverErrors}
            />
            <QuickRequestBox onParsed={fill} />
          </div>
        </div>
      </section>

      <div className="max-w-6xl mx-auto px-4 w-full flex flex-col gap-10 mt-8">
        <div ref={resultRef} className="flex flex-col gap-4 empty:hidden">
          {loading && (
            <div className="bg-white rounded-lg shadow-card p-5 flex items-center gap-4" role="status">
              <span className="w-8 h-8 rounded-full border-4 border-brand/20 border-t-brand animate-spin" />
              <div>
                <p className="font-semibold text-ink">Building your trip…</p>
                <p className="text-sm text-ink-mute">Checking every city split, flight, hotel and transfer for your dates.</p>
              </div>
            </div>
          )}
          {metaError && <ErrorBanner tone="warning" title="Couldn't load destinations" message={metaError} />}
          {error && <ErrorBanner title="We couldn't build your trip" message={error} onDismiss={() => setError(null)} />}
          {outcome?.outcome === 'OVER_BUDGET' && (
            <OverBudgetPanel
              cheapestTotal={outcome.cheapest_total}
              overBy={outcome.over_by}
              suggestion={outcome.suggestion}
              onModifyRequest={() => fill(initialValues)}
              onAcceptCheapest={outcome.package_id ? () => navigate(`/package/${outcome.package_id}`) : undefined}
            />
          )}
          {outcome?.outcome === 'NO_PACKAGE' && (
            <NoPackagePanel reason={outcome.reason} onModifyRequest={() => fill(initialValues)} />
          )}
        </div>

        {/* Popular trips */}
        <section aria-labelledby="popular">
          <h2 id="popular" className="text-2xl font-bold text-ink">Popular trips</h2>
          <p className="text-ink-mute mt-1">Start from one of these and change anything you like.</p>
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {PRESETS.map((p) => (
              <button
                key={p.title}
                type="button"
                onClick={() => fill(p.values)}
                className="group text-left bg-white rounded-lg shadow-card overflow-hidden hover:shadow-pop transition-shadow focus:outline-none focus:ring-2 focus:ring-brand"
              >
                <Photo src={p.image} alt={p.title} fallbackType="city" className="w-full h-40 object-cover" />
                <div className="p-3">
                  <p className="font-bold text-ink group-hover:text-brand">{p.title}</p>
                  <p className="text-sm text-ink-mute mt-0.5">{p.subtitle}</p>
                </div>
              </button>
            ))}
          </div>
        </section>

        {/* How it works */}
        <section aria-labelledby="how" className="bg-white rounded-lg shadow-card p-5 sm:p-6">
          <h2 id="how" className="text-xl font-bold text-ink">How it works</h2>
          <ol className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {STEPS.map((s, i) => (
              <li key={s.title} className="flex gap-3">
                <span className="w-10 h-10 rounded-full bg-brand-light text-brand flex items-center justify-center shrink-0">
                  <Icon name={s.icon} />
                </span>
                <div>
                  <p className="font-semibold text-ink">
                    {i + 1}. {s.title}
                  </p>
                  <p className="text-sm text-ink-mute mt-0.5">{s.text}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>
      </div>
    </div>
  );
};
