import React from 'react';

type Strategy = 'cheapest' | 'fastest' | 'best_rated';

interface AlternativesPickerProps {
  onSelectStrategy?: (strategy: Strategy) => void;
  activeStrategy?: Strategy;
}

const LABELS: Record<Strategy, string> = { cheapest: 'Cheapest', fastest: 'Fastest', best_rated: 'Best rated' };

/** G4 tabs: cheapest / fastest / best rated (shown only when a handler is passed). */
export const AlternativesPicker: React.FC<AlternativesPickerProps> = ({ onSelectStrategy, activeStrategy = 'cheapest' }) => {
  if (!onSelectStrategy) return null;
  return (
    <div className="inline-flex rounded-md border border-line bg-white overflow-hidden" role="tablist">
      {(Object.keys(LABELS) as Strategy[]).map((s) => (
        <button
          key={s}
          type="button"
          role="tab"
          aria-selected={activeStrategy === s}
          onClick={() => onSelectStrategy(s)}
          className={`h-10 px-4 text-sm font-semibold ${
            activeStrategy === s ? 'bg-brand text-white' : 'text-ink-soft hover:bg-canvas'
          }`}
        >
          {LABELS[s]}
        </button>
      ))}
    </div>
  );
};
