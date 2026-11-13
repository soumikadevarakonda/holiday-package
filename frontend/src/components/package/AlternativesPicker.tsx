import React from 'react';

interface AlternativesPickerProps {
  onSelectStrategy?: (strategy: 'cheapest' | 'fastest' | 'best_rated') => void;
  activeStrategy?: 'cheapest' | 'fastest' | 'best_rated';
}

export const AlternativesPicker: React.FC<AlternativesPickerProps> = ({
  onSelectStrategy,
  activeStrategy = 'cheapest',
}) => {
  if (!onSelectStrategy) return null;

  return (
    <div className="flex items-center gap-space-xs flex-wrap font-label-md text-label-md">
      <span className="text-on-surface-variant font-label-sm text-label-sm uppercase mr-1">
        Package Focus:
      </span>
      <button
        type="button"
        onClick={() => onSelectStrategy('cheapest')}
        className={`px-3 py-1 rounded-full transition-colors cursor-pointer ${
          activeStrategy === 'cheapest'
            ? 'bg-primary text-on-primary font-semibold'
            : 'bg-surface-container-low text-on-surface-variant hover:text-on-surface'
        }`}
      >
        Cheapest Overall
      </button>
      <button
        type="button"
        onClick={() => onSelectStrategy('fastest')}
        className={`px-3 py-1 rounded-full transition-colors cursor-pointer ${
          activeStrategy === 'fastest'
            ? 'bg-primary text-on-primary font-semibold'
            : 'bg-surface-container-low text-on-surface-variant hover:text-on-surface'
        }`}
      >
        Fastest Transfers
      </button>
      <button
        type="button"
        onClick={() => onSelectStrategy('best_rated')}
        className={`px-3 py-1 rounded-full transition-colors cursor-pointer ${
          activeStrategy === 'best_rated'
            ? 'bg-primary text-on-primary font-semibold'
            : 'bg-surface-container-low text-on-surface-variant hover:text-on-surface'
        }`}
      >
        Best Rated Stays
      </button>
    </div>
  );
};
