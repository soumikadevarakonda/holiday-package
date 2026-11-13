import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { PhotoCredits } from './components/common/PhotoCredits';

export const App: React.FC = () => {
  const location = useLocation();

  const isPlanTrip = location.pathname === '/';
  const isActivePackage = location.pathname.startsWith('/package');
  const isReservation = location.pathname.startsWith('/reservation');
  let lastPackage: string | null = null;
  try {
    lastPackage = localStorage.getItem('bmh:lastPackage');
  } catch {
    lastPackage = null;
  }

  return (
    <div className="min-h-screen bg-surface flex flex-col font-body-md text-body-md text-on-surface antialiased">
      {/* Header */}
      <header className="fixed top-0 left-0 w-full z-50 bg-surface-container-lowest/95 backdrop-blur-md border-b border-outline-variant/40">
        <div className="h-16 max-w-7xl mx-auto px-margin flex items-center justify-between gap-space-md">
          <div className="flex items-center gap-space-lg">
            <Link to="/" className="flex items-center gap-space-sm">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-on-primary font-bold">
                <span className="material-symbols-outlined text-[20px]">flight_takeoff</span>
              </div>
              <span className="font-headline-sm text-headline-sm text-on-surface tracking-tight font-bold">
                Build My Holiday
              </span>
            </Link>

            <nav className="hidden md:flex items-center gap-space-md">
              <Link
                to="/"
                className={`transition-colors py-space-xs px-space-xs ${
                  isPlanTrip
                    ? 'text-primary font-semibold'
                    : 'text-on-surface-variant hover:text-on-surface'
                }`}
              >
                Plan Trip
              </Link>
              <Link
                to={lastPackage ? `/package/${lastPackage}` : '/'}
                className={`transition-colors py-space-xs px-space-xs ${
                  isActivePackage
                    ? 'text-primary font-semibold'
                    : 'text-on-surface-variant hover:text-on-surface'
                }`}
              >
                Active Package
              </Link>
              <Link
                to="/reservation"
                className={`transition-colors py-space-xs px-space-xs ${
                  isReservation
                    ? 'text-primary font-semibold'
                    : 'text-on-surface-variant hover:text-on-surface'
                }`}
              >
                Reservation Lookup
              </Link>
            </nav>
          </div>

          <div className="flex items-center gap-space-sm">
            <div className="hidden sm:flex items-center gap-space-xs bg-surface-container-low px-space-sm py-1 rounded-full">
              <span className="material-symbols-outlined text-[16px] text-primary">support_agent</span>
              <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
                Desk 24/7
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
            </div>
            <div className="flex items-center px-space-sm py-1 rounded bg-surface-container-low">
              <span className="font-label-md text-label-md text-on-surface-variant font-medium">
                INR (₹)
              </span>
            </div>
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
              <span className="material-symbols-outlined text-on-primary text-[18px]">person</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Page Area */}
      <main className="w-full pt-16 bg-surface min-h-[calc(100vh-80px)] flex-1 flex flex-col">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="w-full bg-surface-container-lowest border-t border-outline-variant/30 py-space-lg mt-auto">
        <div className="max-w-7xl mx-auto px-margin flex flex-col md:flex-row items-center justify-between gap-space-md font-body-sm text-body-sm text-on-surface-variant">
          <div className="flex flex-wrap items-center gap-space-sm">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-primary"></span>
              <span>Engines Operational</span>
            </span>
            <span className="text-outline-variant">•</span>
            <span>Itinerary Compiler v2.4.9</span>
            <span className="text-outline-variant">•</span>
            <PhotoCredits />
          </div>
          <div className="text-center md:text-right font-label-sm text-label-sm text-on-surface-variant/80">
            All quotes dynamically indexed in INR (₹) inclusive of real-time GST &amp; fuel surcharge buffers.
          </div>
        </div>
      </footer>
    </div>
  );
};
