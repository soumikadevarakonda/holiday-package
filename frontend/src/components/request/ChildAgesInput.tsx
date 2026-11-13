import React from 'react';
import { Icon } from '../common/Icon';

interface StepperProps {
  label: string;
  hint?: string;
  value: number;
  min: number;
  max: number;
  onChange: (v: number) => void;
}

export const Stepper: React.FC<StepperProps> = ({ label, hint, value, min, max, onChange }) => (
  <div className="flex items-center justify-between gap-4 py-2">
    <div>
      <div className="font-medium text-ink">{label}</div>
      {hint && <div className="text-xs text-ink-mute">{hint}</div>}
    </div>
    <div className="flex items-center border border-line rounded-md">
      <button
        type="button"
        onClick={() => onChange(Math.max(min, value - 1))}
        disabled={value <= min}
        className="w-10 h-10 flex items-center justify-center text-brand disabled:text-ink-mute/40"
        aria-label={`Fewer ${label.toLowerCase()}`}
      >
        <Icon name="remove" />
      </button>
      <span className="w-8 text-center font-semibold tabular-nums" aria-live="polite">
        {value}
      </span>
      <button
        type="button"
        onClick={() => onChange(Math.min(max, value + 1))}
        disabled={value >= max}
        className="w-10 h-10 flex items-center justify-center text-brand disabled:text-ink-mute/40"
        aria-label={`More ${label.toLowerCase()}`}
      >
        <Icon name="add" />
      </button>
    </div>
  </div>
);

interface ChildAgesInputProps {
  childrenCount: number;
  childAges: number[];
  onChange: (count: number, ages: number[]) => void;
  maxChildren?: number;
}

/** Children stepper plus one age picker per child (ages matter for child fares and room sizes). */
export const ChildAgesInput: React.FC<ChildAgesInputProps> = ({
  childrenCount,
  childAges,
  onChange,
  maxChildren = 8,
}) => {
  const setCount = (n: number) => {
    const ages = childAges.slice(0, n);
    while (ages.length < n) ages.push(6);
    onChange(n, ages);
  };
  const setAge = (i: number, age: number) => {
    const ages = [...childAges];
    ages[i] = age;
    onChange(childrenCount, ages);
  };

  return (
    <div>
      <Stepper label="Children" hint="Ages 0–17" value={childrenCount} min={0} max={maxChildren} onChange={setCount} />
      {childrenCount > 0 && (
        <div className="grid grid-cols-2 gap-2 pt-1 pb-2">
          {childAges.slice(0, childrenCount).map((age, i) => (
            <label key={i} className="text-xs text-ink-mute">
              Child {i + 1} age
              <select
                value={age}
                onChange={(e) => setAge(i, Number(e.target.value))}
                className="mt-1 w-full h-9 border border-line rounded-md px-2 text-sm text-ink bg-white focus:outline-none focus:ring-2 focus:ring-brand"
              >
                {Array.from({ length: 18 }, (_, a) => (
                  <option key={a} value={a}>
                    {a} {a === 1 ? 'year' : 'years'}
                  </option>
                ))}
              </select>
            </label>
          ))}
        </div>
      )}
    </div>
  );
};
