import React, { useState } from 'react';

export const PhotoCredits: React.FC = () => {
  const [open, setOpen] = useState(false);

  return (
    <div className="inline-block">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="font-label-sm text-label-sm text-on-surface-variant hover:text-primary underline transition-colors"
      >
        Photo Attributions &amp; Licensing
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-inverse-surface/40 backdrop-blur-sm p-4">
          <div className="bg-surface-container-lowest rounded-xl shadow-xl max-w-lg w-full p-space-lg flex flex-col gap-space-md">
            <div className="flex items-center justify-between">
              <h3 className="font-headline-sm text-headline-sm text-on-surface font-bold">
                Catalogue Image Attributions
              </h3>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="w-8 h-8 rounded-full bg-surface-container-low flex items-center justify-center text-on-surface-variant hover:text-on-surface"
              >
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
            <div className="font-body-sm text-body-sm text-on-surface-variant max-h-60 overflow-y-auto space-y-2">
              <p>
                All imagery presented across itineraries is sourced via official destination authorities, licensed Unsplash creative partners, and Open Heritage media archives under Creative Commons attribution.
              </p>
              <p>
                Hotels and attractions comply with tourism board representations for Japan and UAE corridors. Full license references are available in the repository catalogue attributions registry.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="px-space-md py-2 rounded-lg bg-primary text-on-primary font-label-md text-label-md self-end"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
