import React, { useState } from 'react';
import { Icon } from './Icon';

type Kind = 'hotel' | 'attraction' | 'city' | 'flight' | 'transfer';

interface PhotoProps {
  src?: string | null;
  alt: string;
  className?: string;
  fallbackType?: Kind;
}

const FALLBACK_ICON: Record<Kind, string> = {
  hotel: 'hotel',
  attraction: 'attractions',
  city: 'location_city',
  flight: 'flight',
  transfer: 'directions_bus',
};

/** Catalog photo served by the backend at /images/...; shows an icon tile when there is none. */
export const Photo: React.FC<PhotoProps> = ({ src, alt, className = '', fallbackType = 'hotel' }) => {
  const [hasError, setHasError] = useState(false);
  const finalSrc = src && !src.startsWith('http') && !src.startsWith('/') ? `/${src}` : src;

  if (!finalSrc || hasError) {
    return (
      <div className={`bg-navy-light text-navy flex items-center justify-center ${className}`} role="img" aria-label={alt}>
        <Icon name={FALLBACK_ICON[fallbackType]} className="!text-3xl" />
      </div>
    );
  }
  return <img src={finalSrc} alt={alt} className={className} onError={() => setHasError(true)} loading="lazy" />;
};
