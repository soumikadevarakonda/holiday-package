import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getReservation } from '../api/reservations';
import { ReservationSummary } from '../components/reservation/ReservationSummary';
import { LookupBox } from '../components/reservation/LookupBox';
import { Spinner } from '../components/common/Spinner';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { ApiError } from '../api/client';
import type { ReservationResponse } from '../api/types';

export const ReservationPage: React.FC = () => {
  const { ref } = useParams<{ ref: string }>();
  const navigate = useNavigate();
  const [reservation, setReservation] = useState<ReservationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [notFoundRef, setNotFoundRef] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setReservation(null);
    setError(null);
    setNotFoundRef(null);
    if (!ref) return;
    if (!/^\d{10}$/.test(ref)) {
      setNotFoundRef(ref);
      return;
    }
    setLoading(true);
    getReservation(ref)
      .then((res) => !cancelled && setReservation(res))
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiError && (err.status === 404 || err.status === 400)) setNotFoundRef(ref);
        else setError(err.message || 'Could not look up the booking');
      })
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [ref]);

  const lookup = (r: string) => navigate(`/reservation/${r}`);

  return (
    <div className="max-w-6xl mx-auto px-4 w-full py-6 flex flex-col gap-6">
      {loading && <Spinner size="lg" label="Finding your booking…" className="py-24" />}
      {error && <ErrorBanner title="Something went wrong" message={error} />}
      {reservation && <ReservationSummary reservation={reservation} />}
      {!loading && (
        <div className={reservation ? 'no-print max-w-xl' : 'max-w-xl mx-auto w-full mt-6'}>
          <LookupBox onLookup={lookup} notFoundRef={notFoundRef} compact={Boolean(reservation)} />
        </div>
      )}
    </div>
  );
};
