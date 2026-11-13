import React, { useState } from 'react';
import { Icon } from '../common/Icon';
import { buildTravelTips, tipsAsText } from '../../utils/travelTips';
import type { PackageData, PackageItem } from '../../api/types';

interface TravelTipsProps {
  pkg: Partial<PackageData>;
  items: PackageItem[];
}

/** "Before you go": weather, country basics, packing for the planned activities, and group tips. */
export const TravelTips: React.FC<TravelTipsProps> = ({ pkg, items }) => {
  const [copied, setCopied] = useState(false);
  const groups = buildTravelTips(pkg, items);
  if (!groups.length) return null;

  const copy = () => {
    navigator.clipboard
      ?.writeText(tipsAsText(groups))
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      })
      .catch(() => undefined);
  };

  return (
    <section className="bg-white rounded-lg shadow-card p-4" aria-labelledby="tips-title">
      <div className="flex items-center justify-between gap-2">
        <h2 id="tips-title" className="text-lg font-bold text-ink flex items-center gap-2">
          <Icon name="luggage" className="text-brand" />
          Before you go
        </h2>
        <button
          type="button"
          onClick={copy}
          className="no-print h-8 px-2 rounded-md text-sm font-semibold text-brand hover:bg-brand-light flex items-center gap-1"
        >
          <Icon name={copied ? 'check' : 'content_copy'} className="!text-base" />
          {copied ? 'Copied' : 'Copy list'}
        </button>
      </div>
      {groups.map((g) => (
        <div key={g.title} className="mt-3">
          <h3 className="text-sm font-semibold text-ink flex items-center gap-1.5">
            <Icon name={g.icon} className="!text-base text-ink-mute" />
            {g.title}
          </h3>
          <ul className="mt-1 space-y-1 text-sm text-ink-soft list-disc pl-5">
            {g.tips.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
        </div>
      ))}
      <p className="mt-3 text-xs text-ink-mute">Weather is the usual April average, not a forecast.</p>
    </section>
  );
};