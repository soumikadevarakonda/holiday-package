import React from 'react';
import { Link } from 'react-router-dom';
import { Icon } from '../components/common/Icon';

export const NotFoundPage: React.FC = () => (
  <div className="max-w-xl mx-auto px-4 py-20 text-center flex flex-col items-center gap-3">
    <span className="w-16 h-16 rounded-full bg-navy-light text-navy flex items-center justify-center">
      <Icon name="travel_explore" className="!text-4xl" />
    </span>
    <h1 className="text-2xl font-bold text-ink">We can't find that page</h1>
    <p className="text-ink-mute">The link may be wrong, or the page has moved.</p>
    <div className="flex gap-2 mt-2">
      <Link to="/" className="h-10 px-4 rounded-md bg-brand hover:bg-brand-dark text-white font-semibold flex items-center">
        Plan a trip
      </Link>
      <Link to="/reservation" className="h-10 px-4 rounded-md border border-brand text-brand font-semibold hover:bg-brand-light flex items-center">
        Find a booking
      </Link>
    </div>
  </div>
);
