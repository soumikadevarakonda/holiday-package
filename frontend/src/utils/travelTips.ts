/**
 * Packing and weather hints, chosen by simple rules from the trip (no AI):
 * cities + month -> weather, country -> basics, attraction categories -> what to bring, travelers -> group tips.
 */
import { ACTIVITY_TIPS, CLIMATE_APRIL, COUNTRY_TIPS } from '../data/travelTips';
import type { PackageData, PackageItem } from '../api/types';

export interface TipGroup {
  title: string;
  icon: string;
  tips: string[];
}

function weatherTip(city: string): string | null {
  const w = CLIMATE_APRIL[city];
  if (!w) return null;
  const wear =
    w.high >= 30
      ? 'light cotton clothes, sunglasses and sunscreen'
      : w.low <= 10
      ? 'layers and a light jacket for the mornings'
      : 'light layers';
  const rain = w.rainyDays >= 8 ? ' Pack a small umbrella.' : '';
  return `${city}: about ${w.low}–${w.high}°C. ${w.note}. Bring ${wear}.${rain}`;
}

export function buildTravelTips(pkg: Partial<PackageData>, items: PackageItem[]): TipGroup[] {
  const groups: TipGroup[] = [];

  // 1. Weather for each city on the trip (the catalog window is always April)
  const cities: string[] = pkg.cities?.length
    ? pkg.cities
    : [...new Set(items.filter((i) => i.type === 'hotel').map((i) => i.city || ''))].filter(Boolean);
  const weather = cities.map(weatherTip).filter((t): t is string => Boolean(t));
  if (weather.length) groups.push({ title: 'Weather in April', icon: 'partly_cloudy_day', tips: weather });

  // 2. Country basics
  const basics = COUNTRY_TIPS[pkg.country || ''];
  if (basics) groups.push({ title: `Good to know in ${pkg.country}`, icon: 'info', tips: basics });

  // 3. What the planned activities need — one tip per category in the trip
  const categories = new Set(
    items.filter((i) => i.type === 'attraction' && i.category).map((i) => String(i.category).toUpperCase())
  );
  const plans = [...categories].map((c) => ACTIVITY_TIPS[c]).filter(Boolean);
  if (items.some((i) => i.type === 'transfer' && i.intercity)) {
    plans.push(
      pkg.country === 'Japan'
        ? 'Bullet train between cities: travel light; very large suitcases need a reserved luggage space.'
        : 'Coach between cities: keep water, snacks and anything valuable in a small bag with you.'
    );
  }
  if (plans.length) groups.push({ title: 'For your plans', icon: 'backpack', tips: plans });

  // 4. The group and the journey
  const group: string[] = [];
  const ages = pkg.travelers?.child_ages || [];
  if (ages.some((a) => a < 5)) group.push('Little ones: a light foldable stroller helps on long walking days.');
  if (ages.length) group.push('Kids: pack snacks, a water bottle and a change of clothes for travel days.');
  const out = items.find((i) => i.type === 'flight' && i.leg === 'arrival');
  if (out?.start && pkg.start_date && out.start.slice(0, 10) < pkg.start_date) {
    group.push('Your flight out is overnight — a neck pillow and eye mask will help you arrive rested.');
  }
  group.push('Keep passports, your booking number and a printed copy of this plan in your hand luggage.');
  groups.push({ title: 'For your group', icon: 'family_restroom', tips: group });

  return groups;
}

/** Plain-text version for "Copy list". */
export function tipsAsText(groups: TipGroup[]): string {
  return groups.map((g) => `${g.title}\n${g.tips.map((t) => `- ${t}`).join('\n')}`).join('\n\n');
}