import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { usePackage } from '../hooks/usePackage';
import { CityPlanHeader } from '../components/package/CityPlanHeader';
import { DayTimeline } from '../components/package/DayTimeline';
import { PriceBreakdown } from '../components/package/PriceBreakdown';
import { CityPlanPicker } from '../components/package/CityPlanPicker';
import { ChangeDrawer } from '../components/change/ChangeDrawer';
import { SideEffectsAlert } from '../components/change/SideEffectsAlert';
import { ErrorBanner } from '../components/common/ErrorBanner';
import { Spinner } from '../components/common/Spinner';
import { confirmPackage } from '../api/reservations';
import {
  getHotelOptions,
  getFlightOptions,
  getAttractionOptions,
  getExportPackageUrl,
} from '../api/packages';
import type { PackageItem, ChangeOption, TimelineDay } from '../api/types';

export const PackagePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const {
    data: packageRes,
    loading,
    error,
    actionLoading,
    warnings,
    sideEffects,
    applyChange,
    rebuild,
  } = usePackage(id);

  // Change modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalKind, setModalKind] = useState<'hotel' | 'flight' | 'attraction'>('hotel');
  const [modalTitle, setModalTitle] = useState('');
  const [modalSubtitle, setModalSubtitle] = useState<string | undefined>();
  const [modalItem, setModalItem] = useState<PackageItem | null>(null);
  const [modalOptions, setModalOptions] = useState<ChangeOption[]>([]);
  const [modalLoading, setModalLoading] = useState(false);
  const [activeDayDate, setActiveDayDate] = useState<string | undefined>();

  // Confirmation state
  const [confirming, setConfirming] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Handle open Change Hotel
  const handleChangeHotel = async (item: PackageItem) => {
    if (!id) return;
    setModalKind('hotel');
    setModalItem(item);
    setModalTitle(`Alternative Hotels for ${item.city || 'Stay'}`);
    setModalSubtitle(`${item.nights || 4} Nights • Verified Room Allocations`);
    setIsModalOpen(true);
    try {
      setModalLoading(true);
      const res = await getHotelOptions(id, item.city);
      setModalOptions(res.options || []);
    } catch (err: any) {
      setActionError(err.message || 'Failed to fetch hotel alternatives');
    } finally {
      setModalLoading(false);
    }
  };

  // Handle open Change Flight
  const handleChangeFlight = async (item: PackageItem) => {
    if (!id) return;
    const isArrival = item.start ? true : false;
    const leg = isArrival ? 'arrival' : 'return';
    setModalKind('flight');
    setModalItem(item);
    setModalTitle(`Alternative Flights (${leg === 'arrival' ? 'Outbound' : 'Inbound'})`);
    setModalSubtitle('Direct & 1-stop scheduled departures');
    setIsModalOpen(true);
    try {
      setModalLoading(true);
      const res = await getFlightOptions(id, leg);
      setModalOptions(res.options || []);
    } catch (err: any) {
      setActionError(err.message || 'Failed to fetch flight alternatives');
    } finally {
      setModalLoading(false);
    }
  };

  // Handle open Add Attraction
  const handleAddAttraction = async (day: TimelineDay) => {
    if (!id) return;
    setActiveDayDate(day.date);
    const dayCity = packageRes?.package_data?.cities?.[0] || 'Tokyo';
    setModalKind('attraction');
    setModalItem(null);
    setModalTitle(`Add Experience to Day ${day.day_number}`);
    setModalSubtitle(`Available excursions for ${dayCity} on ${day.date?.slice(0, 10)}`);
    setIsModalOpen(true);
    try {
      setModalLoading(true);
      const res = await getAttractionOptions(id, day.date?.slice(0, 10), dayCity);
      setModalOptions(res.options || []);
    } catch (err: any) {
      setActionError(err.message || 'Failed to fetch attraction options');
    } finally {
      setModalLoading(false);
    }
  };

  // Handle item change click dispatch
  const handleChangeClick = (item: PackageItem) => {
    if (item.type === 'flight') {
      handleChangeFlight(item);
    } else if (item.type === 'hotel') {
      handleChangeHotel(item);
    }
  };

  // Handle remove attraction
  const handleRemoveAttraction = async (item: PackageItem) => {
    if (!id) return;
    try {
      setActionError(null);
      await applyChange({
        kind: 'attraction',
        current_item_id: item.item_id,
        new_catalog_id: '',
        params: { action: 'remove', item_id: item.item_id },
      });
    } catch (err: any) {
      setActionError(err.message || 'Failed to remove attraction');
    }
  };

  // Handle option selected from modal
  const handleSelectOption = async (option: ChangeOption) => {
    if (!id) return;
    try {
      setActionError(null);
      setIsModalOpen(false);

      if (modalKind === 'hotel') {
        await applyChange({
          kind: 'hotel',
          current_item_id: modalItem?.item_id,
          new_catalog_id: option.catalog_id,
          params: {
            city: modalItem?.city,
            room_id: option.room_id,
          },
        });
      } else if (modalKind === 'flight') {
        await applyChange({
          kind: 'flight',
          current_item_id: modalItem?.item_id,
          new_catalog_id: option.catalog_id,
          params: {
            leg: 'arrival',
          },
        });
      } else if (modalKind === 'attraction') {
        await applyChange({
          kind: 'attraction',
          new_catalog_id: option.catalog_id,
          params: {
            action: 'add',
            date: activeDayDate,
          },
        });
      }
    } catch (err: any) {
      setActionError(err.message || 'Failed to apply selected change');
    }
  };

  // Handle JSON export
  const handleExportJson = () => {
    if (!id) return;
    const exportUrl = getExportPackageUrl(id);
    window.open(exportUrl, '_blank');
  };

  // Handle confirm holiday
  const handleConfirm = async () => {
    if (!id) return;
    try {
      setConfirming(true);
      setActionError(null);
      const res = await confirmPackage(id, {
        base_version: packageRes?.version_no ?? packageRes?.version,
        customer_name: 'Rajesh Sharma',
        customer_email: 'rajesh.sharma@example.com',
      });
      const ref = res.reference || res.reservation_reference;
      if (ref) {
        navigate(`/reservation/${ref}`);
      }
    } catch (err: any) {
      setActionError(err.message || 'Failed to confirm reservation');
    } finally {
      setConfirming(false);
    }
  };

  if (loading) {
    return (
      <div className="w-full min-h-[60vh] flex flex-col items-center justify-center gap-space-md">
        <Spinner size="lg" label="Loading Active Package Dossier..." />
        <span className="font-body-sm text-body-sm text-on-surface-variant">
          Retrieving live quotes, hotel room allocations &amp; timeline
        </span>
      </div>
    );
  }

  if (error || !packageRes) {
    return (
      <div className="max-w-4xl mx-auto px-margin py-space-xl flex flex-col gap-space-lg">
        <ErrorBanner
          title="Unable to Load Package"
          message={error || `Package ${id} could not be found or has expired.`}
        />
        <button
          onClick={() => navigate('/')}
          className="self-start px-space-md py-2 bg-primary text-on-primary rounded-lg font-headline-sm text-headline-sm"
        >
          Return to Trip Planner
        </button>
      </div>
    );
  }

  const pkgData = packageRes.package_data || packageRes.package || {};
  const items = packageRes.items || pkgData.items || [];
  const timeline = packageRes.timeline || [];
  const cities = pkgData.cities || ['Tokyo', 'Kyoto'];
  const travelerCount =
    (pkgData.travelers?.adults || 2) + (pkgData.travelers?.children || 1);

  return (
    <div className="w-full flex flex-col">
      {/* Top Command & Executive Summary Strip */}
      <CityPlanHeader
        packageRes={packageRes}
        onExportJson={handleExportJson}
        onConfirm={handleConfirm}
        confirming={confirming}
      />

      {/* Main Content Workspace (Split Layout 70% / 30%) */}
      <div className="max-w-7xl mx-auto px-margin w-full pb-space-xl">
        {actionError && (
          <div className="mb-space-md">
            <ErrorBanner
              title="Action Notice"
              message={actionError}
              onDismiss={() => setActionError(null)}
            />
          </div>
        )}

        {(sideEffects.length > 0 || warnings.length > 0) && (
          <div className="mb-space-md">
            <SideEffectsAlert sideEffects={sideEffects} warnings={warnings} />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-xl">
          {/* LEFT STREAM: Chronological Itinerary Builder (70% - lg:col-span-8) */}
          <div className="lg:col-span-8 flex flex-col gap-space-lg">
            {/* Alternative City Plans (G3) */}
            {packageRes.city_plans && packageRes.city_plans.length > 1 && (
              <CityPlanPicker
                cityPlans={packageRes.city_plans}
                onSelectPlan={(plan) => rebuild(plan)}
                loading={actionLoading}
              />
            )}

            {/* Timeline Days */}
            <DayTimeline
              timeline={timeline}
              items={items}
              cities={cities}
              onChangeClick={handleChangeClick}
              onRemoveClick={handleRemoveAttraction}
              onAddAttractionClick={handleAddAttraction}
            />
          </div>

          {/* RIGHT SIDEBAR: Sticky Pricing Manifest & Financial Matrix (30% - lg:col-span-4) */}
          <PriceBreakdown
            totals={pkgData.totals}
            items={items}
            totalPrice={packageRes.total_inr || packageRes.total_price}
            travelerCount={travelerCount}
            onConfirm={handleConfirm}
            confirming={confirming}
          />
        </div>
      </div>

      {/* Change Drawer / Modal */}
      <ChangeDrawer
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={modalTitle}
        subtitle={modalSubtitle}
        kind={modalKind}
        currentItem={modalItem}
        options={modalOptions}
        onSelectOption={handleSelectOption}
        loading={modalLoading}
      />
    </div>
  );
};
