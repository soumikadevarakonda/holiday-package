import React from 'react';

interface ErrorBannerProps {
  title?: string;
  message: string;
  onDismiss?: () => void;
  className?: string;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({
  title = 'Validation or System Alert',
  message,
  onDismiss,
  className = '',
}) => {
  return (
    <div
      className={`bg-error-container/40 border border-error/30 text-on-error-container rounded-xl p-space-md flex items-start gap-space-sm ${className}`}
      role="alert"
    >
      <span className="material-symbols-outlined text-error text-[22px] shrink-0 mt-0.5">
        error
      </span>
      <div className="flex-1">
        <h4 className="font-headline-sm text-headline-sm text-error font-semibold">
          {title}
        </h4>
        <p className="font-body-md text-body-md text-on-surface-variant mt-0.5">
          {message}
        </p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-on-surface-variant hover:text-error transition-colors p-1"
          aria-label="Dismiss alert"
        >
          <span className="material-symbols-outlined text-[18px]">close</span>
        </button>
      )}
    </div>
  );
};
