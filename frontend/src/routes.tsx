import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { App } from './App';
import { RequestPage } from './pages/RequestPage';
import { PackagePage } from './pages/PackagePage';
import { ReservationPage } from './pages/ReservationPage';
import { NotFoundPage } from './pages/NotFoundPage';

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<App />}>
        <Route index element={<RequestPage />} />
        <Route path="package/:id" element={<PackagePage />} />
        <Route path="reservation/:ref" element={<ReservationPage />} />
        <Route path="reservation" element={<ReservationPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
};
