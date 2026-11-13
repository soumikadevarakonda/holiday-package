import React from 'react';
import { Photo } from '../common/Photo';
import { Icon } from '../common/Icon';
import { ScoreBadge } from '../common/ScoreBadge';
import { formatDate, formatINR } from '../../utils/format';
import type { PackageItem } from '../../api/types';

interface ItemRowProps {
  item: PackageItem;
  city?: string;
  onChangeClick?: (item: PackageItem) => void;
  onRemoveClick?: (item: PackageItem) => void;
  readOnly?: boolean;
}

export function formatDuration(minutes?: number): string {
  if (!minutes) return '';
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h ? `${h}h${m ? ` ${m}m` : ''}` : `${m}m`;
}

const time = (s?: string) => (s && s.includes('T') ? s.slice(11, 16) : '');
const pretty = (s?: string) => (s || '').replace(/_/g, ' ').toLowerCase();

const TYPE_STYLE: Record<string, { label: string; icon: string; chip: string }> = {
  flight: { label: 'Flight', icon: 'flight', chip: 'bg-brand-light text-brand' },
  hotel: { label: 'Stay', icon: 'hotel', chip: 'bg-navy-light text-navy' },
  transfer: { label: 'Transfer', icon: 'directions_bus', chip: 'bg-canvas text-ink-soft' },
  attraction: { label: 'Activity', icon: 'attractions', chip: 'bg-ok-light text-ok' },
};

const Price: React.FC<{ amount: number; note?: string }> = ({ amount, note }) => (
  <div className="text-right">
    <div className="text-lg font-bold text-ink tabular-nums">{amount === 0 ? 'Free' : formatINR(amount)}</div>
    {note && <div className="text-xs text-ink-mute">{note}</div>}
  </div>
);

const ActionButton: React.FC<{ onClick: () => void; children: React.ReactNode; tone?: 'primary' | 'danger' }> = ({
  onClick,
  children,
  tone = 'primary',
}) => (
  <button
    type="button"
    onClick={onClick}
    className={
      tone === 'danger'
        ? 'h-9 px-3 rounded-md text-sm font-semibold text-bad hover:bg-bad-light'
        : 'h-9 px-3 rounded-md text-sm font-semibold border border-brand text-brand hover:bg-brand-light'
    }
  >
    {children}
  </button>
);

/** One booked part of the trip: flight, hotel stay, transfer or activity. */
export const ItemRow: React.FC<ItemRowProps> = ({ item, city, onChangeClick, onRemoveClick, readOnly = false }) => {
  const type = (item.type || '').toLowerCase();
  const style = TYPE_STYLE[type] || TYPE_STYLE.transfer;
  const price = item.price_inr ?? item.price ?? 0;
  const qty = item.quantity ?? 1;
  const canChange = !readOnly && onChangeClick && (type === 'flight' || type === 'hotel');
  const canRemove = !readOnly && onRemoveClick && type === 'attraction';

  const Label = (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold ${style.chip}`}>
      <Icon name={style.icon} className="!text-sm" />
      {type === 'flight' ? (item.leg === 'return' ? 'Flight home' : 'Flight out') : type === 'transfer' && item.intercity ? 'Train between cities' : style.label}
    </span>
  );

  // ---------------------------------------------------------------- flight
  if (type === 'flight') {
    return (
      <article className="bg-white border border-line rounded-lg p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            {Label}
            <span className="text-sm text-ink-soft">
              {item.airline} · {item.flight_number || item.catalog_id}
            </span>
          </div>
          <Price amount={price} note={`${qty} seat${qty > 1 ? 's' : ''}`} />
        </div>
        <div className="mt-3 grid grid-cols-[auto_1fr_auto] items-center gap-3">
          <div>
            <div className="text-2xl font-bold text-ink tabular-nums">{time(item.start)}</div>
            <div className="text-sm text-ink-soft">{item.from_airport}</div>
            <div className="text-xs text-ink-mute">{formatDate(item.start)}</div>
          </div>
          <div className="flex flex-col items-center text-xs text-ink-mute">
            <span>{formatDuration(item.duration_minutes)}</span>
            <div className="w-full flex items-center gap-1 my-1">
              <span className="h-px flex-1 bg-line" />
              <Icon name="flight" className="!text-base text-ink-mute rotate-90" />
              <span className="h-px flex-1 bg-line" />
            </div>
            <span className={item.stops ? 'text-warn' : 'text-ok'}>
              {item.stops ? `${item.stops} stop${item.stops > 1 ? 's' : ''}` : 'Direct'}
            </span>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-ink tabular-nums">{time(item.end)}</div>
            <div className="text-sm text-ink-soft">{item.to_airport}</div>
            <div className="text-xs text-ink-mute">{formatDate(item.end)}</div>
          </div>
        </div>
        <div className="mt-3 pt-3 border-t border-line flex flex-wrap items-center justify-between gap-2">
          <span className="text-xs text-ink-mute">Local times · {pretty(item.details?.cabin) || 'economy'}</span>
          {canChange && <ActionButton onClick={() => onChangeClick!(item)}>Change flight</ActionButton>}
        </div>
      </article>
    );
  }

  // ---------------------------------------------------------------- hotel
  if (type === 'hotel') {
    const nights = item.nights;
    return (
      <article className="bg-white border border-line rounded-lg overflow-hidden flex flex-col sm:flex-row">
        <Photo src={item.image} alt={item.hotel_name || item.name || 'Hotel'} className="w-full sm:w-48 h-44 sm:h-auto object-cover shrink-0" />
        <div className="flex-1 p-4 flex flex-col gap-2 min-w-0">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              {Label}
              <h3 className="mt-1 text-lg font-bold text-brand leading-snug">{item.hotel_name || item.name}</h3>
              <p className="text-sm text-ink-soft flex items-center gap-1">
                <Icon name="location_on" className="!text-base" />
                {item.area ? `${item.area}, ` : ''}
                {item.city || city}
              </p>
            </div>
            <ScoreBadge rating={item.rating} stars={item.stars} />
          </div>
          <ul className="text-sm text-ink-soft space-y-0.5">
            <li>
              <span className="font-semibold text-ink">
                {qty > 1 ? `${qty} × ` : ''}
                {item.room_name || 'Room'}
              </span>
              {item.details?.refundable === false && <span className="text-ink-mute"> · non-refundable</span>}
              {item.details?.refundable === true && <span className="text-ok"> · free cancellation</span>}
            </li>
            <li>
              {formatDate(item.start)} – {formatDate(item.end)}
              {nights ? ` · ${nights} night${nights > 1 ? 's' : ''}` : ''}
            </li>
            {item.details?.check_in_from && (
              <li className="text-ink-mute">
                Check-in from {item.details.check_in_from} · check-out by {item.details.check_out_until}
              </li>
            )}
          </ul>
          <div className="mt-auto flex flex-wrap items-end justify-between gap-2 pt-2">
            {canChange ? <ActionButton onClick={() => onChangeClick!(item)}>Change hotel</ActionButton> : <span />}
            <Price amount={price} note={nights ? `${nights} night${nights > 1 ? 's' : ''}, ${qty} room${qty > 1 ? 's' : ''}` : undefined} />
          </div>
        </div>
      </article>
    );
  }

  // ---------------------------------------------------------------- attraction
  if (type === 'attraction') {
    return (
      <article className="bg-white border border-line rounded-lg p-3 flex gap-3">
        <Photo src={item.image} alt={item.name || 'Activity'} fallbackType="attraction" className="w-20 h-20 sm:w-24 sm:h-24 rounded-md object-cover shrink-0" />
        <div className="flex-1 min-w-0 flex flex-col">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              {Label}
              <h3 className="mt-1 font-bold text-ink leading-snug">{item.name}</h3>
              <p className="text-sm text-ink-soft">
                {item.time_slot}
                {item.category ? ` · ${pretty(item.category)}` : ''}
                {item.details?.visit_minutes ? ` · about ${formatDuration(item.details.visit_minutes)}` : ''}
              </p>
            </div>
            <Price amount={price} note={price ? `${qty} ticket${qty > 1 ? 's' : ''}` : undefined} />
          </div>
          {canRemove && (
            <div className="mt-auto pt-2 flex justify-end">
              <ActionButton tone="danger" onClick={() => onRemoveClick!(item)}>
                <Icon name="delete" className="!text-base mr-1" />
                Remove
              </ActionButton>
            </div>
          )}
        </div>
      </article>
    );
  }

  // ---------------------------------------------------------------- transfer
  return (
    <article className="bg-white border border-line rounded-lg p-3 flex gap-3 items-start">
      <span className="w-12 h-12 rounded-full bg-canvas text-ink-soft flex items-center justify-center shrink-0">
        <Icon name={item.intercity ? 'train' : pretty(item.transfer_type).includes('taxi') ? 'local_taxi' : 'directions_bus'} />
      </span>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            {Label}
            <h3 className="mt-1 font-semibold text-ink leading-snug">{item.name}</h3>
            <p className="text-sm text-ink-soft">
              {time(item.start)}
              {item.end ? `–${time(item.end)}` : ''}
              {item.from_location && item.to_location ? ` · ${item.from_location} → ${item.to_location}` : ''}
            </p>
          </div>
          <Price amount={price} note={qty > 1 ? `${qty} tickets/vehicles` : undefined} />
        </div>
      </div>
    </article>
  );
};
