export interface TripRequest {
  departure_city: string;
  destination_country: string;
  start_date: string;
  nights: number;
  adults: number;
  children: number;
  child_ages: number[];
  budget: number;
  mode?: string;
}

export interface Totals {
  flights: number;
  hotels: number;
  transfers: number;
  attractions: number;
  total: number;
  budget?: number;
  budget_left?: number;
  budget_over?: number;
}

export interface PackageItem {
  item_id: string;
  type: 'flight' | 'hotel' | 'transfer' | 'attraction' | string;
  catalog_id?: string;
  name?: string;
  city?: string;
  start?: string;
  end?: string;
  start_datetime?: string;
  end_datetime?: string;
  price_inr?: number;
  price?: number;
  quantity?: number;
  details?: Record<string, any>;
  image?: string;
  warnings?: string[];
  // Additional item fields
  flight_number?: string;
  airline?: string;
  from_airport?: string;
  to_airport?: string;
  seats?: number;
  hotel_id?: string;
  hotel_name?: string;
  room_id?: string;
  room_name?: string;
  nights?: number;
  transfer_type?: string;
  vehicle_type?: string;
  from_location?: string;
  to_location?: string;
  attraction_id?: string;
  attraction_name?: string;
  time_slot?: string;
}

export interface TimelineEvent {
  item_id?: string;
  type: string;
  time: string;
  title: string;
  city: string;
  end_time?: string | null;
  price_inr: number;
  quantity: number;
  warnings?: string[];
}

export interface TimelineDay {
  day_number: number;
  date: string;
  weekday: string;
  events: TimelineEvent[];
}

export interface CityPlan {
  cities: string[];
  nights: Record<string, number>;
  order?: string[];
  total_nights?: number;
}

export interface PackageData {
  trip_id: string;
  country?: string;
  start_date?: string;
  end_date?: string;
  departure_city?: string;
  destination_country?: string;
  cities?: string[];
  nights_per_city?: Record<string, number>;
  travelers?: {
    adults: number;
    children: number;
    child_ages?: number[];
  };
  items: PackageItem[];
  totals?: Totals;
  status?: string;
  total_inr?: number;
  total_price?: number;
  currency?: string;
  customer?: {
    name?: string;
    email?: string;
    phone?: string;
  };
}

export interface PackageResponse {
  outcome?: 'PACKAGE' | 'OVER_BUDGET' | 'NO_PACKAGE';
  package_id: string;
  trip_id?: string;
  status: string;
  version?: number;
  version_no: number;
  total_price: number;
  total_inr?: number;
  created_at?: string;
  updated_at?: string;
  package_data?: PackageData;
  package?: PackageData;
  items?: PackageItem[];
  timeline: TimelineDay[];
  city_plans: CityPlan[];
  cheapest_total?: number;
  over_by?: number;
  suggestion?: string;
  cheapest_package?: PackageData;
  reason?: string;
}

export interface ComponentChangeRequest {
  base_version?: number;
  kind: 'hotel' | 'flight' | 'attraction' | string;
  current_item_id?: string;
  new_catalog_id: string;
  params?: Record<string, any>;
}

export interface ChangeOption {
  catalog_id: string;
  name: string;
  price_inr: number;
  price_diff: number;
  details?: Record<string, any>;
  image?: string;
  rating?: number;
  room_type?: string;
  room_id?: string;
  airline?: string;
  flight_number?: string;
  departure_time?: string;
  arrival_time?: string;
  duration?: string;
  category?: string;
  time_slot?: string;
}

export interface ChangeResponse {
  message: string;
  package_id: string;
  version: number;
  version_no: number;
  total_price: number;
  items: PackageItem[];
  package: PackageData;
  side_effects?: string[];
  warnings?: string[];
}

export interface ConfirmPackageRequest {
  base_version?: number;
  customer_name?: string;
  customer_email?: string;
  customer_phone?: string;
}

export interface ReservationResponse {
  reservation_id: string;
  reference: string;
  reservation_reference?: string;
  package_id: string;
  status: string;
  customer_name: string;
  customer_email: string;
  total_price: number;
  created_at?: string;
  items: PackageItem[];
  snapshot: PackageData;
}

export interface CountryMeta {
  code?: string;
  name?: string;
  country?: string;
  timezone?: string;
  cities?: any[];
  links?: any[];
}

export interface DepartureCityMeta {
  airport?: string;
  city?: string;
  code?: string;
  name?: string;
}

export interface MetaResponse {
  departure_cities: (string | DepartureCityMeta)[];
  destination_countries: (CountryMeta | string)[];
  rules: Record<string, any>;
  summary: Record<string, any>;
}

export interface QuickRequestResponse {
  parsed: Partial<TripRequest>;
  missing_fields: string[];
  ambiguous_fields: string[];
  ready_to_build: boolean;
}
