import React from 'react';
import { Outlet, Link, NavLink, useLocation } from 'react-router-dom';
import { PhotoCredits } from './components/common/PhotoCredits';
import { Icon } from './components/common/Icon';

function lastPackageId(): string | null {
  try {
    return localStorage.getItem('bmh:lastPackage');
  } catch {
    return null;
  }
}

const navClass = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-1.5 px-3 py-2 rounded-full text-sm font-medium transition-colors ${
    isActive ? 'bg-white/15 text-white ring-1 ring-white/60' : 'text-white/90 hover:bg-white/10'
  }`;

export const App: React.FC = () => {
  useLocation(); // re-render on navigation so "My trip" appears as soon as a package is opened
  const lastPackage = lastPackageId();

  return (
    <div className="min-h-screen flex flex-col bg-canvas">
      <header className="bg-navy text-white">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-2 shrink-0" aria-label="Build My Holiday home">
            <span className="w-8 h-8 rounded-lg bg-white text-navy flex items-center justify-center">
              <Icon name="travel" filled />
            </span>
            <span className="text-lg sm:text-xl font-extrabold tracking-tight">Build My Holiday</span>
          </Link>

          <nav className="flex items-center gap-1" aria-label="Main">
            <NavLink to="/" end className={navClass}>
              <Icon name="search" />
              <span className="hidden sm:inline">Plan a trip</span>
            </NavLink>
            {lastPackage && (
              <NavLink to={`/package/${lastPackage}`} className={navClass}>
                <Icon name="luggage" />
                <span className="hidden sm:inline">My trip</span>
              </NavLink>
            )}
            <NavLink to="/reservation" className={navClass}>
              <Icon name="confirmation_number" />
              <span className="hidden sm:inline">Find a booking</span>
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="flex-1 flex flex-col">
        <Outlet />
      </main>

      <footer className="bg-white border-t border-line mt-12">
        <div className="max-w-6xl mx-auto px-4 py-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-sm text-ink-mute">
          <p>Flights, hotels, transfers and activities in one trip • Japan and UAE • 1–20 April 2027</p>
          <div className="flex items-center gap-4">
            <span>All prices in INR (₹)</span>
            <PhotoCredits />
          </div>
        </div>
      </footer>
    </div>
  );
};
