import React from 'react';

interface SideEffectsAlertProps {
  sideEffects?: string[];
  warnings?: string[];
  className?: string;
}

export const SideEffectsAlert: React.FC<SideEffectsAlertProps> = ({
  sideEffects = [],
  warnings = [],
  className = '',
}) => {
  if (sideEffects.length === 0 && warnings.length === 0) return null;

  return (
    <div className={`flex flex-col gap-space-xs p-space-sm rounded-lg bg-surface-container-high/60 text-on-surface ${className}`}>
      <div className="flex items-center gap-space-xs text-primary font-semibold font-label-md text-label-md">
        <span className="material-symbols-outlined text-[18px]">info</span>
        <span>Schedule Updates &amp; Notices (G1)</span>
      </div>
      {sideEffects.map((effect, idx) => (
        <p key={idx} className="font-body-sm text-body-sm text-on-surface-variant">
          • {effect}
        </p>
      ))}
      {warnings.map((warn, idx) => (
        <p key={idx} className="font-body-sm text-body-sm text-tertiary">
          ⚠ {warn}
        </p>
      ))}
    </div>
  );
};
