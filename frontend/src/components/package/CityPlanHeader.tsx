import React from 'react';
import { formatINR, formatDate } from '../../utils/format';
import type { PackageResponse, PackageData } from '../../api/types';

interface CityPlanHeaderProps {
  packageRes: PackageResponse;
  onExportJson: () => void;
  onConfirm: () => void;
  exporting?: boolean;
  confirming?: boolean;
}

export const CityPlanHeader: React.FC<CityPlanHeaderProps> = ({
  packageRes,
  onExportJson,
  onConfirm,
  exporting = false,
  confirming = false,
}) => {
  const pkgData: PackageData = packageRes.package_data || packageRes.package || ({} as PackageData);
  const total = packageRes.total_inr || packageRes.total_price || pkgData.total_inr || 0;
  const targetBudget = pkgData.totals?.budget || 450000;
  const diff = targetBudget - total;
  const isUnder = diff >= 0;

  // City corridor
  const cities = pkgData.cities || ['Tokyo', 'Kyoto'];
  const nightsPerCity = pkgData.nights_per_city || {};

  // Travelers
  const travelers = pkgData.travelers || { adults: 2, children: 1, child_ages: [7] };
  const travelerText = `${travelers.adults} ${travelers.adults === 1 ? 'Adult' : 'Adults'}${
    travelers.children > 0
      ? `, ${travelers.children} ${travelers.children === 1 ? 'Child' : 'Children'}`
      : ''
  }`;

  // Dates
  const startDateStr = formatDate(pkgData.start_date || '2027-04-05');
  const endDateStr = formatDate(pkgData.end_date || '2027-04-13');

  // Reference
  const refCode = packageRes.package_id.toUpperCase().slice(0, 10);

  return (
    <div className="w-full bg-surface-container-lowest shadow-sm mb-space-lg">
      <div className="max-w-7xl mx-auto px-margin py-space-md flex flex-col gap-space-md">
        {/* Breadcrumb, Package Tag & Reference */}
        <div className="flex flex-wrap items-center justify-between gap-space-sm font-label-md text-label-md">
          <div className="flex items-center gap-space-xs text-on-surface-variant">
            <span className="hover:text-primary cursor-pointer transition-colors">Holiday Builder</span>
            <span className="material-symbols-outlined text-[16px]">chevron_right</span>
            <span className="hover:text-primary cursor-pointer transition-colors">
              {pkgData.country || 'International'} Packages
            </span>
            <span className="material-symbols-outlined text-[16px]">chevron_right</span>
            <span className="text-on-surface font-semibold">
              {pkgData.country || 'Holiday'} Discovery (#{refCode})
            </span>
          </div>
          <div className="flex items-center gap-space-xs bg-surface-container-low px-space-sm py-1 rounded-full text-on-surface-variant font-currency-md text-label-sm">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
            <span>LIVE QUOTE ACCREDITED</span>
            <span className="text-outline-variant">•</span>
            <span>VERSION v{packageRes.version_no || packageRes.version || 1}</span>
          </div>
        </div>

        {/* Title & Key Travel Specs */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-space-md">
          <div>
            <div className="flex flex-wrap items-center gap-space-xs mb-space-xs">
              <span className="bg-primary/10 text-primary px-space-sm py-0.5 rounded-full font-label-sm text-label-sm uppercase tracking-wider font-semibold">
                Curated Itinerary
              </span>
              <span className="bg-surface-container-high text-on-surface-variant px-space-sm py-0.5 rounded-full font-label-sm text-label-sm">
                REF: #{refCode}
              </span>
            </div>
            <h1 className="font-headline-xl text-headline-xl text-on-surface tracking-tight font-bold">
              {pkgData.country || 'Destination'} Discovery: {cities.join(' & ')}
            </h1>
            <div className="flex flex-wrap items-center gap-x-space-md gap-y-space-xs mt-1 text-on-surface-variant font-body-md text-body-md">
              <span className="flex items-center gap-1">
                <span className="material-symbols-outlined text-primary text-[18px]">
                  calendar_today
                </span>
                {startDateStr} – {endDateStr}
              </span>
              <span className="text-outline-variant">•</span>
              <span className="flex items-center gap-1">
                <span className="material-symbols-outlined text-primary text-[18px]">group</span>
                {travelerText}
              </span>
            </div>
          </div>

          {/* Primary Action Suite */}
          <div className="flex items-center gap-space-sm">
            <button
              type="button"
              onClick={onExportJson}
              disabled={exporting}
              className="flex items-center gap-space-xs px-space-md py-2.5 rounded-lg bg-surface-container-low text-on-surface hover:bg-surface-container-high transition-all shadow-sm font-label-md text-label-md cursor-pointer disabled:opacity-50"
            >
              <span className="material-symbols-outlined text-[18px] text-on-surface-variant">
                data_object
              </span>
              <span>{exporting ? 'Exporting...' : 'Export Itinerary (JSON)'}</span>
            </button>
            <button
              type="button"
              onClick={onConfirm}
              disabled={confirming}
              className="flex items-center gap-space-xs px-space-lg py-2.5 rounded-lg bg-primary hover:bg-primary-container text-on-primary font-headline-sm text-headline-sm transition-all shadow-md active:scale-95 cursor-pointer disabled:opacity-60"
            >
              <span className="material-symbols-outlined text-[20px]">verified_user</span>
              <span>{confirming ? 'Confirming...' : 'Confirm Holiday'}</span>
            </button>
          </div>
        </div>

        {/* Segment Ribbon & Real-time Budget Metrics */}
        <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-space-md pt-space-sm bg-surface-container-low/60 p-space-md rounded-xl">
          {/* Journey Corridor */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-label-sm text-label-sm uppercase text-on-surface-variant font-bold tracking-wider mr-1">
              Journey Corridor:
            </span>
            {cities.map((city, idx) => (
              <React.Fragment key={city}>
                {idx > 0 && (
                  <>
                    <span className="material-symbols-outlined text-outline-variant text-[16px]">
                      arrow_forward
                    </span>
                    <div className="flex items-center gap-1.5 px-3 py-1 bg-surface-container-lowest rounded-full shadow-sm text-on-surface font-label-md text-label-md">
                      <span className="material-symbols-outlined text-[16px] text-secondary">
                        train
                      </span>
                      <span>Intercity Transit</span>
                    </div>
                    <span className="material-symbols-outlined text-outline-variant text-[16px]">
                      arrow_forward
                    </span>
                  </>
                )}
                <div className="flex items-center gap-1.5 px-3 py-1 bg-surface-container-lowest rounded-full shadow-sm text-on-surface font-label-md text-label-md">
                  <span className="material-symbols-outlined text-[16px] text-primary">
                    location_city
                  </span>
                  <span className="font-semibold">{city}</span>
                  <span className="text-on-surface-variant text-[11px]">
                    ({nightsPerCity[city] || Math.floor(8 / cities.length)} Nights)
                  </span>
                </div>
              </React.Fragment>
            ))}
          </div>

          {/* Financial Health Micro-Component */}
          <div className="flex flex-wrap items-center gap-space-lg">
            <div className="flex items-baseline gap-space-xs">
              <span className="font-label-sm text-label-sm text-on-surface-variant uppercase">
                Current Total:
              </span>
              <span className="font-currency-display text-headline-lg font-bold text-on-surface">
                {formatINR(total)}
              </span>
            </div>
            <div className="flex items-baseline gap-space-xs">
              <span className="font-label-sm text-label-sm text-on-surface-variant uppercase">
                Target Budget:
              </span>
              <span className="font-currency-md text-currency-md text-on-surface-variant">
                {formatINR(targetBudget)}
              </span>
            </div>

            {/* Status Indicator Pill */}
            <div className="flex items-center gap-space-xs">
              <div
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full font-label-sm text-label-sm font-semibold transition-all ${
                  isUnder
                    ? 'bg-primary/10 text-primary'
                    : 'bg-error-container text-on-error-container'
                }`}
              >
                <span className="material-symbols-outlined text-[16px]">
                  account_balance_wallet
                </span>
                <span>
                  {isUnder
                    ? `${formatINR(diff)} Under Budget`
                    : `${formatINR(Math.abs(diff))} Over Budget (Warning)`}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
