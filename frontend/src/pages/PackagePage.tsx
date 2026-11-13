import React, { useCallback, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { usePackage } from '../hooks/usePackage';
import { CityPlanHeader } from '../components/package/CityPlanHeader';
import { DayTimeline } from '../components/package/DayTimeline';
import { PriceBreakdown } from '../components/package/PriceBreakdown';
import { CityPlanPicker } from '../components/package/CityPlanPicker';
import { ChangeDrawer } from '../components/change/ChangeDrawer';
import { SideEffectsAlert } from '../components/change/SideEffectsAlert';
import { ConfirmDialog, type BookerDetails } from '../components/reservation/ConfirmDialog';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { Spinner } from '../components/common/Spinner';
import { confirmPackage } from '../api/reservations';
import { getHotelOptions, getFlightOptions, getAttractionOptions, getExportPackageUrl } from '../api/packages';
import { formatINR, formatWeekdayDate } from '../utils/format';
import { isFromLastResults, loadLastResults } from '../utils/lastResults';
import type { PackageItem, ChangeOption, TimelineDay, PackageData } from '../api/types';

type Kind = 'hotel' | 'flight' | 'attraction';

export const PackagePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: packageRes, loading, error, actionLoading, warnings, sideEffects, applyChange, rebuild, undo } = usePackage(id);

  // Change drawer
  const [drawer, setDrawer] = useState<{ kind: Kind; title: string; subtitle?: string; item: PackageItem | null; date?: string } | null>(null);
  const [options, setOptions] = useState<ChangeOption[]>([]);
  const [optionsLoading, setOptionsLoading] = useState(false);

  // Booking
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [confirmError, setConfirmError] = useState<string | null>(null);

  const [actionError, setActionError] = useState<string | null>(null);
  const [notesDismissed, setNotesDismissed] = useState(false);

  const openDrawer = async (
    kind: Kind,
    title: string,
    subtitle: string | undefined,
    item: PackageItem | null,
    load: () => Promise<{ options: ChangeOption[] }>,
    date?: string
  ) => {
    setDrawer({ kind, title, subtitle, item, date });
    setOptions([]);
    setActionError(null);
    try {
      setOptionsLoading(true);
      setOptions((await load()).options || []);
    } catch (err: any) {
      setDrawer(null);
      setActionError(err.message || 'Could not load options');
    } finally {
      setOptionsLoading(false);
    }
  };

  const handleChangeClick = (item: PackageItem) => {
    if (!id) return;
    if (item.type === 'hotel') {
      openDrawer(
        'hotel',
        `Change your stay in ${item.city}`,
        `${item.nights ?? ''} night${item.nights === 1 ? '' : 's'} · same dates · prices are for the whole stay`,
        item,
        () => getHotelOptions(id, item.city)
      );
    } else if (item.type === 'flight') {
      const flights = (packageRes?.items || []).filter((it) => it.type === 'flight');
      const leg: 'arrival' | 'return' = item.leg || (flights[0]?.item_id === item.item_id ? 'arrival' : 'return');
      openDrawer(
        'flight',
        leg === 'arrival' ? 'Change your flight out' : 'Change your flight home',
        'Same day and airports · transfers are re-timed for you',
        { ...item, leg },
        () => getFlightOptions(id, leg)
      );
    }
  };

  const handleAddAttraction = (day: TimelineDay) => {
    if (!id) return;
    const date = day.date.slice(0, 10);
    openDrawer(
      'attraction',
      `Add an activity on day ${day.day_number}`,
      `${formatWeekdayDate(date)}${day.city ? ` · ${day.city}` : ''} · only times that fit your day are shown`,
      null,
      () => getAttractionOptions(id, date),
      date
    );
  };

  const run = async (fn: () => Promise<unknown>, fallback: string) => {
    try {
      setActionError(null);
      setNotesDismissed(false);
      await fn();
    } catch (err: any) {
      setActionError(err.message || fallback);
    }
  };

  const handleSelectOption = (option: ChangeOption) => {
    if (!drawer) return;
    const { kind, item, date } = drawer;
    setDrawer(null);
    if (kind === 'hotel') {
      run(
        () =>
          applyChange({
            kind: 'hotel',
            current_item_id: item?.item_id,
            new_catalog_id: option.catalog_id,
            params: { city: item?.city, room_id: option.room_id },
          }),
        'Could not change the hotel'
      );
    } else if (kind === 'flight') {
      run(
        () =>
          applyChange({
            kind: 'flight',
            current_item_id: item?.item_id,
            new_catalog_id: option.catalog_id,
            params: { leg: item?.leg || 'arrival' },
          }),
        'Could not change the flight'
      );
    } else {
      run(
        () => applyChange({ kind: 'add_attraction', new_catalog_id: option.catalog_id, params: { date, start: option.start } }),
        'Could not add the activity'
      );
    }
  };

  const handleRemove = (item: PackageItem) =>
    run(
      () => applyChange({ kind: 'remove_attraction', current_item_id: item.item_id, new_catalog_id: '', params: {} }),
      'Could not remove the activity'
    );

  const book = async (details?: BookerDetails) => {
    if (!id) return;
    try {
      setConfirming(true);
      setConfirmError(null);
      const res = await confirmPackage(id, {
        base_version: packageRes?.version_no ?? packageRes?.version,
        ...details,
      });
      const ref = res.reference || res.reservation_reference;
      if (ref) navigate(`/reservation/${ref}`);
    } catch (err: any) {
      setConfirmError(err.message || 'Could not book this trip');
    } finally {
      setConfirming(false);
    }
  };

  const closeDrawer = useCallback(() => setDrawer(null), []);
  const closeConfirm = useCallback(() => setConfirmOpen(false), []);

  if (loading && !packageRes) {
    return <Spinner size="lg" label="Loading your trip…" className="py-32" />;
  }

  if (error && !packageRes) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12 flex flex-col gap-4">
        <ErrorBanner title="We couldn't open this trip" message={error} />
        <Link to="/" className="self-start h-10 px-4 rounded-md bg-brand text-white font-semibold flex items-center">
          Plan a new trip
        </Link>
      </div>
    );
  }
  if (!packageRes) return null;

  const pkg: Partial<PackageData> = packageRes.package_data || packageRes.package || {};
  const items = packageRes.items || pkg.items || [];
  const travelerCount = (pkg.travelers?.adults || 0) + (pkg.travelers?.children || 0) || 1;
  const isBooked = packageRes.status === 'BOOKED';
  const total = packageRes.total_inr ?? packageRes.total_price;
  const backLabel = isFromLastResults(id)
    ? Object.keys(loadLastResults()?.outcome.alternatives || {}).length > 0
      ? 'Back to your 3 options'
      : 'Back to search results'
    : undefined;

  return (
    <div className="flex flex-col">
      <CityPlanHeader
        packageRes={packageRes}
        onExportJson={() => id && window.open(getExportPackageUrl(id), '_blank')}
        onUndo={() => run(() => undo(), 'Could not undo')}
        undoing={actionLoading}
        backLabel={backLabel}
      />

      <div className="max-w-6xl mx-auto px-4 w-full py-6 grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-6 items-start">
        <div className="flex flex-col gap-4 min-w-0">
          {isBooked && (
            <ErrorBanner
              tone="success"
              title="This trip is booked"
              message="It can't be changed any more. Use “View your booking” to see the confirmation."
            />
          )}
          {packageRes.status === 'OVER_BUDGET' && (
            <ErrorBanner
              tone="warning"
              title="This is the cheapest possible trip — and it's over your budget"
              message={`It costs ${formatINR(pkg.totals?.budget_over)} more than you set. You can still change or book it.`}
            />
          )}
          {actionError && <ErrorBanner title="That change didn't work" message={actionError} onDismiss={() => setActionError(null)} />}
          {!notesDismissed && <SideEffectsAlert sideEffects={sideEffects} warnings={warnings} onDismiss={() => setNotesDismissed(true)} />}
          {actionLoading && <Spinner size="sm" label="Updating your trip…" className="justify-start" />}

          <DayTimeline
            timeline={packageRes.timeline || []}
            items={items}
            cities={pkg.cities || []}
            onChangeClick={handleChangeClick}
            onRemoveClick={handleRemove}
            onAddAttractionClick={handleAddAttraction}
            readOnly={isBooked || actionLoading}
          />

          {!isBooked && (packageRes.city_plans?.length || 0) > 1 && (
            <CityPlanPicker
              cityPlans={packageRes.city_plans}
              currentCities={pkg.cities}
              currentNights={pkg.nights_per_city}
              currentTotal={total}
              onSelectPlan={(plan) => run(() => rebuild(plan), 'Could not rebuild on that city split')}
              loading={actionLoading}
            />
          )}
        </div>

        <PriceBreakdown
          totals={pkg.totals}
          items={items}
          totalPrice={total}
          travelerCount={travelerCount}
          booked={isBooked}
          confirming={confirming && !confirmOpen}
          onConfirm={() => (isBooked ? book() : (setConfirmError(null), setConfirmOpen(true)))}
        />
      </div>

      {/* Phones: total + book button always in reach */}
      <div className="lg:hidden h-20" aria-hidden="true" />
      <div className="lg:hidden fixed bottom-0 inset-x-0 z-40 bg-white border-t border-line shadow-pop px-4 py-3 flex items-center justify-between gap-3">
        <div>
          <div className="text-xs text-ink-mute">Total for {travelerCount} traveler{travelerCount === 1 ? '' : 's'}</div>
          <div className="text-xl font-extrabold text-ink tabular-nums">{formatINR(total)}</div>
        </div>
        <button
          type="button"
          onClick={() => (isBooked ? book() : (setConfirmError(null), setConfirmOpen(true)))}
          disabled={confirming}
          className={`h-11 px-5 rounded-md font-bold text-white disabled:opacity-60 ${isBooked ? 'bg-ok' : 'bg-brand hover:bg-brand-dark'}`}
        >
          {isBooked ? 'View booking' : 'Book this trip'}
        </button>
      </div>

      <ChangeDrawer
        isOpen={drawer !== null}
        onClose={closeDrawer}
        title={drawer?.title || ''}
        subtitle={drawer?.subtitle}
        kind={drawer?.kind || 'hotel'}
        currentItem={drawer?.item}
        options={options}
        onSelectOption={handleSelectOption}
        loading={optionsLoading}
      />

      <ConfirmDialog
        isOpen={confirmOpen}
        total={total}
        defaultName={pkg.traveler_name}
        submitting={confirming}
        error={confirmError}
        onClose={closeConfirm}
        onConfirm={book}
      />
    </div>
  );
};
