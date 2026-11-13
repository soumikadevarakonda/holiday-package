/**
 * The single place where backend response shapes are turned into the shapes the components use.
 * Every function in api/*.ts runs its response through one of these.
 */
import type {
  ApiTotals,
  ChangeOption,
  CityPlan,
  MetaResponse,
  PackageData,
  PackageItem,
  PackageResponse,
  QuickRequestResponse,
  ReservationResponse,
  Totals,
  TripRequest,
} from './types';

const hhmm = (s?: string | null) => (s && s.includes('T') ? s.slice(11, 16) : undefined);

export function normalizeItem(raw: any): PackageItem {
  const d = raw?.details || {};
  const item: PackageItem = { ...raw, details: d };
  switch (raw?.type) {
    case 'flight':
      Object.assign(item, {
        leg: d.leg,
        airline: d.airline,
        flight_number: d.flight_number,
        from_airport: d.from_airport ? `${d.from_airport}${d.from_city ? ` (${d.from_city})` : ''}` : undefined,
        to_airport: d.to_airport ? `${d.to_airport}${d.to_city ? ` (${d.to_city})` : ''}` : undefined,
        stops: d.stops,
        duration_minutes: d.duration_minutes,
      });
      break;
    case 'hotel':
      Object.assign(item, {
        hotel_name: d.hotel_name || raw.name,
        room_name: d.room_name,
        nights: d.nights,
        image: d.image,
        rating: d.rating,
        stars: d.stars,
        area: d.area,
      });
      break;
    case 'transfer':
      Object.assign(item, {
        transfer_type: d.transfer_type,
        from_location: d.from_point,
        to_location: d.to_point,
        intercity: d.intercity,
        duration_minutes: d.duration_minutes,
      });
      break;
    case 'attraction':
      Object.assign(item, {
        attraction_name: raw.name,
        image: d.image,
        category: d.category,
        time_slot: hhmm(raw.start) ? `${hhmm(raw.start)}–${hhmm(raw.end) ?? ''}` : undefined,
      });
      break;
  }
  return item;
}

function toTotals(t: ApiTotals | undefined, items: PackageItem[], budget?: number): Totals {
  const sum = (type: string) =>
    items.filter((i) => i.type === type).reduce((s, i) => s + (i.price_inr ?? 0), 0);
  const by = t?.by_type;
  const total = t?.total_inr ?? items.reduce((s, i) => s + (i.price_inr ?? 0), 0);
  const b = t?.budget_inr ?? budget ?? 0;
  return {
    flights: by?.flight ?? sum('flight'),
    hotels: by?.hotel ?? sum('hotel'),
    transfers: by?.transfer ?? sum('transfer'),
    attractions: by?.attraction ?? sum('attraction'),
    total,
    budget: b,
    budget_left: Math.max(0, b - total),
    budget_over: Math.max(0, total - b),
  };
}

export function normalizePackageData(raw: any, totals?: ApiTotals): PackageData {
  if (!raw) return { trip_id: '', items: [] };
  const items: PackageItem[] = (raw.items || []).map(normalizeItem);
  const plan: { city: string; nights: number }[] = raw.city_plan || [];
  const t = raw.traveler || {};
  return {
    ...raw,
    items,
    cities: plan.map((c) => c.city),
    nights_per_city: Object.fromEntries(plan.map((c) => [c.city, c.nights])),
    destination_country: raw.country,
    departure_city: t.home_airport,
    traveler_name: t.name,
    travelers: { adults: t.adults ?? 0, children: t.children ?? 0, child_ages: t.child_ages ?? [] },
    totals: toTotals(totals, items, raw.budget_inr),
  };
}

export function normalizeCityPlan(raw: any): CityPlan {
  const plan: { city: string; nights: number }[] =
    raw.plan ||
    (Array.isArray(raw.cities) && Array.isArray(raw.nights)
      ? raw.cities.map((c: string, i: number) => ({ city: c, nights: raw.nights[i] }))
      : []);
  return {
    ...raw,
    plan,
    cities: plan.map((c) => c.city),
    nights: Object.fromEntries(plan.map((c) => [c.city, c.nights])),
    total_nights: plan.reduce((s, c) => s + c.nights, 0),
  };
}

export function normalizePackageResponse(raw: any): PackageResponse {
  const items: PackageItem[] = (raw.items || raw.package?.items || []).map(normalizeItem);
  const pkg = raw.package ? normalizePackageData({ ...raw.package, items: raw.items || raw.package.items }, raw.totals) : undefined;
  return {
    ...raw,
    items,
    package: pkg,
    package_data: pkg,
    version_no: raw.version_no ?? raw.version ?? 1,
    total_price: raw.total_inr ?? raw.total_price ?? 0,
    timeline: raw.timeline || [],
    city_plans: (raw.city_plans || []).map(normalizeCityPlan),
    cheapest_package: raw.cheapest_package ? normalizePackageData(raw.cheapest_package) : undefined,
  };
}

export function normalizeOption(raw: any): ChangeOption {
  const d = raw.details || {};
  return {
    ...raw,
    key: `${raw.catalog_id}|${raw.room_id ?? ''}|${raw.start ?? ''}`,
    name: raw.label || raw.name || raw.catalog_id,
    current: Boolean(d.current),
    rating: d.rating,
    room_type: d.room_type ? `${d.room_type.replace(/_/g, ' ')}${d.rooms > 1 ? ` × ${d.rooms}` : ''}${d.area ? ` • ${d.area}` : ''}` : undefined,
    airline: d.airline,
    departure_time: hhmm(d.departure_local),
    arrival_time: hhmm(d.arrival_local),
    duration: d.duration_minutes ? `${Math.floor(d.duration_minutes / 60)}h ${d.duration_minutes % 60}m` : undefined,
    category: d.category,
    time_slot: hhmm(raw.start),
    image: d.image,
  };
}

export function normalizeReservation(raw: any): ReservationResponse {
  const r = raw.reservation || {};
  const snapshot = normalizePackageData(raw.snapshot || r.package_snapshot);
  return {
    ...raw,
    reservation_id: raw.reservation_id || r.reservation_id,
    created_at: raw.created_at || r.created_at,
    total_price: raw.total_inr ?? raw.total_price ?? r.total_price ?? 0,
    items: (raw.items || snapshot.items || []).map(normalizeItem),
    snapshot,
  };
}

export function normalizeMeta(raw: any): MetaResponse {
  return {
    ...raw,
    destination_countries: raw.destination_countries || raw.countries || [],
    departure_cities: raw.departure_cities || [],
    rules: raw.rules || {},
    summary: raw.summary || {},
  };
}

const REQUIRED: (keyof TripRequest)[] = ['departure_city', 'destination_country', 'start_date', 'nights', 'adults', 'budget'];

export function normalizeParse(raw: any): QuickRequestResponse {
  const r = raw.request || raw.parsed || {};
  const parsed: Partial<TripRequest> = {};
  if (r.departure_city) parsed.departure_city = r.departure_city;
  if (r.country || r.destination_country) parsed.destination_country = r.country || r.destination_country;
  if (r.start_date) parsed.start_date = r.start_date;
  if (r.nights !== undefined) parsed.nights = r.nights;
  if (r.adults !== undefined) parsed.adults = r.adults;
  const ages = r.children_ages || r.child_ages;
  if (Array.isArray(ages)) {
    parsed.child_ages = ages;
    parsed.children = ages.length;
  }
  if (r.budget_inr !== undefined || r.budget !== undefined) parsed.budget = r.budget_inr ?? r.budget;
  const missing = REQUIRED.filter((k) => parsed[k] === undefined);
  return {
    parsed,
    missing_fields: missing,
    ambiguous_fields: raw.warnings || [],
    ready_to_build: missing.length === 0,
    unparsed: raw.unparsed || [],
    warnings: raw.warnings || [],
  };
}
