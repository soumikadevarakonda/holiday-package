import React from 'react';

interface NoPackagePanelProps {
  reason?: string;
  onModifyRequest: () => void;
}

export const NoPackagePanel: React.FC<NoPackagePanelProps> = ({
  reason = 'No flight or accommodation schedules could satisfy your required corridor, passenger sizing, and minimum night distribution rules.',
  onModifyRequest,
}) => {
  return (
    <div className="bg-surface-container-lowest rounded-xl shadow-md p-space-lg lg:p-space-xl border border-error/20 flex flex-col gap-space-md">
      <div className="flex items-start gap-space-md">
        <div className="w-12 h-12 rounded-xl bg-error-container text-error flex items-center justify-center shrink-0">
          <span className="material-symbols-outlined text-[26px]">fmd_bad</span>
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full bg-error/10 text-error font-label-sm text-label-sm uppercase font-semibold">
              Feasibility Conflict
            </span>
            <span className="font-label-sm text-label-sm text-on-surface-variant">
              Engine Code: NO_FEASIBLE_PACKAGE
            </span>
          </div>
          <h3 className="font-headline-lg text-headline-lg text-on-surface mt-1">
            Unable to Compile Package with Current Constraints
          </h3>
          <p className="font-body-md text-body-md text-on-surface-variant mt-1">
            {reason}
          </p>
        </div>
      </div>

      <div className="bg-surface-container-low p-space-md rounded-xl flex items-start gap-space-sm">
        <span className="material-symbols-outlined text-primary text-[20px] shrink-0 mt-0.5">
          lightbulb
        </span>
        <div className="font-body-sm text-body-sm text-on-surface-variant">
          <strong className="text-on-surface block font-medium">Suggested Adjustments:</strong>
          <ul className="list-disc list-inside mt-1 space-y-0.5">
            <li>Ensure departure date is within 1–20 Apr 2027 and total nights do not exceed 20 Apr.</li>
            <li>Try departing from alternate hubs (Mumbai BOM, Delhi DEL, Bengaluru BLR, Chennai MAA).</li>
            <li>Adjust duration to 4–8 nights for optimal flight connection schedules.</li>
          </ul>
        </div>
      </div>

      <div className="flex justify-end pt-space-xs">
        <button
          type="button"
          onClick={onModifyRequest}
          className="px-space-lg py-2.5 rounded-lg bg-primary hover:bg-primary-container text-on-primary font-headline-sm text-headline-sm transition-all shadow-sm"
        >
          Reconfigure Travel Parameters
        </button>
      </div>
    </div>
  );
};
