import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getReservation } from '../api/reservations';
import { ReservationSummary } from '../components/reservation/ReservationSummary';
import { LookupBox } from '../components/reservation/LookupBox';
import { Spinner } from '../components/common/Spinner';
import type { ReservationResponse } from '../api/types';

export const ReservationPage: React.FC = () => {
  const { ref } = useParams<{ ref: string }>();
  const navigate = useNavigate();

  const [reservation, setReservation] = useState<ReservationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [notFoundRef, setNotFoundRef] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!ref || !/^\d{10}$/.test(ref)) {
        setReservation(null);
        setNotFoundRef(ref && ref !== 'lookup' ? ref : null);
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        setNotFoundRef(null);
        const res = await getReservation(ref);
        if (!cancelled) {
          setReservation(res);
        }
      } catch (err: any) {
        if (!cancelled) {
          setReservation(null);
          setNotFoundRef(ref);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [ref]);

  const handleLookup = (searchRef: string) => {
    navigate(`/reservation/${searchRef}`);
  };

  if (loading) {
    return (
      <div className="w-full min-h-[60vh] flex flex-col items-center justify-center gap-space-md">
        <Spinner size="lg" label="Searching Central Reservation Vault..." />
        <span className="font-body-sm text-body-sm text-on-surface-variant">
          Locating 10-digit reservation record #{ref}
        </span>
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col">
      {/* Top Status & Dossier Quick Action Bar */}
      <div className="w-full bg-surface-container-low px-space-md py-space-sm">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-space-sm font-label-md text-label-md">
          <div className="flex items-center gap-space-xs text-on-surface-variant">
            <span className="material-symbols-outlined text-[16px] text-primary">verified</span>
            <span>Registry ID:</span>
            <span className="font-currency-md text-on-surface font-semibold tracking-wide">
              {reservation ? `BMH-${reservation.reference}` : 'Lookup Mode'}
            </span>
            <span className="text-outline-variant">•</span>
            <span className="text-primary font-medium">Vault Connected</span>
          </div>
          <div className="flex items-center gap-space-md">
            <button
              type="button"
              onClick={() => window.print()}
              className="flex items-center gap-1.5 text-on-surface-variant hover:text-primary transition-colors cursor-pointer"
            >
              <span className="material-symbols-outlined text-[16px]">print</span>
              <span>Dossier Print</span>
            </button>
            <span className="text-outline-variant">|</span>
            <div className="flex items-center gap-1.5 text-on-surface-variant">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
              <span>Central Ledger Active</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto w-full px-space-md lg:px-margin py-space-lg flex flex-col gap-space-xl">
        {/* If reservation is found, display full confirmed itinerary */}
        {reservation && <ReservationSummary reservation={reservation} />}

        {/* Lookup Box: Handles finding other reservations or showing not-found state */}
        <LookupBox
          onLookup={handleLookup}
          notFoundRef={notFoundRef}
          activeRef={reservation?.reference}
        />
      </div>
    </div>
  );
};
