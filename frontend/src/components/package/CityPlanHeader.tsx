import React from 'react';
import { Link } from 'react-router-dom';
import { Icon } from '../common/Icon';
import { formatDate } from '../../utils/format';
import type { PackageResponse, PackageData } from '../../api/types';

interface CityPlanHeaderProps {
  packageRes: PackageResponse;
  onExportJson: () => void;
  onUndo?: () => void;
  undoing?: boolean;
  /** Text for the link back to the search results this trip was picked from (hidden when not given). */
  backLabel?: string;
}

const STATUS: Record<string, { label: string; cls: string }> = {
  PLANNED: { label: 'Not booked yet', cls: 'bg-brand-light text-brand' },
  OVER_BUDGET: { label: 'Over budget', cls: 'bg-warn-light text-warn' },
  BOOKED: { label: 'Booked', cls: 'bg-ok-light text-ok' },
};

/** Trip summary: search recap strip, then the trip title with status and actions. */
export const CityPlanHeader: React.FC<CityPlanHeaderProps> = ({ packageRes, onExportJson, onUndo, undoing, backLabel }) => {
  const pkg: PackageData = packageRes.package_data || packageRes.package || ({ trip_id: '', items: [] } as PackageData);
  const plan = (pkg.cities || []).map((c) => ({ city: c, nights: pkg.nights_per_city?.[c] }));
  const t = pkg.travelers || { adults: 0, children: 0, child_ages: [] };
  const version = packageRes.version_no ?? packageRes.version ?? 1;
  const status = STATUS[packageRes.status] || { label: packageRes.status, cls: 'bg-canvas text-ink-soft' };
  const nights = plan.reduce((s, p) => s + (p.nights || 0), 0);

  const people = [
    `${t.adults} adult${t.adults === 1 ? '' : 's'}`,
    t.children ? `${t.children} child${t.children === 1 ? '' : 'ren'}${t.child_ages?.length ? ` (age ${t.child_ages.join(', ')})` : ''}` : '',
  ]
    .filter(Boolean)
    .join(', ');

  return (
    <div className="bg-white border-b border-line">
      {/* Search recap */}
      <div className="bg-navy-light">
        <div className="max-w-6xl mx-auto px-4 py-2.5 flex flex-wrap items-center gap-x-5 gap-y-1 text-sm text-navy">
          {backLabel && (
            <Link
              to="/?view=results"
              className="flex items-center gap-1 font-semibold text-brand hover:underline pr-4 sm:border-r border-navy/20"
            >
              <Icon name="arrow_back" className="!text-base" />
              {backLabel}
            </Link>
          )}
          <span className="flex items-center gap-1.5 font-semibold">
            <Icon name="flight_takeoff" className="!text-base" />
            {pkg.departure_city} → {pkg.country}
          </span>
          <span className="flex items-center gap-1.5">
            <Icon name="calendar_month" className="!text-base" />
            {formatDate(pkg.start_date)} – {formatDate(pkg.end_date)} · {nights} night{nights === 1 ? '' : 's'}
          </span>
          <span className="flex items-center gap-1.5">
            <Icon name="group" className="!text-base" />
            {people}
          </span>
          <Link to="/" className="ml-auto font-semibold text-brand hover:underline flex items-center gap-1">
            <Icon name="edit" className="!text-base" />
            Change search
          </Link>
        </div>
      </div>

      {/* Title */}
      <div className="max-w-6xl mx-auto px-4 py-5 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className={`px-2 py-0.5 rounded font-semibold ${status.cls}`}>{status.label}</span>
            <span className="text-ink-mute">Version {version}</span>
          </div>
          <h1 className="mt-1 text-2xl sm:text-3xl font-extrabold text-ink tracking-tight">
            {pkg.traveler_name && pkg.traveler_name !== 'Traveler' ? `${pkg.traveler_name}'s ` : 'Your '}
            {pkg.country} trip
          </h1>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {plan.map((p, i) => (
              <React.Fragment key={p.city}>
                {i > 0 && <Icon name="arrow_forward" className="!text-base text-ink-mute" />}
                <span className="px-2.5 py-1 rounded-full bg-canvas text-sm font-medium text-ink">
                  {p.city} <span className="text-ink-mute">· {p.nights}N</span>
                </span>
              </React.Fragment>
            ))}
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {onUndo && version > 1 && packageRes.status !== 'BOOKED' && (
            <button
              type="button"
              onClick={onUndo}
              disabled={undoing}
              className="h-10 px-3 rounded-md border border-line text-ink-soft font-semibold hover:bg-canvas flex items-center gap-1 disabled:opacity-50"
            >
              <Icon name="undo" />
              Undo last change
            </button>
          )}
          <button
            type="button"
            onClick={onExportJson}
            className="h-10 px-3 rounded-md border border-line text-ink-soft font-semibold hover:bg-canvas flex items-center gap-1"
          >
            <Icon name="download" />
            Download trip
          </button>
        </div>
      </div>
    </div>
  );
};
