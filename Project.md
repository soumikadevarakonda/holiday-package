# Project Plan — Backend API Split (2 people)

Goal: every backend API in [PRD-Build-My-Holiday.md](PRD-Build-My-Holiday.md) section 10 is working, tested and callable from `/docs`, **before** frontend work starts.

The split lets both people work at the same time without blocking each other:

- **Person A (Engine):** the pure Python logic. Catalog, pricing, rules, builder, change options, quick-request parser. No HTTP except two read-only endpoints, and no database except loading the catalog tables once at startup.
- **Person B (API + DB):** everything that touches HTTP or MySQL. Routers, schemas, database, packages, changes, export, reservations, inventory.

They meet at **5 engine functions** with fixed signatures (section 3). Person A ships **stubs** of these in the first hour, so Person B can build and test every endpoint against fake-but-valid data while A writes the real logic. When A replaces a stub, B's endpoints start returning real packages with no code change.

---

## 1. Phase 0 — ✅ complete

Phase 0 is done and goes to `main` before the split. Both people should still read [data/problem-1-holiday-package.md](data/problem-1-holiday-package.md) (the official brief) and [data/DATA_DICTIONARY.md](data/DATA_DICTIONARY.md), including the FAQ.

| # | Task | Status | Files |
|---|---|---|---|
| 0.1 | Settings from `.env` (`DB_URL`, `DATA_DIR`, `DATABASE_DIR`, ports, CORS, `DB_AUTO_INIT`) | ✅ | `backend/app/core/config.py`, `.env.example` |
| 0.2 | Error shape `{code, message, details}`, `AppError`, handlers (422 → `INVALID_INPUT` with `field_errors`) | ✅ | `backend/app/core/errors.py` |
| 0.3 | FastAPI app, CORS, all 6 routers mounted (empty), `GET /api/health`, `/images` static files | ✅ | `backend/app/main.py`, `*/router.py` |
| 0.4 | **Shared model**: `TripRequest`, `Package` (+ `to/from_trip_format`), `Item`, `CityStay`, `Totals`, `Violation`, `BuildResult`, `CityPlanSummary`, `Option`, `Change`, `ChangeResult` | ✅ | `backend/app/core/package_model.py` |
| 0.5 | **5 engine signatures frozen + stubs** (section 3) | ✅ | `builder/search.py`, `rules/validator.py`, `changes/options.py`, `changes/side_effects.py`, `catalog/store.py`, `app/stubs.py` |
| 0.6 | Menon package from real catalog IDs (Tokyo 3 + Kyoto 3, ₹2,34,710) | ✅ | `backend/tests/fixtures/menon_package.json` |
| 0.7 | **MySQL schema from the ER diagram** (catalog) + app-state tables | ✅ | `database/init/000_create_database.sql`, `database/schema/001–010_*.sql`, `database/README.md` |
| 0.8 | Apply schema + seed catalog from JSON (on startup, or by hand) | ✅ | `backend/app/core/migrate.py`, `backend/app/catalog/seed.py`, `database/scripts/*.sh` |
| 0.9 | DB engine + per-request transaction + ping | ✅ | `backend/app/core/database.py` |
| 0.10 | Python deps, pytest config, `__init__.py` everywhere, Phase 0 tests (8 passing) | ✅ | `backend/requirements.txt`, `backend/pytest.ini`, `backend/tests/conftest.py`, `backend/tests/test_phase0.py` |
| 0.11 | Docker + no-Docker start, `.gitignore` | ✅ | `docker-compose.yml`, `backend/Dockerfile`, `start.sh`, `.gitignore` |

**Exit check:** `uvicorn app.main:app` starts and `/docs` loads. `GET /api/health` returns `200` with `"db": true, "catalog_seeded": true`. `/images/attractions/ATT-KYO-001.jpg` and `/images/ATTRIBUTIONS.md` open. `pytest` is green. The steps are in section 9.

### Database design (from the ER diagram)

The catalog now lives in **MySQL tables that follow [database/travel_platform_er_diagram.md](database/travel_platform_er_diagram.md)**: `country`, `destination_city`, `airport`, `city_airport`, `departure_city`, `flight`, `hotel`, `room`, `room_availability`, `transfer` + `airport_transfer` / `city_transfer` / `intercity_transfer`, `intercity_link`, `link_transfer` and `attraction`.

- `data/catalog/*.json` stays the read-only source. `catalog/seed.py` copies it into the tables on startup, and only when the files change.
- At M-1, Person A's `catalog/loader.py` reads these tables **once at startup** into the in-memory `CatalogStore`. The engine never queries MySQL per request, so it stays fast and testable.
- The ER diagram shows key columns only. The schema adds every field the rules need (prices, service hours, opening days, …). The differences are listed in [database/README.md](database/README.md).
- The app-state tables (`trip_requests`, `packages`, `package_versions`, `reservations`, `inventory_usage`) are now `006–010`.

> Shared files after Phase 0: `core/package_model.py`, `core/config.py` and `main.py` (router and startup lines only). Changing them needs both people to agree.

---

## 2. Who owns what

### Person A — Engine

| Folder / file | What it does | Features | Status |
|---|---|---|---|
| `backend/app/core/timeutil.py` | `HH:MM` and `24:00` parsing, windows past midnight, inclusive ends, weekday, ISO date-times, `next_grid_slot` | all | ✅ M-1 |
| `backend/app/core/money.py` | `format_inr()`: Indian grouping (₹3,50,000) | M5 | ✅ M-1 |
| `backend/app/catalog/models.py` | Frozen dataclasses for every catalog record, plus `DepartureCity`, `IntercityLink`, `RulesMeta` | M1 | ✅ M-1 |
| `backend/app/catalog/loader.py` | MySQL catalog tables → models at startup (`child_price` NULL ≠ 0, JSON columns → lists). Falls back to the JSON files when MySQL is unreachable or `DB_AUTO_INIT=false` (tests). Verified: DB and JSON loads are identical | M1 | ✅ M-1 |
| `backend/app/catalog/indexes.py` | `CatalogIndexes`: flights by (from, arrival date) / (to, departure date), airports serving a city, hotels by city, rooms by hotel, availability by (room, date), airport transfers by (airport, city), inter-city by route, link transfer IDs, attractions by city, `max_flight_seats` | all | ✅ M-1 |
| `backend/app/catalog/store.py` | `CatalogStore` singleton, `load()`, query helpers (`get_arrival_flights`, `get_hotels_in_city`, `get_rooms_left`, …); loaded in `main.py` lifespan | all | ✅ M-1 |
| `backend/app/catalog/router.py` | **`GET /api/meta`**: departure cities, countries + cities, rules, `max_flight_seats` | M1 | ✅ M-1 |
| `backend/app/pricing/calculator.py` | Price formulas (flight, hotel, transfer PER_PERSON / PER_VEHICLE, attraction; `is not None` on `child_price`) | M5, P1 | ✅ M-1 |
| `backend/app/pricing/totals.py` | `compute_totals(items, budget)` → `Totals` by type, left / over | M5 | ✅ M-1 |
| `backend/app/rules/violations.py` | `Violation` + `to_dicts()` (Phase 0) | M3 | ✅ Phase 0 |
| `backend/app/rules/context.py` | Parses a package once (flights, stays, transfers by kind, visits) for all checks | M3 | ✅ M-2 |
| `backend/app/rules/validator.py` | `validate(pkg, *, initial, seats_used, rooms_used)`: runs all checks | M3 | ✅ M-2 |
| `backend/app/rules/checks/*.py` | `dates` (D1–D3), `flights` (F1–F4), `airport_transfers` (AT1–AT4), `intercity` (CT1), `hotels` (H1–H4), `attractions` (A1–A4), `prices` (P1, 1%) | M3 | ✅ M-2 |
| `backend/app/builder/*.py` | `city_plans` (enumerate), `hotels` (memoized cheapest stays), `flights`, `transfers` (+60 / −180 / grid ≥ 10:00), `attractions` (matching: 1 per full day), `assemble`, `failures`, `selector` (city rule + G4), `search` (`build`, `rebuild`, M8 suggestion) | M2, M8, G3, G4 | ✅ M-2 (G3 `rebuild` and G4 `mode="three"` included) |
| `backend/app/changes/options.py` | Hotel (per city), flight (arrival / return) and attraction (per date) alternatives. Each is applied to a copy and validated, so only valid choices are offered; `price_diff` = new total − current total. The current choice is flagged in `details.current` | M6, G2 | ✅ M-3 |
| `backend/app/changes/side_effects.py` | `apply_change()` for hotel / flight / add / remove attraction. Re-picks and re-times airport transfers, drops arrival-day visits that no longer fit, warns about check-in time and empty days. Raises `ChangeError` for impossible requests | M6, G1 | ✅ M-3 |
| `backend/app/parser/quick_request.py` | Regex + keywords: city / country aliases (Bombay, Tokyo, UAE…), dates (10 Apr, April 5th, 8/4, ISO), nights / "a week", adults, kids + ages, budget (3.5 lakh, ₹2,50,000, 300k) | S1 | ✅ M-4 |
| `backend/app/parser/router.py` | **`POST /api/parse`** → `{request, unparsed, warnings}` | S1 | ✅ M-4 |
| `backend/tests/conftest.py` | `catalog_store` (session), `client`, `menon` fixtures; forces `DB_AUTO_INIT=false` so tests use the JSON catalog | — | ✅ M-1 |
| `backend/tests/fixtures/requests.json` | 9 requests with expected outcomes: Menon, UAE (BOM), DEL → HND, 1A+3C, Japan 10 nights, return after window, 10 travelers, 8 travelers on full flights, tiny budget | — | ✅ M-2 |
| `backend/tests/unit/*` | `test_timeutil`, `test_pricing`, `test_rules` (pass + fail per rule ID), `test_city_plans` (135 plans), `test_builder` (every fixture, determinism, M8, rebuild), `test_changes` (every option stays valid, G1 effects, errors), `test_parser` | — | ✅ 7 of 7 |
| `backend/tests/oracle/test_fast_vs_brute.py` | `strategy="brute"` tries every flight × transfer × hotel combination at both ends; plan totals must equal the fast search on every fixture | — | ✅ M-4 |
| `backend/tests/api/test_packages_api.py` | `GET /api/meta` and `POST /api/parse` tests (A's endpoints; B adds package tests here) | M1, S1 | ✅ |
| `backend/tests/helpers.py` | `menon_package()`, `to_request()`, `MENON_REQUEST` (replaces the deleted `app/stubs.py`) | — | ✅ |

Legend: ✅ done · ⏳ stub in place, real version due · 🔶 partly done · ⬜ not started.

**M-1 review notes (all handled in M-2):**
- ✅ The inter-city builder and CT1 check service hours and the frequency grid, not just `next_grid_slot()`.
- ✅ The builder and AT1 match the transfer `area == hotel.area or area is None`.
- ✅ `/api/health` has `catalog_source` (`"mysql"` normally, `"json"` if MySQL was unreachable).

**M-2 results** (from `tests/fixtures/requests.json`; the builder runs in 0.01–0.2 s):

| Request | Outcome |
|---|---|
| Menon (BLR → Japan, 6 nights, 2A + 1C) | Tokyo 2 + Osaka 4, **₹2,30,440** (matches the PRD estimate); validates `[]` |
| Tiny budget (₹50,000) | `OVER_BUDGET`: cheapest ₹2,19,324 (Tokyo only) + suggestion |
| Japan 10 nights | 135 plans checked; Tokyo 2 + Kyoto 6 + Osaka 2 |
| Start 18 Apr + 3 nights | `NO_PACKAGE`: "Flights run from 1 Apr 2027 to 20 Apr 2027. A 3-night trip from 18 Apr 2027 returns on 21 Apr 2027." |
| 10 travelers | `NO_PACKAGE`: "No flight has more than 9 seats left; …" |

**M-3 / M-4 results:** 103 tests green.
- Picking a later arrival flight (FL-405, lands 21:30) switches the arrival transfer to the Narita taxi at 22:30 (PRD edge case).
- An arrival-day visit that no longer fits is removed, with a side-effect message.
- Fast and brute-force search agree on every city plan total of every fixture.

**Person A's backend work is complete.** What's left is joint: the sync checks with Person B's endpoints (M-2 … M-4), and fixes they turn up.

### Person B — API + Database

| Folder / file | What it does | Features |
|---|---|---|
| `database/schema/006–010_*.sql` | App-state tables (written in Phase 0). Extend them if needed with a new numbered file, never by editing a file already applied | — |
| `docker-compose.yml`, `start.sh` | Add the frontend service / start command after M-2 | — |
| `backend/app/core/database.py` | Written in Phase 0 (`get_db`, `db_ping`); add helpers if needed | — |
| `backend/app/packages/schemas.py` | Pydantic request/response models, M1 field checks (`422`) | M1 |
| `backend/app/packages/repository.py` | Save / load requests, packages, versions | M2 |
| `backend/app/packages/service.py` | Validate request → `build()` → save version → response | M2, M8 |
| `backend/app/packages/timeline.py` | Day-by-day plan in time order | M4 |
| `backend/app/packages/router.py` | **Build, get, city-plans, rebuild, undo** | M2, M4, G3, G4 |
| `backend/app/changes/apply.py` | Apply a change on a copy → `validate()` → save or `409` | M6 |
| `backend/app/changes/router.py` | **Options + PATCH** | M6, G1, G2 |
| `backend/app/export/trip_format.py` | Package → shared trip format JSON (DATA_DICTIONARY section 4; times as `YYYY-MM-DDTHH:MM`, match `data/trip_format_example.json`) | M5, M7 |
| `backend/app/export/router.py` | **Export** | M5 |
| `backend/app/reservations/reference.py` | Random 10-digit number, retry on duplicate | M7 |
| `backend/app/reservations/repository.py` | `reservations` table | M7 |
| `backend/app/reservations/service.py` | Confirm transaction (re-validate → inventory → snapshot → BOOKED) | M7, S2 |
| `backend/app/reservations/router.py` | **Confirm + lookup** | M7 |
| `backend/app/inventory/service.py`, `repository.py` | Effective seats / rooms = catalog − booked | S2 |
| `backend/tests/api/*` | `test_packages_api`, `test_changes_api`, `test_reservations_api` | — |

---

## 3. The interface between A and B

Person A owns these functions. Person B only **calls** them. The signatures are frozen in Phase 0.

| # | Function (file) | Returns | Used by B in |
|---|---|---|---|
| 1 | `build(req: TripRequest, mode="default", strategy="fast") -> BuildResult` (`builder/search.py`) | `BuildResult(outcome, package, alternatives, city_plans, cheapest_total, over_by, suggestion, reason)`; `outcome` ∈ `PACKAGE`, `OVER_BUDGET`, `NO_PACKAGE` | `packages/service.py` |
| 2 | `rebuild(req, city_plan) -> BuildResult` (`builder/search.py`) | Same as above, on one plan | `packages/service.py` |
| 3 | `validate(pkg: Package, *, initial=False, seats_used=None, rooms_used=None) -> list[Violation]` (`rules/validator.py`) | Empty list = valid. `initial=True` only for the first built package (A3). `seats_used` / `rooms_used` = S2 bookings from `inventory_usage` (pass them in confirm) | `changes/apply.py`, `reservations/service.py`, `export/router.py` |
| 4 | `options(pkg, kind, **params) -> list[Option]` (`changes/options.py`) | `kind` ∈ `hotel` (`city=`), `flight` (`leg="arrival"\|"return"`), `attraction` (`date="YYYY-MM-DD"`); each option has `price_diff`, attractions a suggested `start`, `details.current` marks the current choice. Raises `ChangeError` for a bad kind / city / date | `changes/router.py` |
| 5 | `apply_change(pkg, change) -> ChangeResult` (`changes/side_effects.py`) | `ChangeResult(package, side_effects, warnings)`: a new package (input untouched), **not yet validated**. Raises `ChangeError` (unknown ID, wrong item, room that can't fit) → B returns `422`; violations from `validate()` → B returns `409 RULE_VIOLATION` | `changes/apply.py` |

Plus the catalog accessor `get_store() -> CatalogStore` (`catalog/store.py`) for B's inventory checks and `seats_left` / `rooms_left`. All types live in `core/package_model.py`.

**Stubs (✅ in Phase 0):** every function exists with its final signature and returns data from `tests/fixtures/menon_package.json` through `app/stubs.py`.

| Stub | Phase 0 behaviour |
|---|---|
| `build` / `rebuild` | ✅ Real since M-2: `PACKAGE` / `OVER_BUDGET` (+ `cheapest_total`, `over_by`, `suggestion`) / `NO_PACKAGE` (+ `reason`); `city_plans` ranked; `mode="three"` fills `cheapest`, `fastest`, `best_rated` |
| `validate` | ✅ Real since M-2: every rule ID D1–P1 |
| `options` | ✅ Real since M-3 |
| `apply_change` | ✅ Real since M-3 |
| `get_store` | ✅ Real since M-1: the full catalog in memory, `loaded = True` |

All stubs are replaced, and `app/stubs.py` is deleted; the Menon fixture loader now lives in `tests/helpers.py`.

---

## 4. API endpoints — owner and readiness

"Real at" = the milestone (section 5) when the endpoint stops using stubs.

| # | Method + path | Owner | Engine call | Real at |
|---|---|---|---|---|
| 1 | `GET /api/health` | Both (Phase 0) | — | Phase 0 |
| 2 | `GET /api/meta` | **A** | catalog store | ✅ M-1 |
| 3 | `POST /api/parse` | **A** | parser | ✅ M-4 |
| 4 | `POST /api/packages` | **B** | `build()` ✅ real | M-2 |
| 5 | `GET /api/packages/{id}` | **B** | — (DB + timeline) | M-1 |
| 6 | `GET /api/packages/{id}/options/hotel?city=` | **B** | `options()` | M-3 (engine ✅, endpoint ⬜) |
| 7 | `GET /api/packages/{id}/options/flight?leg=` | **B** | `options()` | M-3 (engine ✅, endpoint ⬜) |
| 8 | `GET /api/packages/{id}/options/attraction?date=` | **B** | `options()` | M-3 (engine ✅, endpoint ⬜) |
| 9 | `PATCH /api/packages/{id}` | **B** | `apply_change()` + `validate()` | M-3 (engine ✅, endpoint ⬜) |
| 10 | `GET /api/packages/{id}/city-plans` | **B** | `BuildResult.city_plans` | M-2 |
| 11 | `POST /api/packages/{id}/rebuild` | **B** | `rebuild()` | M-4 (engine ✅, endpoint ⬜) |
| 12 | `POST /api/packages/{id}/undo` | **B** | — (DB) | M-1 |
| 13 | `GET /api/packages/{id}/export` | **B** | `validate()` | M-2 |
| 14 | `POST /api/packages/{id}/confirm` | **B** | `validate()` | M-2 |
| 15 | `GET /api/reservations/{ref}` | **B** | — (DB) | M-1 |

Person B owns more endpoints, but most are thin. Person A owns the hard logic behind them.

---

## 5. Timeline and sync points

| Milestone | Person A delivers | Person B delivers | Sync check (together) |
|---|---|---|---|
| **Phase 0** ✅ | Package model, stubs, Menon fixture | ER schema, seed, DB plumbing, Docker | App starts, `/docs` loads, catalog seeded, 8 tests green |
| **M-1** (h 1–3) | ✅ `timeutil`, catalog loader (MySQL → memory, JSON fallback) + indexes + store, `GET /api/meta`, pricing + tests (21 tests green) | Repositories, endpoints 4, 5, 12, 15 working on stubs; reservation number | `GET /api/meta` real; build → get → undo → confirm → lookup work end-to-end on the stub package |
| **M-2** (h 3–5) | ✅ All rule checks with pass + fail tests; real `build()` / `rebuild()` (city rule, M8, G3, G4); 65 tests green | Timeline, export, confirm transaction, city-plans; `tests/api` for packages + reservations | **Real** Menon package builds, exports, validates (`[]`) and confirms |
| **M-3** (h 5–7) | ✅ `OVER_BUDGET` / `NO_PACKAGE` with reasons (done in M-2); `options()`; `apply_change()` + `ChangeError` | Options + PATCH endpoints, `409 RULE_VIOLATION`, `409 VERSION_CONFLICT`; `tests/api` for changes | Change hotel, flight, attraction; a bad change is refused; tiny budget gives M8 |
| **M-4** (h 7–9) | ✅ G4 `mode="three"` and `rebuild()` (done in M-2), parser + `POST /api/parse`, fast vs brute oracle; 103 tests green | Rebuild endpoint, S2 inventory in confirm, `start.sh` | All 15 endpoints real; full test suite green |

After M-2 the frontend can start against the real API.

---

## 6. How each person works

**Person A (engine)**

1. Write a unit test first for each rule ID and each price formula (pass case + fail case).
2. Never import FastAPI, SQLAlchemy or a repository in `catalog/`, `pricing/`, `rules/` or `builder/`. The exceptions are `catalog/seed.py` and `catalog/loader.py`, which run only at startup.
3. Replace one stub at a time; keep its signature exactly.
4. Run `pytest tests/unit tests/oracle` before every push.

**Person B (API + DB)**

1. All engine functions are real (no stubs left), so every endpoint returns real packages from the start. Test each one with `httpx` in `tests/api` and by hand in `/docs`.
2. Every path that returns or stores a package calls `validate()` first.
3. Every write takes `base_version`; a stale one gets `409 VERSION_CONFLICT`.
4. Business outcomes (`OVER_BUDGET`, `NO_PACKAGE`) return `200` with `outcome`; bad input returns `422`.
5. Run `pytest tests/api` before every push.

---

## 7. Git workflow

- Phase 0 goes straight to `main`.
- Then one branch each: `engine` (A) and `api` (B). Small commits tagged by feature, e.g. `M3: hotel rules H1–H4`, `M7: confirm endpoint`.
- Merge into `main` at every sync point (M-1 … M-4), run the **full** test suite on `main`, then both rebase.
- The two branches touch different folders, so merge conflicts should only happen in `core/package_model.py` (agree first) and `main.py` (router lines only).

---

## 8. Definition of done (per endpoint)

An endpoint is done when:

1. It matches the request / response / error shape in PRD section 10.
2. It works in `/docs` with the Menon request and at least one failing request.
3. It has at least one passing test in `tests/api` (B) or `tests/unit` (A).
4. Any package it returns or stores passes `validate()`.
5. It survives a backend restart (anything stored is read back from MySQL).

---

## 9. Running the backend after Phase 0

### Option A: local MySQL (Windows, no Docker)

Run these from the repo root in Git Bash. PowerShell equivalents are noted where they differ.

1. **Create the database and dev user** (once). It asks for your MySQL root password:
   ```bash
   mysql -u root -p < database/init/000_create_database.sql
   ```
   This creates database `holiday` and user `holiday` / `holiday`.
2. **Create `.env`** (once):
   ```bash
   cp .env.example .env            # PowerShell: Copy-Item .env.example .env
   ```
   The default `DB_URL=mysql+pymysql://holiday:holiday@localhost:3306/holiday` matches step 1.
3. **Install Python deps** (once). The venv is already created in `backend/.venv`:
   ```bash
   cd backend
   python -m venv .venv            # only if .venv is missing
   source .venv/Scripts/activate   # PowerShell: .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
4. **Start the API:**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   On startup it applies `database/schema/*.sql` and seeds the catalog tables from `data/catalog`. The first start takes a few seconds; later starts skip the seed.
5. **Check it:**
   - http://localhost:8000/api/health → `"status": "ok", "db": true, "catalog_seeded": true`
   - http://localhost:8000/docs → Swagger UI
   - http://localhost:8000/images/ATTRIBUTIONS.md → photo credits
6. **Run the tests** (from `backend/`, venv active):
   ```bash
   pytest
   ```

Steps 2–4 in one command: `./start.sh` (Git Bash).

### Option B: Docker

```bash
cp .env.example .env
docker compose up --build       # MySQL :3306 + API :8000
```

Docker Desktop must be running. The first start creates the database (`database/init`), and the backend then creates the tables and seeds the catalog.

### Useful commands (from `backend/`, venv active)

| Command | Does |
|---|---|
| `python -m app.core.migrate` | Apply `database/schema/*.sql` by hand |
| `python -m app.catalog.seed --force` | Re-fill the catalog tables from JSON |
| `mysql -u holiday -pholiday holiday < ../database/seeds/demo_reset.sql` | Clear packages and reservations before a demo |

### If something is wrong

| Symptom | Fix |
|---|---|
| Health shows `"db": false` | MySQL isn't running, or `DB_URL` in `.env` is wrong. `db_init_error` in the health response says which. |
| `Access denied for user 'holiday'` | Step 1 wasn't run, or `DB_URL` has another password |
| `"catalog_seeded": false` with `db: true` | Read `db_init_error`; re-run `python -m app.catalog.seed --force` |
| Port 8000 in use | `uvicorn app.main:app --reload --port 8001` |
