import React from 'react';
import { Icon } from './Icon';

type Tone = 'error' | 'warning' | 'info' | 'success';

interface ErrorBannerProps {
  title?: string;
  message: React.ReactNode;
  onDismiss?: () => void;
  className?: string;
  tone?: Tone;
  children?: React.ReactNode;
}

const TONES: Record<Tone, { box: string; icon: string; name: string }> = {
  error: { box: 'bg-bad-light border-bad/30', icon: 'text-bad', name: 'error' },
  warning: { box: 'bg-warn-light border-warn/30', icon: 'text-warn', name: 'warning' },
  info: { box: 'bg-brand-light border-brand/30', icon: 'text-brand', name: 'info' },
  success: { box: 'bg-ok-light border-ok/30', icon: 'text-ok', name: 'check_circle' },
};

/** Inline alert box, used for errors, notices and confirmations. */
export const ErrorBanner: React.FC<ErrorBannerProps> = ({
  title,
  message,
  onDismiss,
  className = '',
  tone = 'error',
  children,
}) => {
  const t = TONES[tone];
  return (
    <div
      className={`border rounded-lg p-4 flex items-start gap-3 ${t.box} ${className}`}
      role={tone === 'error' ? 'alert' : 'status'}
    >
      <Icon name={t.name} filled className={`${t.icon} mt-0.5`} />
      <div className="flex-1 min-w-0">
        {title && <p className="font-semibold text-ink">{title}</p>}
        <div className="text-sm text-ink-soft mt-0.5">{message}</div>
        {children}
      </div>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="text-ink-mute hover:text-ink p-1 -m-1 rounded"
          aria-label="Dismiss"
        >
          <Icon name="close" />
        </button>
      )}
    </div>
  );
};
