# Context — Build My Holiday

Working context for anyone (or any AI assistant) writing code in this repo. Read this before changing the engine, the API or the UI.

| Document | What it is |
|---|---|
| [data/problem-1-holiday-package.md](data/problem-1-holiday-package.md) | **Official brief** (source of truth for rules, features, judging) |
| [data/DATA_DICTIONARY.md](data/DATA_DICTIONARY.md) | Every catalog field, the shared trip format, data FAQ |
| [PRD-Build-My-Holiday.md](PRD-Build-My-Holiday.md) | Our spec: design, API, edge cases, trade-offs |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Folder and file layout |
| [Project.md](Project.md) | Backend work split between the two developers |

If our docs and the brief disagree, the brief wins.

---

## 1. What we are building

A hackathon web app (Problem 1) that turns 7 inputs into **one complete, rule-valid holiday package** and books it.

- **Inputs:** departure city, destination country, start date, nights, adults, children's ages, budget (INR).
- **Package parts:** arrival + return flight, a hotel per city, airport transfers, inter-city transfers, attractions.
- **Four possible outcomes** for every request:
  1. a package,
  2. **over budget** (M8): the cheapest total and the gap,
  3. **no package** (M2): a specific reason,
  4. **invalid input** (M1): field-level errors (`422`).
- After confirm: a unique **10-digit reservation number** that survives a backend restart.

**Primary persona (the demo request):** Menon family. BLR → Japan, 10 Apr 2027, 6 nights, 2 adults + 1 child (age 6), budget ₹3,50,000. It must build in under 3 seconds and fit the budget.

**Judging:** end-to-end features 25% · correctness on unseen requests 25% · individual understanding 20% · product and UX 15% · engineering quality 15%. **A package that breaks one rule counts as wrong.**

---

## 2. Stack and principles

| Layer | Tech | Role |
|---|---|---|
| Frontend | React + Vite + TypeScript + Tailwind | Displays only. Computes nothing. |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy Core | All logic: builder, validator, pricing, changes |
| Database | MySQL 8 | App state only (requests, packages, versions, reservations, inventory) |
| Catalog | JSON files in `data/catalog/` | Read-only, loaded into memory once at startup |
| Photos | JPGs in `data/images/` | Static files at `/images`; optional in the UI, but credits must be shown if used |

**Non-negotiables**

1. **One validator** (`backend/app/rules/validator.py`) is used by build, every change, confirm and export. A package is valid only if `validate(package) == []`.
2. **The frontend computes no prices, rules or city choices.** It renders what the API returns.
3. **The catalog is never edited.** S2 inventory use is stored in MySQL (`inventory_usage`) and subtracted.
4. **No AI or LLM call anywhere in the app.** The S1 parser uses regex and keywords only.
5. **Deterministic:** the same request always gives the same package (stable sorting; the only randomness is the reservation number).
6. **Money is integer INR**, never floats.
7. **Limits come from the data** (`destinations.json.rules`, max seats computed at startup), never hard-coded.

---

## 3. Domain rules (the validator)

Notation: S = start date (arrival day), N = nights, L = S + N (return day). Hotel nights are S … L−1. T = adults + children (a child is 0–17).

| ID | Rule |
|---|---|
| D1 | 3 ≤ N ≤ 10; S ≥ 1 Apr 2027; return flight date ≤ 20 Apr 2027 |
| D2 | Every city belongs to the chosen country |
| D3 | Each city: ≥ 2 consecutive nights, appears once; nights sum to N |
| F1 | Exactly one arrival flight and one return flight |
| F2 | Arrival: date of `arrival_local` = S; arrival airport's `serves_cities` contains the first city |
| F3 | Return: date of `departure_local` = L; departure airport serves the last city; lands at the home airport |
| F4 | `seats_left` ≥ T on both flights |
| AT1 | One airport → first hotel transfer and one last hotel → airport transfer; area = hotel area or null |
| AT2 | Pickup ≥ landing + 60 min |
| AT3 | At the airport ≤ departure − 180 min |
| AT4 | Pickup / leave time inside service hours, ends included; windows can pass midnight; `24:00` = end of day |
| CT1 | On each city-change day, one link transfer, inside service hours, on the `frequency_minutes` grid |
| H1 | Exactly one hotel for every night S … L−1, none on L |
| H2 | Per city: one hotel and one room type for all nights; k rooms |
| H3 | adults ≤ k × max_adults; T ≤ k × (max_adults + max_children); adults ≥ k |
| H4 | `rooms_left` ≥ k on every night of the stay |
| A1 | Attraction in that night's city, open that weekday, not on a closed date, visit fits opening hours |
| A2 | No overlapping visits on a day; each attraction at most once |
| A3 | Initial package only: 1–2 attractions on every full day |
| A4 | Arrival day and city-change days: optional, after reaching the city. None on L |
| P1 | Every line price matches its formula; total = sum of parts (within 1%) |

**Price formulas (INR)**

- Flight = `price_per_seat × T`
- Hotel = `price_per_night × k × nights`
- Transfer PER_PERSON = `adults × price + children × (child_price if not None else price)`
- Transfer PER_VEHICLE = `price × ceil(T / max_passengers)`
- Attraction = `adults × price_per_person + children × (child_price if not None else price_per_person)`

**Full day** = a day in S+1 … L−1 that is not a city-change day.

---

## 4. Data traps (check these before writing code)

| Trap | What to do |
|---|---|
| Kyoto has no airport; KIX serves Osaka and Kyoto; DXB serves Dubai and Abu Dhabi; ITM has `serves_cities: []` | Take first/last city from `serves_cities`, never `airports.city`. A missing field = empty list |
| Overnight outbound flights leave on S−1 | Filter arrivals by the **date of `arrival_local`**, returns by the **date of `departure_local`** |
| Returns on 20 Apr can land on 21 Apr | Valid: only the departure date counts |
| Local times differ across zones (IST +5:30, JST +9:00, GST +4:00) | Never subtract local times across zones. Use `duration_minutes` |
| `seats_left` is 1–9; FL-403 BLR → HND on 10 Apr has 2 seats | 10+ travelers are rejected at input. Menon (3) cannot use FL-403 |
| Transfer windows use `24:00` and can wrap midnight (06:00–00:30) | Use the one shared helper in `core/timeutil.py` |
| Buses start ~06:30 and stop ~22:00; Japan taxis 06:00–23:00 | Early returns and late landings often need a taxi. Check timing per flight pair, not cheapest first |
| 22:50 KIX landing → pickup ≥ 23:50 | Only the KIX → Namba shuttle works, so the first hotel must be in Namba (Osaka) |
| 5+ travelers in a 4-seat taxi | 2 vehicles, price × 2 |
| `child_price` = 0 on 5 attractions; missing on taxis | **Check `is not None`.** Never `child_price or price` |
| 24 attractions are free (price 0) | Valid; keep them first for cheap packages |
| 61 room-nights are sold out (`rooms_left` 0) | One sold-out night rejects that room type for the whole city stay |
| ATT-TYO-006 closed 10–20 Apr; 11 attractions skip a weekday | Check `closed_dates` and the weekday (12 Apr 2027 is a Monday) |
| 2 attractions are in Nara, which has no hotels | Never offer them |
| 10 nights only in Osaka (9 attractions) or Abu Dhabi (7) | Can't fill every full day, so the plan fails A3; move to a multi-city plan |
| Catalog date-times have seconds (`2027-04-01T07:20:00`); the export uses `YYYY-MM-DDTHH:MM` | Parse with seconds in the loader; format without seconds in `export/trip_format.py` |
| Prices are objects: `{ "amount": 6440, "currency": "INR" }` | The loader unwraps `amount` to an int |
| Every seat costs `price_per_seat`; children get no flight discount | `child_price` applies only to transfers and attractions |
| Hotel `image` paths are shared by type (10 photos for 49 hotels); attraction `image` is `images/attractions/<id>.jpg` | Paths are relative to `data/`, so the URL is `/` + `image` |
| Only `catalog/loader.py` knows raw JSON field names | Everything else uses the dataclasses in `catalog/models.py` |

---

## 5. Builder and city rule

**Method: enumerate + greedy + validate.**

1. Validate the request.
2. Pre-filter flights (by local date, `seats_left ≥ T`).
3. Feasible first and last cities from the airports' `serves_cities`.
4. Enumerate city plans: ordered distinct cities × night splits (≥ 2 per city). At most 135 for Japan at 10 nights.
5. Hotels per city: the cheapest valid (hotel, room type, k). Memoized; greedy is optimal here.
6. Cheapest flight pair whose airport transfers fit the timing.
7. Inter-city transfer: first 30-minute grid slot at or after 10:00.
8. Attractions: free and child-friendly first, then price; 1–2 per full day, 30-minute gap, no overlap.
9. Price + full validation; drop failing plans.
10. Choose by the city rule.

**City rule:** `c* = max(1, floor(N / 3))`, capped by cities in the country (Japan 3, UAE 2). Pick the cheapest plan within budget with `c*` cities; else try `c*−1 … 1`, then `c*+1`; else return M8 with the globally cheapest package.

**G4 definitions (from the data FAQ):**
- **Cheapest** = lowest total.
- **Fastest** = `duration_minutes` of the 2 flights + each inter-city transfer (`from_city` / `to_city` records). Airport transfers and city taxis don't count.
- **Best rated** = highest average hotel `stars` per night, within budget (e.g. 2 nights × 5★ + 4 nights × 3★ = 3.67). Guest `rating` doesn't count.

**Safety net:** `builder.search(req, strategy="fast" | "brute")`. A pytest checks that both give the same totals on every fixture.

**Failure reasons** are counted per stage (e.g. "0 of 14 arrival flights land on 10 Apr with 5 seats") and the most specific one is returned for M2.

---

## 6. API contract (frozen)

All routes are under `/api`. Errors use one shape: `{code, message, details}`. Over budget and no package return `200` with an `outcome` field; invalid input returns `422`. Every write to a package sends `base_version`; a stale one gets `409 VERSION_CONFLICT`.

| Method + path | Purpose |
|---|---|
| `GET /api/meta` | Departure cities, countries, date window, night limits |
| `POST /api/packages` | Build (`mode: "default" \| "three"` for G4) |
| `GET /api/packages/{id}` | Current version, day plan, totals, warnings |
| `GET /api/packages/{id}/options/{hotel\|flight\|attraction}` | Valid alternatives with `price_diff` |
| `PATCH /api/packages/{id}` | Apply a change → new version, or `409 RULE_VIOLATION` (package unchanged) |
| `GET /api/packages/{id}/city-plans` | Ranked city plans (G3) |
| `POST /api/packages/{id}/rebuild` | Rebuild on another city plan |
| `POST /api/packages/{id}/undo` | Restore the previous version as a new version |
| `GET /api/packages/{id}/export` | Shared trip format JSON (attachment) |
| `POST /api/packages/{id}/confirm` | Book → `{reference}`; idempotent |
| `GET /api/reservations/{ref}` | `400` if not 10 digits, `404 "Reservation not found"` |
| `POST /api/parse` | S1 quick request |
| `GET /api/health` | Catalog and DB status |

**Export format** (DATA_DICTIONARY section 4): `trip_id`, `traveler{…}`, `start_date`, `end_date` (= return day), `country`, `budget_inr`, `total_inr`, `items[]`. Times are `YYYY-MM-DDTHH:MM` (no seconds). Flight `city` = arrival city. Hotel items carry `room_id`. `sources` is always `[]`. Booked packages have status `BOOKED` and `booking.reference`.

---

## 7. Database

| Table | Purpose |
|---|---|
| `trip_requests` | Validated request as entered |
| `packages` | One row per package: status (`DRAFT`/`BOOKED`), current version, total |
| `package_versions` | Every accepted change is a new version (JSON body); `UNIQUE(package_id, version_no)` |
| `reservations` | Frozen snapshot at confirm; `reference CHAR(10)` primary key |
| `inventory_usage` | S2: seats and rooms consumed by bookings |

**Reservation number:** `secrets.randbelow(9 * 10**9) + 10**9` (10 digits, no leading zero), stored as a string, retry up to 5 times on a duplicate key.

**Confirm transaction:** BEGIN → lock `inventory_usage` rows → recompute effective seats/rooms → re-validate → insert reservation + usage → set BOOKED → COMMIT. Any failure rolls back with a reason.

---

## 8. Conventions

- **Backend layering:** routers → services → domain (`builder → rules → pricing → catalog → core`) → repositories → MySQL. `catalog`, `pricing`, `rules` and `builder` never import a router, a repository or SQLAlchemy.
- **Frontend:** only `src/api/` calls the backend. `src/api/types.ts` mirrors the Pydantic schemas.
- **Money display:** ₹ with Indian grouping (₹3,50,000). **Times:** local time with a zone label (JST / GST / IST).
- **Violations** carry `rule_id`, `item_ref` and a plain-English message; the UI shows the message as the refusal reason.
- **Commits:** small, at least hourly, tagged by feature, e.g. `M6: hotel change endpoint`.
- **Performance targets:** build ≤ 3 s, change ≤ 500 ms.

---

## 9. Team and priorities

| Person | Owns |
|---|---|
| A (engine) | `core/timeutil.py`, `catalog/`, `pricing/`, `rules/`, `builder/`, `changes/options.py` + `side_effects.py`, `tests/unit`, `tests/oracle` |
| B (API + UI + DB) | `database/`, `core/database.py`, `packages/`, `changes/router.py` + `apply.py`, `export/`, `reservations/`, `inventory/`, `parser/`, `frontend/`, `tests/api` |

**Build order:** all Must features (M1–M8) first and passing on 5+ test requests → G2, G1, G4, G3 → S2, S1, S3 if time remains.

**Out of scope:** login, payments, real supplier booking, online deployment, editing catalog files, AI calls, mobile apps, multi-currency.

---

## 10. Current status

- PRD, project structure, README and backend work split (`Project.md`) written.
- Empty file and folder skeleton created.
- **Data pack in place** (`data/`): brief, data dictionary, 8 catalog files, trip format example, 66 photos + credits. Record counts match the PRD.
- No feature implemented yet.
