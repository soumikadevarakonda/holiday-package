import React from 'react';

interface ChildAgesInputProps {
  childrenCount: number;
  childAges: number[];
  onChange: (count: number, ages: number[]) => void;
  maxChildren?: number;
}

export const ChildAgesInput: React.FC<ChildAgesInputProps> = ({
  childrenCount,
  childAges,
  onChange,
  maxChildren = 5,
}) => {
  const handleCountChange = (delta: number) => {
    const nextCount = Math.max(0, Math.min(maxChildren, childrenCount + delta));
    let nextAges = [...childAges];
    if (nextCount > nextAges.length) {
      while (nextAges.length < nextCount) {
        nextAges.push(7); // Default age 7 as in Stitch
      }
    } else if (nextCount < nextAges.length) {
      nextAges = nextAges.slice(0, nextCount);
    }
    onChange(nextCount, nextAges);
  };

  const handleAgeSelect = (index: number, age: number) => {
    const nextAges = [...childAges];
    nextAges[index] = age;
    onChange(childrenCount, nextAges);
  };

  const handleRemoveChild = (index: number) => {
    const nextAges = childAges.filter((_, i) => i !== index);
    onChange(nextAges.length, nextAges);
  };

  const handleAddChild = () => {
    if (childrenCount < maxChildren) {
      const nextCount = childrenCount + 1;
      const nextAges = [...childAges, 6];
      onChange(nextCount, nextAges);
    }
  };

  return (
    <div className="md:col-span-8 flex flex-col gap-space-xs">
      <div className="flex items-center justify-between">
        <label className="flex items-center gap-1.5 font-label-md text-label-md text-on-surface font-medium">
          <span className="material-symbols-outlined text-[18px] text-primary">child_care</span>
          Children (Age 0 - 11)
        </label>
        <span className="text-primary font-label-sm text-label-sm">
          Ages required for exact child airfare &amp; extra bed
        </span>
      </div>
      <div className="flex flex-wrap items-center gap-space-sm">
        {/* Stepper */}
        <div className="flex items-center justify-between bg-surface-container-lowest rounded-lg p-1.5 shadow-sm min-w-[130px]">
          <button
            type="button"
            className="w-8 h-8 rounded bg-surface-container-low hover:bg-surface-container text-on-surface flex items-center justify-center transition-colors disabled:opacity-40"
            onClick={() => handleCountChange(-1)}
            disabled={childrenCount <= 0}
          >
            <span className="material-symbols-outlined text-[16px]">remove</span>
          </button>
          <span className="w-14 text-center font-currency-md text-currency-md text-on-surface">
            {childrenCount} {childrenCount === 1 ? 'Child' : 'Children'}
          </span>
          <button
            type="button"
            className="w-8 h-8 rounded bg-surface-container-low hover:bg-surface-container text-on-surface flex items-center justify-center transition-colors disabled:opacity-40"
            onClick={() => handleCountChange(1)}
            disabled={childrenCount >= maxChildren}
          >
            <span className="material-symbols-outlined text-[16px]">add</span>
          </button>
        </div>

        {/* Dynamic Children Age Badges */}
        <div className="flex flex-wrap items-center gap-space-xs">
          {childAges.map((age, idx) => (
            <div
              key={idx}
              className="flex items-center gap-2 bg-surface-container-lowest px-space-sm py-1 rounded-lg shadow-sm"
            >
              <span className="font-label-sm text-label-sm text-on-surface-variant uppercase">
                Child {idx + 1}
              </span>
              <div className="relative">
                <select
                  value={age}
                  onChange={(e) => handleAgeSelect(idx, parseInt(e.target.value, 10))}
                  className="bg-surface-container-low font-label-md text-label-md text-on-surface rounded px-2 py-0.5 pr-6 appearance-none focus:outline-none cursor-pointer"
                >
                  {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map((a) => (
                    <option key={a} value={a}>
                      Age {a}
                    </option>
                  ))}
                </select>
                <span className="material-symbols-outlined absolute right-1 top-1 pointer-events-none text-on-surface-variant text-[14px]">
                  expand_more
                </span>
              </div>
              <span className="px-1.5 py-0.5 rounded bg-primary-fixed text-on-primary-fixed font-label-sm text-label-sm">
                Child Fare ({age < 2 ? 'Infant' : '75%'})
              </span>
              <button
                type="button"
                onClick={() => handleRemoveChild(idx)}
                className="text-on-surface-variant hover:text-error transition-colors"
                title="Remove child"
              >
                <span className="material-symbols-outlined text-[16px]">close</span>
              </button>
            </div>
          ))}
        </div>

        {childrenCount < maxChildren && (
          <button
            type="button"
            onClick={handleAddChild}
            className="inline-flex items-center gap-1 px-space-sm py-1.5 rounded-lg bg-surface-container-lowest hover:bg-surface-container text-primary font-label-md text-label-md shadow-sm transition-colors"
          >
            <span className="material-symbols-outlined text-[16px]">add</span>
            Add Child
          </button>
        )}
      </div>
      <span className="font-body-sm text-body-sm text-on-surface-variant">
        Includes verified juvenile pass tiers and child baggage allocations
      </span>
    </div>
  );
};
