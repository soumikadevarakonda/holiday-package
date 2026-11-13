import React, { useEffect, useState } from 'react';
import { Icon } from '../common/Icon';
import { formatINR } from '../../utils/format';

export interface BookerDetails {
  customer_name: string;
  customer_email: string;
  customer_phone?: string;
}

interface ConfirmDialogProps {
  isOpen: boolean;
  total: number;
  defaultName?: string;
  submitting?: boolean;
  error?: string | null;
  onClose: () => void;
  onConfirm: (details: BookerDetails) => void;
}

/** "Your details" step before booking. */
export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  total,
  defaultName = '',
  submitting = false,
  error,
  onClose,
  onConfirm,
}) => {
  const [name, setName] = useState(defaultName);
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [touched, setTouched] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setName(defaultName && defaultName !== 'Traveler' ? defaultName : '');
      setTouched(false);
    }
  }, [isOpen, defaultName]);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && !submitting && onClose();
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [isOpen, submitting, onClose]);

  if (!isOpen) return null;

  const nameErr = !name.trim() ? 'Enter the lead traveler’s name' : '';
  const emailErr = !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim()) ? 'Enter a valid email address' : '';

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setTouched(true);
    if (nameErr || emailErr) return;
    onConfirm({ customer_name: name.trim(), customer_email: email.trim(), customer_phone: phone.trim() || undefined });
  };

  const input = 'mt-1 w-full h-11 px-3 rounded-md border focus:outline-none focus:ring-2 focus:ring-brand';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
      <button type="button" className="absolute inset-0 bg-black/40" aria-label="Close" onClick={() => !submitting && onClose()} />
      <form onSubmit={submit} noValidate className="relative w-full max-w-md bg-white rounded-lg shadow-pop overflow-hidden">
        <div className="p-5 border-b border-line">
          <h2 id="confirm-title" className="text-xl font-bold text-ink">
            Enter your details
          </h2>
          <p className="text-sm text-ink-mute mt-0.5">We’ll put the booking under this name.</p>
        </div>
        <div className="p-5 flex flex-col gap-4">
          <label className="text-sm font-semibold text-ink">
            Full name <span className="text-bad">*</span>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoFocus
              autoComplete="name"
              className={`${input} ${touched && nameErr ? 'border-bad' : 'border-line'}`}
            />
            {touched && nameErr && <span className="block mt-1 text-xs font-normal text-bad">{nameErr}</span>}
          </label>
          <label className="text-sm font-semibold text-ink">
            Email <span className="text-bad">*</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              className={`${input} ${touched && emailErr ? 'border-bad' : 'border-line'}`}
            />
            {touched && emailErr && <span className="block mt-1 text-xs font-normal text-bad">{emailErr}</span>}
          </label>
          <label className="text-sm font-semibold text-ink">
            Phone <span className="font-normal text-ink-mute">(optional)</span>
            <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} autoComplete="tel" className={`${input} border-line`} />
          </label>
          {error && (
            <p className="text-sm text-bad bg-bad-light rounded-md p-3 flex gap-2" role="alert">
              <Icon name="error" filled className="!text-base" />
              {error}
            </p>
          )}
        </div>
        <div className="p-5 bg-canvas flex items-center justify-between gap-3">
          <div>
            <div className="text-xs text-ink-mute">Total to pay</div>
            <div className="text-xl font-extrabold text-ink tabular-nums">{formatINR(total)}</div>
          </div>
          <div className="flex gap-2">
            <button type="button" onClick={onClose} disabled={submitting} className="h-11 px-4 rounded-md text-brand font-semibold hover:bg-brand-light">
              Cancel
            </button>
            <button type="submit" disabled={submitting} className="h-11 px-5 rounded-md bg-brand hover:bg-brand-dark text-white font-bold disabled:opacity-60">
              {submitting ? 'Booking…' : 'Book now'}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
