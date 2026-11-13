# Project Structure — Build My Holiday

Stack: **React (Vite + TypeScript)** frontend · **Python (FastAPI)** backend · **MySQL 8** database.
Build method: **enumerate + greedy + validate** (see `docs/PRD.md`, section 7).
Official brief: `data/problem-1-holiday-package.md` · field reference: `data/DATA_DICTIONARY.md`.

The repo has three top-level parts (`frontend/`, `backend/`, `database/`), plus the read-only data pack in `data/` and the docs in `docs/`. The backend is split **by module**: each folder owns one part of the product and maps to one or more features (M1–M8, G1–G4, S1–S3).

---

## 1. Top level

```
build-my-holiday/
├── README.md                  # start commands, architecture, city rule, features done, limitations
├── docker-compose.yml         # command 1: mysql + backend + frontend
├── start.sh                   # command 2 (fallback, no Docker): install + run both apps
├── .env.example               # DB_URL, DATA_DIR, API_PORT, WEB_PORT (no secrets committed)
├── .gitignore                 # node_modules/, .venv/, dist/, __pycache__/, .env
│
├── data/                      # PROVIDED DATA PACK — copied as is, never edited
│   ├── README.md              # data pack overview + event rules (short version)
│   ├── problem-1-holiday-package.md   # official problem statement: rules, features, judging
│   ├── DATA_DICTIONARY.md     # every field, file links, trip format (section 4), data FAQ
│   ├── trip_format_example.json       # 2-item example of the export shape
│   ├── assets/
│   │   └── problem-1-flow.png # user flow diagram from the brief
│   ├── catalog/               # 469 flights · 49 hotels · 125 rooms · 2,500 room-nights
│   │   ├── destinations.json  #   · 66 transfers · 56 attractions · 10 airports
│   │   ├── airports.json
│   │   ├── flights.json
│   │   ├── hotels.json        # `image`: "images/hotels/HOTEL-<TYPE>-<n>.jpg"
│   │   ├── rooms.json
│   │   ├── availability.json
│   │   ├── transfers.json
│   │   └── attractions.json   # `image`: "images/attractions/<attraction_id>.jpg"
│   └── images/                # served by the backend at /images (optional in the UI)
│       ├── ATTRIBUTIONS.md    # photo credits: must be shown if photos are shown
│       ├── attractions/       # 56 photos, one per attraction (real places)
│       └── hotels/            # 10 generic photos shared by hotel type (hotels are fictional)
│
├── docs/
│   ├── PRD.md
│   └── PROJECT_STRUCTURE.md   # this file
│
├── database/                  # MySQL schema and DB scripts
├── backend/                   # FastAPI app: all logic lives here
└── frontend/                  # React app: display only, talks to /api
```

---

## 2. `database/`

MySQL stores **app state only** (requests, packages, versions, reservations, inventory use). The catalog stays in `data/` and is loaded into memory by the backend.

```
database/
├── README.md                          # how the schema is applied, how to reset
├── init/
│   └── 000_create_database.sql        # CREATE DATABASE holiday; user + grants (run by docker on first start)
├── schema/                            # applied in order, idempotent (CREATE TABLE IF NOT EXISTS)
│   ├── 001_trip_requests.sql
│   ├── 002_packages.sql
│   ├── 003_package_versions.sql       # UNIQUE(package_id, version_no)
│   ├── 004_reservations.sql           # reference CHAR(10) PRIMARY KEY, package_id UNIQUE
│   └── 005_inventory_usage.sql        # S2: seats/rooms consumed by confirmed bookings
├── seeds/
│   └── demo_reset.sql                 # dev only: TRUNCATE all app tables before the demo
└── scripts/
    ├── apply_schema.sh                # runs init/ + schema/ against DB_URL (non-Docker setup)
    └── reset_db.sh                    # drop + recreate app tables (dev only)
```

| Table | Purpose | Written by module |
|---|---|---|
| `trip_requests` | Validated request as entered | `packages` |
| `packages` | One row per built package (status, current version, total) | `packages` |
| `package_versions` | Every accepted change = new version (JSON body in trip format) | `packages`, `changes` |
| `reservations` | Frozen snapshot at confirm, 10-digit reference | `reservations` |
| `inventory_usage` | S2: seats and rooms used per flight / room-night | `inventory` |

In Docker, `docker-compose.yml` mounts `database/init` and `database/schema` into `/docker-entrypoint-initdb.d/`, so the schema is created automatically on the first `docker compose up`.

---

## 3. `backend/`

```
backend/
├── requirements.txt           # fastapi, uvicorn, pydantic, sqlalchemy, pymysql, pytest, httpx
├── Dockerfile
├── pytest.ini
├── app/
│   ├── main.py                # create FastAPI app, CORS, mount routers, load catalog on startup,
│   │                          # serve data/images at /images (StaticFiles; also serves
│   │                          # /images/ATTRIBUTIONS.md for the photo credits page)
│   │
│   ├── core/                  # shared plumbing, no business rules
│   │   ├── config.py          # settings from env: DATA_DIR, DB_URL, ports
│   │   ├── database.py        # SQLAlchemy engine + session dependency
│   │   ├── errors.py          # AppError(code, message, details) + exception handlers → {code, message, details}
│   │   ├── package_model.py   # shared dataclasses: TripRequest, Package, Item, CityStay, Totals
│   │   │                      # (the contract between engine and API, see Project.md)
│   │   ├── timeutil.py        # parse "HH:MM" and "24:00", windows past midnight, inclusive ends,
│   │   │                      # weekday of a date, minutes math (single tested helper)
│   │   └── money.py           # integer INR helpers, formatting
│   │
│   ├── catalog/               # READ-ONLY catalog: load JSON once, build indexes       (M1, all)
│   │   ├── models.py          # dataclasses: Airport, Flight, Hotel, RoomType, Availability,
│   │   │                      # Transfer, Attraction, Country, CityLink (hotel/attraction keep `image`)
│   │   ├── loader.py          # read data/catalog/*.json → models (only file that knows raw field names);
│   │   │                      # parses "YYYY-MM-DDTHH:MM:SS" catalog times, {amount, currency} prices
│   │   ├── indexes.py         # dicts: flights by (airport, local date), rooms by hotel,
│   │   │                      # availability by (room_id, date), transfers by (airport, city, area)
│   │   │                      # and (from_city, to_city), attractions by city, airports by served city
│   │   ├── store.py           # singleton CatalogStore: holds models + indexes, query functions
│   │   └── router.py          # GET /api/meta (departure cities, countries, date window, limits)
│   │
│   ├── pricing/               # price formulas from the brief                              (M5, P1)
│   │   ├── calculator.py      # flight, hotel, transfer PER_PERSON / PER_VEHICLE, attraction;
│   │   │                      # child_price checked with "is not None" (0 is a valid price)
│   │   └── totals.py          # line items → total, budget left / over
│   │
│   ├── rules/                 # THE VALIDATOR: every section-4 rule as a check with an ID   (M3)
│   │   ├── violations.py      # Violation(rule_id, item_ref, message)
│   │   ├── validator.py       # validate(package) -> list[Violation]; runs all checks below
│   │   └── checks/
│   │       ├── dates.py       # D1–D3: nights, window, city plan
│   │       ├── flights.py     # F1–F4: dates, serves_cities, seats
│   │       ├── airport_transfers.py   # AT1–AT4: area match, +60 / −180 min, service hours
│   │       ├── intercity.py   # CT1: link transfer, service hours, frequency grid
│   │       ├── hotels.py      # H1–H4: every night, one room type per city, room fit, rooms_left
│   │       ├── attractions.py # A1–A4: city, open day, hours, closed dates, overlap, once only
│   │       └── prices.py      # P1: every line price and the total match the formulas
│   │
│   ├── builder/               # ENUMERATE + GREEDY + VALIDATE                            (M2, M8, G3, G4)
│   │   ├── city_plans.py      # enumerate: city orders × night splits (≥ 2 per city), link check
│   │   ├── hotels.py          # greedy: cheapest valid (hotel, room type, k) per city stay (memoized)
│   │   ├── flights.py         # arrival / return candidates by local date, seats ≥ travelers
│   │   ├── transfers.py       # airport transfer timing (+60 / −180), inter-city slot on 30-min grid
│   │   ├── attractions.py     # greedy day scheduler: free / child-friendly first, no overlap
│   │   ├── assemble.py        # one city plan → full package (items + day timeline)
│   │   ├── search.py          # build(req, strategy="fast" | "brute"); loops plans, validates each
│   │   ├── selector.py        # city rule (≈ N ÷ 3 cities), budget fit, G4 cheapest / fastest / best rated
│   │   └── failures.py        # reason counters per stage → "no package" message (M2) and M8 suggestion
│   │
│   ├── packages/              # API + persistence for packages                           (M2, M4, M5)
│   │   ├── router.py          # POST /api/packages, GET /api/packages/{id}, GET .../city-plans,
│   │   │                      # POST .../rebuild, POST .../undo
│   │   ├── schemas.py         # Pydantic: TripRequest (M1 field checks), PackageOut, Totals, Outcome
│   │   ├── service.py         # validate request → builder → save version → response
│   │   ├── repository.py      # trip_requests, packages, package_versions tables
│   │   └── timeline.py        # day-by-day plan in time order (M4)
│   │
│   ├── changes/               # change hotel / flight / attractions                       (M6, G1, G2)
│   │   ├── router.py          # GET .../options/{hotel|flight|attraction}, PATCH /api/packages/{id}
│   │   ├── options.py         # valid alternatives + price_diff against the current choice (G2)
│   │   ├── apply.py           # apply change on a copy → validate whole package → save or 409
│   │   └── side_effects.py    # re-time transfers, drop attractions that no longer fit, warnings (G1)
│   │
│   ├── export/                # shared trip format JSON                                   (M5, M7)
│   │   ├── trip_format.py     # package → DATA_DICTIONARY section 4 (country, room_id, booking)
│   │   └── router.py          # GET /api/packages/{id}/export (attachment)
│   │
│   ├── reservations/          # confirm + lookup                                          (M7)
│   │   ├── router.py          # POST /api/packages/{id}/confirm, GET /api/reservations/{ref}
│   │   ├── reference.py       # random 10-digit number, retry on duplicate key
│   │   ├── service.py         # confirm transaction: re-validate → (S2 inventory) → snapshot → BOOKED
│   │   └── repository.py      # reservations table
│   │
│   ├── inventory/             # booking uses up seats and rooms                           (S2)
│   │   ├── service.py         # effective seats_left / rooms_left = catalog − booked
│   │   └── repository.py      # inventory_usage table, locked inside the confirm transaction
│   │
│   └── parser/                # quick request in plain words, rules only, no AI           (S1)
│       ├── quick_request.py   # regex/keywords: cities, country, date, nights, adults, child ages, budget
│       └── router.py          # POST /api/parse
│
└── tests/
    ├── conftest.py            # loads the real catalog once, test DB session
    ├── fixtures/
    │   ├── requests.json      # Menon, UAE, DEL/BOM/MAA, 1A+3C, 8 travelers, 22:50 KIX landing,
    │   │                      # 11:00 return, start 18 Apr (no package), tiny budget (M8)
    │   └── menon_package.json # hand-written valid Menon package; backs the engine stubs
    ├── unit/
    │   ├── test_timeutil.py   # 24:00, past-midnight windows, inclusive ends
    │   ├── test_pricing.py    # PER_VEHICLE rounding, child_price 0 vs missing
    │   ├── test_rules.py      # one test per rule ID, pass + fail case
    │   ├── test_city_plans.py # plan counts (Japan 10 nights = 135), link check
    │   └── test_builder.py    # every fixture → validate() == [] or the expected outcome
    ├── oracle/
    │   └── test_fast_vs_brute.py   # strategy="fast" and "brute" give the same totals
    └── api/
        ├── test_packages_api.py    # build, get, export
        ├── test_changes_api.py     # valid change, refused change (409), version conflict
        └── test_reservations_api.py # confirm, lookup after restart, "not found", bad format
```

### Module dependency rules

Dependencies point one way only. This keeps the logic testable without the API or the database.

```
routers (packages, changes, export, reservations, parser, catalog/router)
   │
   ▼
services (packages/service, changes/apply, reservations/service, inventory/service)
   │
   ▼
domain:   builder ──► rules ──► pricing ──► catalog ──► core
             └──────────────────────────────┘
   │
   ▼
repositories (packages, reservations, inventory) ──► core/database ──► MySQL
```

- `catalog`, `pricing`, `rules` and `builder` never import a router, a repository or SQLAlchemy.
- Only `catalog/loader.py` reads raw JSON field names. Everything else uses the dataclasses.
- Every path that returns or stores a package calls `rules.validator.validate()` first.

---

## 4. `frontend/`

```
frontend/
├── package.json
├── vite.config.ts             # dev proxy: /api and /images → backend
├── tsconfig.json
├── tailwind.config.js
├── Dockerfile
├── index.html
└── src/
    ├── main.tsx
    ├── App.tsx                # layout, footer with photo credits
    ├── routes.tsx             # "/", "/package/:id", "/reservation/:ref", "*"
    │
    ├── api/                   # the ONLY place that calls the backend
    │   ├── client.ts          # fetch wrapper, error shape {code, message, details}
    │   ├── types.ts           # TS types mirroring backend Pydantic schemas
    │   ├── meta.ts            # GET /api/meta
    │   ├── packages.ts        # build, get, options, change, undo, city-plans, rebuild, export
    │   ├── reservations.ts    # confirm, lookup
    │   └── parse.ts           # S1 quick request
    │
    ├── pages/
    │   ├── RequestPage.tsx    # M1 form (+ S1 box), routes to package or outcome panel
    │   ├── PackagePage.tsx    # M4 timeline, M5 totals + export, M6 changes, M7 confirm
    │   ├── ReservationPage.tsx # M7 summary + lookup, "Reservation not found"
    │   └── NotFoundPage.tsx
    │
    ├── components/
    │   ├── request/
    │   │   ├── RequestForm.tsx        # 7 fields, inline errors from 422
    │   │   ├── ChildAgesInput.tsx     # one age input per child
    │   │   └── QuickRequestBox.tsx    # S1
    │   ├── outcome/
    │   │   ├── OverBudgetPanel.tsx    # M8: cheapest total, gap, suggestion
    │   │   └── NoPackagePanel.tsx     # M2: reason
    │   ├── package/
    │   │   ├── CityPlanHeader.tsx     # cities + nights
    │   │   ├── BudgetBar.tsx          # total, budget, left / over
    │   │   ├── DayTimeline.tsx        # list of days
    │   │   ├── DayCard.tsx            # one day, items in time order
    │   │   ├── ItemRow.tsx            # flight / hotel / transfer / attraction row + change button
    │   │   ├── PriceBreakdown.tsx     # line items
    │   │   ├── AlternativesPicker.tsx # G4 cheapest / fastest / best rated
    │   │   └── CityPlanPicker.tsx     # G3
    │   ├── change/
    │   │   ├── ChangeDrawer.tsx       # opens per item
    │   │   ├── OptionList.tsx         # options from the backend
    │   │   ├── PriceDiff.tsx          # +₹ / −₹ (G2)
    │   │   └── SideEffectsAlert.tsx   # G1 warnings, 409 refusal reasons
    │   ├── reservation/
    │   │   ├── ReservationSummary.tsx
    │   │   └── LookupBox.tsx
    │   └── common/
    │       ├── Money.tsx              # ₹ with Indian grouping (₹3,50,000)
    │       ├── LocalTime.tsx          # time + zone label (JST / GST / IST)
    │       ├── ErrorBanner.tsx
    │       ├── Spinner.tsx
    │       ├── Photo.tsx              # <img src="/{image}"> for a hotel / attraction, with fallback
    │       └── PhotoCredits.tsx       # renders /images/ATTRIBUTIONS.md (served by the backend)
    │
    ├── hooks/
    │   ├── useMeta.ts
    │   └── usePackage.ts      # load by id (survives refresh), apply change, keep version
    ├── utils/
    │   └── format.ts          # dates, durations
    └── styles/
        └── index.css
```

The frontend computes nothing: no prices, no rules, no city choice. It renders what the API returns, as the brief requires.

---

## 5. Feature → folder map

| Feature | Backend | Frontend | Database |
|---|---|---|---|
| M1 Request form | `packages/schemas.py`, `catalog/router.py` | `RequestForm`, `ChildAgesInput` | — |
| M2 Build one package | `builder/*`, `packages/service.py` | `RequestPage`, `NoPackagePanel` | `trip_requests`, `packages`, `package_versions` |
| M3 Rules respected | `rules/*` | — | — |
| M4 Day-by-day plan | `packages/timeline.py` | `DayTimeline`, `DayCard`, `ItemRow` | — |
| M5 Total + export | `pricing/*`, `export/*` | `BudgetBar`, `PriceBreakdown` | — |
| M6 Change package | `changes/*` | `ChangeDrawer`, `OptionList` | `package_versions` |
| M7 Confirm + summary | `reservations/*`, `export/trip_format.py` | `ReservationPage`, `ReservationSummary` | `reservations` |
| M8 Budget too small | `builder/selector.py`, `builder/failures.py` | `OverBudgetPanel` | — |
| G1 Knock-on effects | `changes/side_effects.py` | `SideEffectsAlert` | — |
| G2 Price difference | `changes/options.py` | `PriceDiff` | — |
| G3 Change cities | `builder/city_plans.py`, `packages/router.py` | `CityPlanPicker` | — |
| G4 Three packages | `builder/selector.py` | `AlternativesPicker` | — |
| S1 Quick request | `parser/*` | `QuickRequestBox` | — |
| S2 Seats and rooms used | `inventory/*`, `reservations/service.py` | — | `inventory_usage` |

---

## 6. Ownership (team of 2)

| Person | Owns | Interface with the other person |
|---|---|---|
| A (engine) | `core/timeutil.py`, `catalog/`, `pricing/`, `rules/`, `builder/`, `changes/options.py` + `side_effects.py`, `tests/unit`, `tests/oracle` | Pure functions: `build(req)`, `validate(pkg)`, `options(pkg, ...)` |
| B (API + UI + DB) | `database/`, `core/database.py`, `packages/`, `changes/router.py` + `apply.py`, `export/`, `reservations/`, `inventory/`, `parser/`, `frontend/`, `tests/api` | API contract in `docs/PRD.md` section 10, frozen in hour 1 |

---

## 7. Start commands (for README)

```bash
# 1. Docker (recommended)
docker compose up --build        # MySQL :3306, API :8000 (/docs), web :5173

# 2. Without Docker (MySQL already running, DB_URL in .env)
./start.sh                       # applies database/schema, starts backend + frontend
```

Run tests: `cd backend && pytest`.
