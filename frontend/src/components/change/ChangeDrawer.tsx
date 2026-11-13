import React from 'react';
import { OptionList } from './OptionList';
import { Spinner } from '../common/Spinner';
import type { ChangeOption, PackageItem } from '../../api/types';

interface ChangeDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  kind: 'hotel' | 'flight' | 'attraction' | string;
  currentItem?: PackageItem | null;
  options: ChangeOption[];
  onSelectOption: (option: ChangeOption) => void;
  loading?: boolean;
}

export const ChangeDrawer: React.FC<ChangeDrawerProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  kind,
  currentItem,
  options,
  onSelectOption,
  loading = false,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-inverse-surface/40 backdrop-blur-sm p-4">
      <div className="bg-surface-container-lowest rounded-2xl shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Drawer Header */}
        <div className="p-space-lg flex items-center justify-between bg-surface-container-low border-b border-outline-variant/30">
          <div>
            <span className="font-label-sm text-label-sm text-primary uppercase font-bold tracking-wider">
              {kind === 'hotel'
                ? 'Stay Customization'
                : kind === 'flight'
                ? 'Aviation Customization'
                : 'Experience Customization'}
            </span>
            <h2 className="font-headline-md text-headline-md text-on-surface font-bold mt-0.5">
              {title}
            </h2>
            {subtitle && (
              <p className="font-body-sm text-body-sm text-on-surface-variant">{subtitle}</p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-surface-container-lowest flex items-center justify-center text-on-surface-variant hover:text-on-surface transition-colors cursor-pointer"
            aria-label="Close dialog"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        {/* Drawer Content */}
        <div className="p-space-lg overflow-y-auto flex flex-col gap-space-md flex-1">
          {/* Information / Caution Note */}
          <div className="flex items-center gap-space-sm p-space-sm rounded-lg bg-surface-container-high/60 text-on-surface">
            <span className="material-symbols-outlined text-primary text-[20px] shrink-0">info</span>
            <span className="font-body-sm text-body-sm">
              {kind === 'hotel'
                ? 'Modifying this accommodation recalculates total room rates while preserving verified airport transfers.'
                : kind === 'flight'
                ? 'Selecting another flight schedule validates inter-modal transfer buffers and day 1 timeline availability.'
                : 'Attractions are validated against city locations and opening calendar slots.'}
            </span>
          </div>

          {loading ? (
            <div className="py-12 flex justify-center">
              <Spinner label="Retrieving alternative options..." />
            </div>
          ) : (
            <OptionList
              options={options}
              currentCatalogId={currentItem?.catalog_id}
              onSelectOption={onSelectOption}
              loading={loading}
            />
          )}
        </div>

        {/* Drawer Footer */}
        <div className="p-space-md bg-surface-container-low border-t border-outline-variant/30 flex items-center justify-between">
          <span className="font-body-sm text-body-sm text-on-surface-variant">
            All alternatives verified against business constraints
          </span>
          <button
            type="button"
            onClick={onClose}
            className="px-space-md py-2 bg-surface-container-lowest text-on-surface rounded-lg font-label-md text-label-md font-medium hover:bg-surface-container-high transition-colors cursor-pointer"
          >
            Keep Current Selection
          </button>
        </div>
      </div>
    </div>
  );
};
