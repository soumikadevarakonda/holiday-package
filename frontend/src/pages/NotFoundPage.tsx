import React from 'react';
import { useNavigate } from 'react-router-dom';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="w-full max-w-3xl mx-auto px-margin py-space-xl flex flex-col items-center justify-center text-center gap-space-md min-h-[50vh]">
      <div className="w-16 h-16 rounded-2xl bg-surface-container-high flex items-center justify-center text-primary">
        <span className="material-symbols-outlined text-[36px]">travel_explore</span>
      </div>
      <h1 className="font-headline-xl text-headline-xl text-on-surface font-bold">
        Page Not Found
      </h1>
      <p className="font-body-lg text-body-lg text-on-surface-variant max-w-md">
        The requested itinerary or route could not be found. Please return to the holiday planner or check your reservation reference.
      </p>
      <div className="flex gap-space-sm pt-space-xs">
        <button
          type="button"
          onClick={() => navigate('/')}
          className="px-space-lg py-2.5 rounded-lg bg-primary text-on-primary font-headline-sm text-headline-sm shadow-sm hover:bg-primary-container transition-colors cursor-pointer"
        >
          Plan a Holiday
        </button>
      </div>
    </div>
  );
};
