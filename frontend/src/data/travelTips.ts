/**
 * Fixed, hand-written travel tips (no AI). Used by utils/travelTips.ts to pick the tips that fit a trip.
 */

export interface Climate {
  low: number;
  high: number;
  rainyDays: number;
  note: string;
}

/** Typical April averages in °C (the catalog only covers April 2027). Not a live forecast. */
export const CLIMATE_APRIL: Record<string, Climate> = {
  Tokyo: { low: 10, high: 19, rainyDays: 10, note: 'Cherry blossom season in early April' },
  Kyoto: { low: 8, high: 20, rainyDays: 9, note: 'Cool mornings, warm afternoons' },
  Osaka: { low: 10, high: 20, rainyDays: 9, note: 'Mild, with some rainy days' },
  Nara: { low: 7, high: 20, rainyDays: 9, note: 'Cool mornings, warm afternoons' },
  Dubai: { low: 21, high: 33, rainyDays: 0, note: 'Hot and sunny, with very strong sun' },
  'Abu Dhabi': { low: 21, high: 33, rainyDays: 0, note: 'Hot and sunny, with very strong sun' },
};

export const COUNTRY_TIPS: Record<string, string[]> = {
  Japan: [
    'Plugs are type A (100 V) — bring an adapter for Indian plugs.',
    'Carry some cash in yen; smaller shops and stalls may not take cards.',
    'Get an IC card (Suica or ICOCA) for city trains, buses and convenience stores.',
    'Tipping is not expected in Japan.',
  ],
  'United Arab Emirates': [
    'Plugs are type G (UK style) — bring an adapter.',
    'The currency is the UAE dirham (AED); cards work almost everywhere.',
    'Dress modestly in malls and public places — cover shoulders and knees.',
    'Carry a refillable water bottle; it gets hot outdoors.',
  ],
};

/** Keys are the catalog's attraction categories. */
export const ACTIVITY_TIPS: Record<string, string> = {
  TEMPLE: 'Temples: wear shoes that slip off easily — you often take them off inside. Clean socks help.',
  SHRINE: 'Shrines: bow at the gate, keep voices low, and wash hands at the water basin.',
  MOSQUE: 'Mosque visit: long sleeves and long trousers or skirt; women cover their hair (scarves are often lent at the entrance).',
  PALACE: 'Palaces: some rooms ask for covered shoulders; a light scarf or shirt is handy.',
  BEACH: 'Beach day: swimwear, high-SPF sunscreen, a hat and sandals.',
  THEME_PARK: 'Theme park: comfortable shoes, a refillable water bottle and a power bank for your phone.',
  NATURE: 'Nature spots: good walking shoes and a small backpack.',
  PARK: 'Parks: good walking shoes; a light picnic mat is handy in blossom season.',
  MARKET: 'Markets: carry small cash for food stalls.',
  VIEWPOINT: 'Viewpoints: go early or near sunset for clearer views and fewer people.',
  MUSEUM: 'Museums: big bags may need a locker; carry a small day bag instead.',
  CASTLE: 'Castles: expect steep stairs inside — comfortable shoes help.',
  DISTRICT: 'Old districts and lanes: comfortable walking shoes; go early or late in the day for cooler air and fewer crowds.',
  MONUMENT: 'Monuments: photos are usually fine outside; check signs before taking pictures indoors.',
  AQUARIUM: 'Aquariums: flash photography is usually not allowed.',
};