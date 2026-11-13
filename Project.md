# Project Plan — Backend API Split (2 people)

Goal: every backend API in [PRD-Build-My-Holiday.md](PRD-Build-My-Holiday.md) section 10 is working, tested and callable from `/docs`, **before** frontend work starts.

The split lets both people work at the same time without blocking each other:

- **Person A (Engine):** the pure Python logic. Catalog, pricing, rules, builder, change options, quick-request parser. No database, no HTTP (except two read-only endpoints).
- **Person B (API + DB):** everything that touches HTTP or MySQL. Routers, schemas, database, packages, changes, export, reservations, inventory.

They meet at **5 engine functions** with fixed signatures (section 3). Person A ships **stubs** of these in the first hour, so Person B can build and test every endpoint against fake-but-valid data while A writes the real logic. When A replaces a stub, B's endpoints start returning real packages with no code change.

---

## 1. Phase 0 — together (first ~1 hour)

Do this together on one machine, commit it to `main`, and then split.

| # | Task | Files |
|---|---|---|
| 0.1 | Settings from `.env` (`DB_URL`, `DATA_DIR`, ports) | `backend/app/core/config.py`, `.env.example` |
| 0.2 | Error shape `{code, message, details}` + `AppError` + exception handlers | `backend/app/core/errors.py` |
| 0.3 | FastAPI app, CORS, router mounting, `GET /api/health`, serve `data/images` at `/images` (StaticFiles) | `backend/app/main.py` |
| 0.4 | **Shared package model** (dataclasses: `TripRequest`, `Package`, `Item`, `CityStay`, `Totals`, `Violation`) | `backend/app/core/package_model.py` *(new file)* |
| 0.5 | **Freeze the 5 engine signatures** (section 3) and write stubs for them | see section 3 |
| 0.6 | One hand-written valid Menon package in trip format | `backend/tests/fixtures/menon_package.json` *(new file)* |
| 0.7 | Agree the MySQL schema (columns from PRD section 9) | `database/schema/*.sql` (B writes them after) |
| 0.8 | Python deps + pytest config | `backend/requirements.txt`, `backend/pytest.ini` |

**Exit check:** `uvicorn app.main:app` starts, `/docs` loads, `GET /api/health` returns `200`, `/images/attractions/ATT-KYO-001.jpg` and `/images/ATTRIBUTIONS.md` open.

**Before Phase 0, both people read** [data/problem-1-holiday-package.md](data/problem-1-holiday-package.md) (the official brief) and [data/DATA_DICTIONARY.md](data/DATA_DICTIONARY.md), including the FAQ at the end. The real catalog is already in `data/catalog/`, so A's loader and B's fixture use real IDs from day one.

> `core/package_model.py` is the only shared file after Phase 0. Changing it needs both people to agree.

---

## 2. Who owns what

### Person A — Engine

| Folder / file | What it does | Features |
|---|---|---|
| `backend/app/core/timeutil.py` | `HH:MM` and `24:00` parsing, windows past midnight, inclusive ends, weekday | all |
| `backend/app/core/money.py` | Integer INR helpers | M5 |
| `backend/app/catalog/models.py` | Dataclasses for every catalog record (keep hotel / attraction `image`) | M1 |
| `backend/app/catalog/loader.py` | Read `data/catalog/*.json` → models (the only file that knows raw field names). Unwrap `{amount, currency}` prices; parse `YYYY-MM-DDTHH:MM:SS` times; treat missing optional fields as absent | M1 |
| `backend/app/catalog/indexes.py` | Lookup dicts (flights by airport + date, availability by room + date, …) | all |
| `backend/app/catalog/store.py` | `CatalogStore` singleton + query functions | all |
| `backend/app/catalog/router.py` | **`GET /api/meta`** | M1 |
| `backend/app/pricing/calculator.py` | Price formulas (flight, hotel, transfer, attraction) | M5, P1 |
| `backend/app/pricing/totals.py` | Line items → total, budget left / over | M5 |
| `backend/app/rules/violations.py` | `Violation(rule_id, item_ref, message)` | M3 |
| `backend/app/rules/validator.py` | `validate(package)` — runs all checks | M3 |
| `backend/app/rules/checks/*.py` | `dates`, `flights`, `airport_transfers`, `intercity`, `hotels`, `attractions`, `prices` | M3 |
| `backend/app/builder/*.py` | `city_plans`, `hotels`, `flights`, `transfers`, `attractions`, `assemble`, `search`, `selector`, `failures` | M2, M8, G3, G4 |
| `backend/app/changes/options.py` | Valid alternatives + `price_diff` | M6, G2 |
| `backend/app/changes/side_effects.py` | Re-time transfers, drop attractions that no longer fit, warnings | G1 |
| `backend/app/parser/quick_request.py` | Regex parser for plain text | S1 |
| `backend/app/parser/router.py` | **`POST /api/parse`** | S1 |
| `backend/tests/conftest.py` | Load the real catalog once | — |
| `backend/tests/fixtures/requests.json` | Menon, UAE, DEL, 1A+3C, 8 travelers, late KIX, early return, bad date, tiny budget | — |
| `backend/tests/unit/*` | `test_timeutil`, `test_pricing`, `test_rules`, `test_city_plans`, `test_builder` | — |
| `backend/tests/oracle/test_fast_vs_brute.py` | Fast and brute search give the same totals | — |

### Person B — API + Database

| Folder / file | What it does | Features |
|---|---|---|
| `database/init/000_create_database.sql` | Create DB, user, grants | — |
| `database/schema/001–005_*.sql` | `trip_requests`, `packages`, `package_versions`, `reservations`, `inventory_usage` | — |
| `database/seeds/demo_reset.sql`, `database/scripts/*.sh` | Reset and apply scripts | — |
| `database/README.md` | How to apply / reset | — |
| `docker-compose.yml`, `backend/Dockerfile`, `start.sh` | Start everything in 1–2 commands | — |
| `backend/app/core/database.py` | SQLAlchemy engine + session dependency | — |
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
| 1 | `build(req: TripRequest, mode="default") -> BuildResult` (`builder/search.py`) | `BuildResult(outcome, package, alternatives, city_plans, cheapest_total, over_by, suggestion, reason)`; `outcome` ∈ `PACKAGE`, `OVER_BUDGET`, `NO_PACKAGE` | `packages/service.py` |
| 2 | `rebuild(req, city_plan) -> BuildResult` (`builder/search.py`) | Same as above, on one plan | `packages/service.py` |
| 3 | `validate(pkg: Package) -> list[Violation]` (`rules/validator.py`) | Empty list = valid | `changes/apply.py`, `reservations/service.py`, `export/router.py` |
| 4 | `options(pkg, kind, **params) -> list[Option]` (`changes/options.py`) | `kind` ∈ `hotel`, `flight`, `attraction`; each option has `price_diff` | `changes/router.py` |
| 5 | `apply_change(pkg, change) -> ChangeResult` (`changes/side_effects.py`) | `ChangeResult(package, side_effects, warnings)` — new package, **not yet validated** | `changes/apply.py` |

Plus the catalog accessor `get_store() -> CatalogStore` for B's inventory checks and `seats_left` / `rooms_left`.

**Stubs (Person A, end of Phase 0):** each function exists with the final signature and returns data built from `tests/fixtures/menon_package.json`. `validate()` returns `[]`. Commit the stubs to `main`, so B is never blocked.

---

## 4. API endpoints — owner and readiness

"Real at" = the milestone (section 5) when the endpoint stops using stubs.

| # | Method + path | Owner | Engine call | Real at |
|---|---|---|---|---|
| 1 | `GET /api/health` | Both (Phase 0) | — | Phase 0 |
| 2 | `GET /api/meta` | **A** | catalog store | M-1 |
| 3 | `POST /api/parse` | **A** | parser | M-4 |
| 4 | `POST /api/packages` | **B** | `build()` | M-2 |
| 5 | `GET /api/packages/{id}` | **B** | — (DB + timeline) | M-1 |
| 6 | `GET /api/packages/{id}/options/hotel?city=` | **B** | `options()` | M-3 |
| 7 | `GET /api/packages/{id}/options/flight?leg=` | **B** | `options()` | M-3 |
| 8 | `GET /api/packages/{id}/options/attraction?date=` | **B** | `options()` | M-3 |
| 9 | `PATCH /api/packages/{id}` | **B** | `apply_change()` + `validate()` | M-3 |
| 10 | `GET /api/packages/{id}/city-plans` | **B** | `BuildResult.city_plans` | M-2 |
| 11 | `POST /api/packages/{id}/rebuild` | **B** | `rebuild()` | M-4 |
| 12 | `POST /api/packages/{id}/undo` | **B** | — (DB) | M-1 |
| 13 | `GET /api/packages/{id}/export` | **B** | `validate()` | M-2 |
| 14 | `POST /api/packages/{id}/confirm` | **B** | `validate()` | M-2 |
| 15 | `GET /api/reservations/{ref}` | **B** | — (DB) | M-1 |

Person B owns more endpoints, but most are thin. Person A owns the hard logic behind them.

---

## 5. Timeline and sync points

| Milestone | Person A delivers | Person B delivers | Sync check (together) |
|---|---|---|---|
| **Phase 0** (h 0–1) | Package model, stubs, Menon fixture | DB schema agreed | App starts, `/docs` loads |
| **M-1** (h 1–3) | `timeutil`, catalog loader + indexes, `GET /api/meta`, pricing + tests | MySQL up (Docker), repositories, endpoints 4, 5, 12, 15 working on stubs; reservation number | `GET /api/meta` real; build → get → undo → confirm → lookup work end-to-end on the stub package |
| **M-2** (h 3–5) | All rule checks with one pass + one fail test each; real `build()` for Menon | Timeline, export, confirm transaction, city-plans; `tests/api` for packages + reservations | **Real** Menon package builds, exports, validates (`[]`) and confirms |
| **M-3** (h 5–7) | `build()` outcomes `OVER_BUDGET` / `NO_PACKAGE` with reasons; `options()`; `apply_change()` | Options + PATCH endpoints, `409 RULE_VIOLATION`, `409 VERSION_CONFLICT`; `tests/api` for changes | Change hotel, flight, attraction; a bad change is refused; tiny budget gives M8 |
| **M-4** (h 7–9) | G4 `mode="three"`, `rebuild()`, parser + `POST /api/parse`, fast vs brute oracle | Rebuild endpoint, S2 inventory in confirm, `start.sh` | All 15 endpoints real; full test suite green |

After M-2 the frontend can start against the real API.

---

## 6. How each person works

**Person A (engine)**

1. Write a unit test first for each rule ID and each price formula (pass case + fail case).
2. Never import FastAPI, SQLAlchemy or a repository in `catalog/`, `pricing/`, `rules/` or `builder/`.
3. Replace one stub at a time; keep its signature exactly.
4. Run `pytest tests/unit tests/oracle` before every push.

**Person B (API + DB)**

1. Build each endpoint against the stubs first; test it with `httpx` in `tests/api` and by hand in `/docs`.
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
