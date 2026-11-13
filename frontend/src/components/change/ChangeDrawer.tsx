import React, { useEffect, useMemo, useState } from 'react';
import { OptionList } from './OptionList';
import { Spinner } from '../common/Spinner';
import { Icon } from '../common/Icon';
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

type SortKey = 'price' | 'rating' | 'time' | 'name';

const SORTS: Record<string, { key: SortKey; label: string }[]> = {
  hotel: [
    { key: 'price', label: 'Price (lowest first)' },
    { key: 'rating', label: 'Guest rating (highest first)' },
    { key: 'name', label: 'Name (A–Z)' },
  ],
  flight: [
    { key: 'price', label: 'Price (lowest first)' },
    { key: 'time', label: 'Departure time' },
  ],
  attraction: [
    { key: 'time', label: 'Start time' },
    { key: 'price', label: 'Price (lowest first)' },
    { key: 'name', label: 'Name (A–Z)' },
  ],
};

const text = (o: ChangeOption) =>
  [o.name, o.room_type, o.airline, o.category, o.details?.area].filter(Boolean).join(' ').toLowerCase();

/** Side sheet listing alternatives, with search, sort and (for hotels) a "free cancellation" filter. */
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
  const sorts = SORTS[kind] || SORTS.hotel;
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState<SortKey>(sorts[0].key);
  const [refundableOnly, setRefundableOnly] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSort((SORTS[kind] || SORTS.hotel)[0].key);
      setRefundableOnly(false);
    }
  }, [isOpen, kind]);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = options.filter((o) => (!q || text(o).includes(q)) && (!refundableOnly || o.details?.refundable === true));
    const by: Record<SortKey, (a: ChangeOption, b: ChangeOption) => number> = {
      price: (a, b) => a.price_diff - b.price_diff,
      rating: (a, b) => (b.rating ?? 0) - (a.rating ?? 0),
      time: (a, b) => (a.departure_time || a.time_slot || '').localeCompare(b.departure_time || b.time_slot || ''),
      name: (a, b) => a.name.localeCompare(b.name),
    };
    return [...list].sort(by[sort]);
  }, [options, query, sort, refundableOnly]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true" aria-labelledby="drawer-title">
      <button type="button" className="absolute inset-0 bg-black/40" aria-label="Close" onClick={onClose} />
      <div className="relative w-full max-w-xl h-full bg-canvas shadow-pop flex flex-col">
        <div className="bg-white border-b border-line p-4 flex items-start justify-between gap-3">
          <div>
            <h2 id="drawer-title" className="text-xl font-bold text-ink">
              {title}
            </h2>
            {subtitle && <p className="text-sm text-ink-mute mt-0.5">{subtitle}</p>}
          </div>
          <button type="button" onClick={onClose} className="p-2 -m-2 rounded-full hover:bg-canvas text-ink-soft" aria-label="Close">
            <Icon name="close" />
          </button>
        </div>

        <div className="bg-white border-b border-line px-4 pb-3 flex flex-col sm:flex-row gap-2">
          <div className="relative flex-1">
            <Icon name="search" className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-mute" />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={kind === 'hotel' ? 'Search hotel, area or room' : kind === 'flight' ? 'Search airline' : 'Search activity'}
              className="w-full h-10 pl-10 pr-3 rounded-md border border-line focus:outline-none focus:ring-2 focus:ring-brand"
              aria-label="Search options"
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-ink-soft">
            <span className="whitespace-nowrap">Sort by</span>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as SortKey)}
              className="h-10 px-2 rounded-md border border-line bg-white text-ink focus:outline-none focus:ring-2 focus:ring-brand"
            >
              {sorts.map((s) => (
                <option key={s.key} value={s.key}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        {kind === 'hotel' && (
          <label className="bg-white border-b border-line px-4 py-2 flex items-center gap-2 text-sm text-ink-soft">
            <input type="checkbox" checked={refundableOnly} onChange={(e) => setRefundableOnly(e.target.checked)} className="w-4 h-4 accent-brand" />
            Free cancellation only
          </label>
        )}

        <div className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <Spinner label="Finding options…" className="py-16" />
          ) : (
            <>
              <p className="text-sm text-ink-mute mb-3">
                {shown.length} option{shown.length === 1 ? '' : 's'} · prices are the difference to your current trip
              </p>
              <OptionList options={shown} kind={kind} currentCatalogId={currentItem?.catalog_id} onSelectOption={onSelectOption} />
            </>
          )}
        </div>
      </div>
    </div>
  );
};
