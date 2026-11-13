import React, { useState } from 'react';

interface PhotoProps {
  src?: string | null;
  alt: string;
  className?: string;
  fallbackType?: 'hotel' | 'attraction' | 'city';
}

export const Photo: React.FC<PhotoProps> = ({
  src,
  alt,
  className = '',
  fallbackType = 'hotel',
}) => {
  const [hasError, setHasError] = useState(false);

  // Normalize src
  let finalSrc = src;
  if (finalSrc && !finalSrc.startsWith('http') && !finalSrc.startsWith('/')) {
    finalSrc = `/${finalSrc}`;
  }

  if (!finalSrc || hasError) {
    const icon =
      fallbackType === 'hotel'
        ? 'apartment'
        : fallbackType === 'attraction'
        ? 'local_activity'
        : 'landscape';

    return (
      <div
        className={`bg-surface-container-high flex flex-col items-center justify-center text-outline-variant ${className}`}
        aria-label={alt}
      >
        <span className="material-symbols-outlined text-[32px]">{icon}</span>
        <span className="font-label-sm text-label-sm mt-1 text-center px-2 line-clamp-1">{alt}</span>
      </div>
    );
  }

  return (
    <img
      src={finalSrc}
      alt={alt}
      className={className}
      onError={() => setHasError(true)}
      loading="lazy"
    />
  );
};
