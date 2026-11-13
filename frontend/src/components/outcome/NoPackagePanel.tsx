import React from 'react';
import { Icon } from '../common/Icon';

interface NoPackagePanelProps {
  reason?: string;
  onModifyRequest: () => void;
}

/** Shown when no trip can be built at all for this search. */
export const NoPackagePanel: React.FC<NoPackagePanelProps> = ({ reason, onModifyRequest }) => (
  <section className="bg-white rounded-lg shadow-card border-l-4 border-bad p-5 sm:p-6" aria-live="polite">
    <div className="flex items-start gap-3">
      <span className="w-10 h-10 rounded-full bg-bad-light text-bad flex items-center justify-center shrink-0">
        <Icon name="event_busy" />
      </span>
      <div className="flex-1">
        <h2 className="text-lg font-bold text-ink">No trip available for this search</h2>
        <p className="text-sm text-ink-soft mt-1">
          {reason || 'No combination of flights and hotels works for these dates and travelers.'}
        </p>
        <p className="text-sm font-semibold text-ink mt-4">Things to try</p>
        <ul className="mt-1 text-sm text-ink-soft space-y-1">
          <li className="flex gap-2">
            <Icon name="check" className="!text-base text-ok" /> A different start date
          </li>
          <li className="flex gap-2">
            <Icon name="check" className="!text-base text-ok" /> Another departure city
          </li>
          <li className="flex gap-2">
            <Icon name="check" className="!text-base text-ok" /> Fewer travelers in one booking
          </li>
        </ul>
        <button
          type="button"
          onClick={onModifyRequest}
          className="mt-4 h-10 px-4 rounded-md bg-brand hover:bg-brand-dark text-white font-semibold"
        >
          Change search
        </button>
      </div>
    </div>
  </section>
);
