import React from 'react';

interface IconProps {
  name: string;
  className?: string;
  filled?: boolean;
  title?: string;
}

/** Material Symbols icon. Decorative unless a title is given. */
export const Icon: React.FC<IconProps> = ({ name, className = '', filled = false, title }) => (
  <span
    className={`material-symbols-outlined ${filled ? 'icon-fill' : ''} ${className}`}
    aria-hidden={title ? undefined : true}
    title={title}
  >
    {name}
  </span>
);
