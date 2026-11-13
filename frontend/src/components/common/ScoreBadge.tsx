import React from 'react';

interface ScoreBadgeProps {
  rating?: number | null;
  stars?: number | null;
  compact?: boolean;
}

const word = (r: number) =>
  r >= 9 ? 'Exceptional' : r >= 8.5 ? 'Excellent' : r >= 8 ? 'Very good' : r >= 7 ? 'Good' : 'Pleasant';

/** Guest rating out of 10 as a score box, with a word and optional hotel stars. */
export const ScoreBadge: React.FC<ScoreBadgeProps> = ({ rating, stars, compact = false }) => {
  if (rating == null && !stars) return null;
  return (
    <div className="flex items-center gap-2">
      {rating != null && !compact && (
        <div className="text-right leading-tight">
          <div className="text-sm font-semibold text-ink">{word(rating)}</div>
          {stars ? <div className="text-xs text-sun">{'★'.repeat(stars)}</div> : null}
        </div>
      )}
      {rating != null && (
        <span className="inline-flex items-center justify-center min-w-[2rem] h-8 px-1.5 rounded-md rounded-bl-none bg-navy text-white text-sm font-bold tabular-nums">
          {rating.toFixed(1)}
        </span>
      )}
      {compact && stars ? <span className="text-xs text-sun">{'★'.repeat(stars)}</span> : null}
    </div>
  );
};
