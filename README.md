# Build My Holiday

A web app that turns 7 inputs into one complete, rule-valid holiday package: flights, hotels, airport transfers, inter-city transfers and attractions. The app re-validates the whole package after every change and books it under a 10-digit reservation number.

**Stack:** React (Vite + TypeScript) · Python (FastAPI) · MySQL 8
**Build method:** enumerate + greedy + validate. No AI, no external solver.

Full details: [docs/PRD.md](docs/PRD.md) · [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)
Problem statement and data: [data/problem-1-holiday-package.md](data/problem-1-holiday-package.md) · [data/DATA_DICTIONARY.md](data/DATA_DICTIONARY.md)

---

## Data pack

The provided data lives in [data/](data/) and is **read-only**: the judges use the same files. Our own state (packages, reservations, inventory use) goes in MySQL.

| Path | Contents |
|---|---|
| `data/catalog/` | 8 JSON files: 10 airports, 469 flights, 49 hotels, 125 room types, 2,500 room-nights, 66 transfers, 56 attractions, plus destinations and rules |
| `data/DATA_DICTIONARY.md` | Every field, how the files link, the shared trip format, data FAQ |
| `data/trip_format_example.json` | Example of the export shape |
| `data/images/` | 56 attraction photos and 10 generic hotel photos, served by the backend at `/images` |
| `data/images/ATTRIBUTIONS.md` | Photo credits, shown on the app's photo-credits footer |

Flights and rooms exist only from **1 to 20 April 2027**.

---

## Quick start

```bash
cp .env.example .env

# 1. Docker (recommended)
docker compose up --build        # MySQL :3306, API :8000 (/docs); web :5173 added later

# 2. Without Docker (MySQL 8 running)
mysql -u root -p < database/init/000_create_database.sql   # once: database `holiday` + dev user
./start.sh                       # venv + deps, starts the API; startup creates tables and seeds the catalog
```

| Service | URL |
|---|---|
| Web app | http://localhost:5173 *(after M-2)* |
| API | http://localhost:8000/api |
| API docs (Swagger) | http://localhost:8000/docs |
| Health | http://localhost:8000/api/health |

Step-by-step instructions and troubleshooting: [Project.md, section 9](Project.md#9-running-the-backend-after-phase-0).

### Environment variables (`.env`)

| Variable | Purpose |
|---|---|
| `DB_URL` | MySQL connection string, default `mysql+pymysql://holiday:holiday@localhost:3306/holiday` |
| `DATA_DIR` | Data pack folder (default `<repo>/data`) |
| `DATABASE_DIR` | SQL folder (default `<repo>/database`) |
| `API_PORT` / `WEB_PORT` | Backend / frontend ports (`8000` / `5173`) |
| `CORS_ORIGINS` | Allowed frontend origins |
| `DB_AUTO_INIT` | `true`: apply `database/schema` and seed the catalog on startup |
| `MYSQL_ROOT_PASSWORD` | Docker only: root password of the MySQL container |

---

## Architecture

```mermaid
flowchart TB
  FE["React frontend (Vite)<br/>Request form · Day-by-day plan · Change panels · Reservation page"]
  FE -->|REST + JSON over /api| RT
  subgraph BE["Python backend (FastAPI)"]
    RT["API routers<br/>meta · packages · options · change · confirm · reservations · export"]
    RT --> BLD["Builder<br/>city plans, then cheapest valid parts"]
    RT --> CHG["Change service<br/>options, price diffs, re-time, re-check"]
    RT --> VAL["Validator<br/>every rule, by ID"]
    RT --> PRC["Pricing<br/>INR line items, total"]
  end
  BE -->|read-only, per request| CAT["Catalog store (in-memory)<br/>loaded once at startup"]
  JSON["data/catalog/*.json<br/>(read-only source)"] -->|seed on startup| CDB
  CDB -->|load once| CAT
  subgraph DB["MySQL 8"]
    CDB[("Catalog tables (ER diagram)<br/>country · city · airport · flight · hotel · room<br/>availability · transfer + subtypes · attraction")]
    ADB[("App state (ORM)<br/>trips · packages · package_versions<br/>reservations · reservation_items · inventory_usage")]
  end
  BE -->|SQLAlchemy| ADB
```

- **Frontend** displays only. It computes no prices, rules or city choices; it renders what the API returns.
- **Backend** holds all logic. Builder, change, confirm and export all call the same validator and pricing on the whole package.
- **Catalog**: the backend copies `data/catalog/*.json` into MySQL tables that follow the [ER diagram](database/travel_platform_er_diagram.md). It then loads those tables into memory once at startup. The JSON files are never edited. Photos in `data/images/` are served as static files at `/images`.
- **MySQL** also stores app state: requests, packages and their versions, reservations, and inventory use. See [database/README.md](database/README.md).

### Repository layout

```
├── data/        # provided data pack (brief, dictionary, catalog, images), untouched
├── docs/        # PRD and project structure
├── database/    # ER diagram, MySQL init, schema (001–005 catalog, 006–011 app state), seeds, scripts
├── backend/     # FastAPI app: core, catalog, pricing, rules, builder,
│                # packages, changes, export, reservations, inventory, parser
└── frontend/    # React app: api client, pages, components, hooks
```

Backend dependencies point one way: routers → services → domain (builder → rules → pricing → catalog → core) → repositories → MySQL. The domain modules never import a router, a repository or SQLAlchemy.

---

## City rule

The backend chooses the cities, their order and the nights per city.

1. **Target city count** `c* = max(1, floor(N / 3))`, capped by the cities in the country (Japan 3, UAE 2). That is about 3 nights per city: 6 nights → 2 cities; 9 nights → 3 in Japan, 2 in the UAE.
2. Among valid plans with `c*` cities, pick the **cheapest package within budget**.
3. If none fits, try `c* − 1` down to 1, then `c* + 1`.
4. If no plan fits the budget at any count, return the **over-budget** outcome (M8) with the cheapest possible package.

Each city gets at least 2 consecutive nights. For the Menon family (6 nights in Japan), this gives 2 cities at about ₹2,30,440 before paid attractions, against ₹2,19,324 for Tokyo alone: roughly 5% more for a more varied trip. The G4 alternatives still offer the cheapest package.

### How a package is built

1. Validate the request (M1).
2. Pre-filter arrival and return flights by local date and seats.
3. Enumerate city plans: city orders × night splits (at most 135 for Japan at 10 nights).
4. Per city, pick the cheapest valid hotel + room type + room count.
5. Pick the cheapest flight pair whose airport transfers fit the timing rules.
6. Pick inter-city transfers on the 30-minute departure grid.
7. Schedule attractions greedily (free and child-friendly first), with no overlaps.
8. Price every line item and run the full validator. Drop any plan that fails.
9. Choose by the city rule.

---

## Features

| ID | Feature | Status |
|---|---|---|
| M1 | Request form with backend validation | ☐ |
| M2 | Build one package (or explain why not) | ☐ |
| M3 | Every rule respected (shared validator) | ☐ |
| M4 | Day-by-day plan | ☐ |
| M5 | Total, budget, JSON export | ☐ |
| M6 | Change hotel, flight, attractions | ☐ |
| M7 | Confirm + 10-digit reservation + summary | ☐ |
| M8 | Budget too small | ☐ |
| G1 | Knock-on effects (re-time, drop, warn) | ☐ |
| G2 | Price difference on each option | ☐ |
| G3 | Change cities | ☐ |
| G4 | Cheapest, fastest, best-rated packages | ☐ |
| S1 | Quick request parser (rules only, no AI) | ☐ |
| S2 | Booking consumes seats and rooms | ☐ |
| S3 | Own idea | ☐ |

---

## Running tests

```bash
cd backend
pytest
```

- `tests/unit` — time helpers, pricing, one test per rule ID, city-plan counts, builder fixtures
- `tests/oracle` — fast and brute-force search give the same totals
- `tests/api` — build, change, refuse, confirm, lookup

---

## Known limitations

- Login, payments, real supplier booking and online deployment are out of scope.
- All prices are in INR; there is no multi-currency support.
- Attraction placement is greedy, not globally optimal (the rules don't require it).
- City-plan enumeration grows as O(C⁵) with the number of cities per country. That is fine for today's catalog (Japan 3, UAE 2); see the PRD, section 7, for the scaling path.
- Groups of 10 or more travelers are rejected: no flight in the catalog has more than 9 seats left.
- A change that pushes the total over budget is allowed, with a warning.
