import React from 'react';
import { PriceDiff } from './PriceDiff';
import type { ChangeOption } from '../../api/types';

interface OptionListProps {
  options: ChangeOption[];
  currentCatalogId?: string;
  onSelectOption: (option: ChangeOption) => void;
  loading?: boolean;
}

export const OptionList: React.FC<OptionListProps> = ({
  options,
  currentCatalogId,
  onSelectOption,
  loading = false,
}) => {
  if (options.length === 0) {
    return (
      <div className="p-space-lg text-center text-on-surface-variant font-body-md text-body-md">
        No alternative options available for this selection.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-space-sm">
      {options.map((option) => {
        const isCurrent = option.current ?? option.catalog_id === currentCatalogId;
        const diff = option.price_diff ?? 0;
        const isUpgrade = diff > 0;

        let badgeText = isCurrent ? 'Current Selection' : isUpgrade ? 'Premium Upgrade' : 'Budget Saver';
        let badgeClass = isCurrent
          ? 'bg-primary text-on-primary'
          : isUpgrade
          ? 'bg-secondary-container text-on-secondary-container'
          : 'bg-surface-container-high text-on-surface-variant';

        return (
          <div
            key={option.key || option.catalog_id}
            className={`p-space-md rounded-xl transition-all ${
              isCurrent
                ? 'bg-surface-container-low border border-primary/20'
                : 'bg-surface-container-lowest hover:bg-surface-container-low border border-outline-variant/30'
            }`}
          >
            <div className="flex items-start justify-between gap-space-sm">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded font-label-sm text-label-sm font-semibold ${badgeClass}`}>
                    {badgeText}
                  </span>
                  <h4 className="font-headline-sm text-headline-sm font-semibold text-on-surface">
                    {option.name}
                  </h4>
                </div>

                {option.room_type && (
                  <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
                    {option.room_type}
                  </p>
                )}

                {option.airline && (
                  <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
                    {option.airline}
                    {option.departure_time ? ` • Departs ${option.departure_time}` : ''}
                    {option.arrival_time ? ` • Arrives ${option.arrival_time}` : ''}
                    {option.duration ? ` • ${option.duration}` : ''}
                  </p>
                )}

                {option.category && (
                  <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
                    {option.category.replace(/_/g, ' ').toLowerCase()}
                    {option.time_slot ? ` • starts ${option.time_slot}` : ''}
                  </p>
                )}

                {(option.details?.side_effects?.length > 0 || option.details?.warnings?.length > 0) && (
                  <p className="font-body-sm text-body-sm text-tertiary mt-1">
                    {[...(option.details?.side_effects || []), ...(option.details?.warnings || [])].join(' ')}
                  </p>
                )}

                <div className="flex items-center gap-2 mt-2 font-label-sm text-label-sm text-on-surface-variant">
                  {option.rating != null && <span>Guest rating {option.rating}/10</span>}
                  {option.rating != null && <span>•</span>}
                  <span>{option.price_inr != null ? `Total ₹ ${Math.round(option.price_inr).toLocaleString('en-IN')}` : ''}</span>
                </div>
              </div>

              <div className="text-right flex flex-col items-end shrink-0">
                <PriceDiff diff={diff} />
                <span className="font-label-sm text-label-sm text-on-surface-variant">
                  {isCurrent ? 'Base Package' : 'Price Difference'}
                </span>

                {!isCurrent && (
                  <button
                    type="button"
                    disabled={loading}
                    onClick={() => onSelectOption(option)}
                    className="mt-2 px-3 py-1 bg-primary text-on-primary rounded text-label-sm font-label-sm font-semibold hover:bg-primary-container transition-colors disabled:opacity-50 cursor-pointer shadow-sm"
                  >
                    {loading ? 'Applying...' : 'Select Option'}
                  </button>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
