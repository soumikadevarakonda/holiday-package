import React from 'react';
import { ErrorBanner } from '../common/ErrorBanner';

interface SideEffectsAlertProps {
  sideEffects?: string[];
  warnings?: string[];
  className?: string;
  onDismiss?: () => void;
}

/** What else changed after an edit (e.g. a transfer re-timed), plus any warnings. */
export const SideEffectsAlert: React.FC<SideEffectsAlertProps> = ({ sideEffects = [], warnings = [], className = '', onDismiss }) => {
  if (sideEffects.length === 0 && warnings.length === 0) return null;
  return (
    <ErrorBanner
      tone={warnings.length ? 'warning' : 'success'}
      title="Your trip was updated"
      className={className}
      onDismiss={onDismiss}
      message={
        <ul className="space-y-0.5">
          {sideEffects.map((s, i) => (
            <li key={`s${i}`}>{s}</li>
          ))}
          {warnings.map((w, i) => (
            <li key={`w${i}`} className="text-warn">
              {w}
            </li>
          ))}
        </ul>
      }
    />
  );
};
