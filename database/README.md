# Build My Holiday — Database & Catalogue Management Layer

This package implements the data management layer for **Build My Holiday** (Booking Holdings Hackathon Problem 1).

---

## 1. Architecture Overview

The system adheres to a hybrid architecture designed for performance, consistency, and simplicity:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        BUILD MY HOLIDAY BACKEND                        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
          ┌─────────────────────────┴─────────────────────────┐
          ▼                                                   ▼
┌───────────────────────────────┐           ┌────────────────────────────────┐
│   Travel Catalogue Layer      │           │    Application Data Layer      │
│   (Read-Only JSON Files)      │           │     (MySQL 8.0+ Database)      │
├───────────────────────────────┤           ├────────────────────────────────┤
│ • destinations.json           │           │ • trips                        │
│ • airports.json               │           │ • trip_cities                  │
│ • flights.json                │           │ • trip_items                   │
│ • hotels.json                 │           │ • reservations                 │
│ • rooms.json                  │           │ • reservation_items            │
│ • availability.json           │           │                                │
│ • transfers.json              │           │ Referenced via catalogue_id:   │
│ • attractions.json            │           │ (No duplication of catalogue)  │
├───────────────────────────────┤           ├────────────────────────────────┤
│ Loaded into memory once on    │           │ Persisted via SQLAlchemy 2.0   │
│ startup; indexed via O(1)     │           │ with connection pooling and    │
│ lookups and relation caches.  │           │ ACID transactions.             │
└───────────────────────────────┘           └────────────────────────────────┘
```

1. **Read-only Catalogue (JSON)**: Original datasets in `hackathon-problem-1-holiday-package/data/catalog/` are treated as immutable truth. No catalogue data is imported into MySQL or modified on disk.
2. **In-Memory Catalogue Indexes**: Loaded into memory once at application startup using Python's built-in `json` module. Indexes provide $O(1)$ lookups and multi-key groupings without scanning entire JSON arrays.
3. **Application State (MySQL)**: Stores user requests, generated packages (`trips`, `trip_cities`, `trip_items`), and confirmed bookings (`reservations`, `reservation_items`). References catalogue items by stable IDs (e.g., `FL-401`, `HTL-TYO-001`).

---

## 2. Directory Structure

```
database/
├── __init__.py                # Package exports (Catalog, Repositories, Engine, etc.)
├── config.py                  # Database configuration from environment / .env
├── connection.py              # SQLAlchemy 2.0 engine, pooling, and session manager
├── catalog_loader.py          # Loads all 8 JSON datasets with relative path resolution
├── catalog_indexes.py         # In-memory indexes for fast travel queries
├── catalog_validator.py       # Validates ID uniqueness and referential integrity
├── schema.sql                 # MySQL schema for application-owned tables
├── test_database.py           # Comprehensive integration & unit test suite
├── README.md                  # Complete documentation
├── models/
│   ├── __init__.py            # DeclarativeBase and model exports
│   ├── trip.py                # Trip ORM model
│   ├── trip_city.py           # TripCity ORM model
│   ├── trip_item.py           # TripItem ORM model
│   └── reservation.py         # Reservation & ReservationItem ORM models
└── repositories/
    ├── __init__.py            # Repository exports
    ├── trip_repository.py     # Data access for trips, cities, and items
    └── reservation_repository.py # Data access for reservations & 10-digit refs
```

---

## 3. Catalogue Loader (`catalog_loader.py`)

Loads all 8 catalogue files relative to the project root:
- `destinations.json` (departure cities, destination countries, links, rules)
- `airports.json` (airports, timezones, served cities)
- `flights.json` (flight schedules, seat inventory, pricing)
- `hotels.json` (hotels, areas, star ratings)
- `rooms.json` (room capacities, nightly pricing)
- `availability.json` (room availability by night)
- `transfers.json` (airport shuttles, taxis, intercity trains and buses)
- `attractions.json` (attractions, opening hours, closed dates, admissions)

### Usage

```python
from database import get_catalog

# Access global singleton catalogue (loads once on first call)
catalog = get_catalog()

# Inspect summary counts
print(catalog.stats())
# {'airports': 10, 'flights': 469, 'hotels': 49, 'rooms': 125, ...}

# Access read-only datasets
airports = catalog.airports
hotels = catalog.hotels
```

---

## 4. Catalogue Indexes (`catalog_indexes.py`)

The catalogue index exposes optimized lookups without scanning JSON arrays:

| Lookup Requirement | Method / Attribute | Output |
|---|---|---|
| Airport by code | `indexes.get_airport("BLR")` | Airport record |
| Flights by route | `indexes.get_flights("BLR", "KIX")` | List of flights |
| Flights by arrival date | `indexes.get_flights_by_arrival_date("BLR", "KIX", "2027-04-10")` | List of matching flights |
| Hotels by city | `indexes.get_hotels_by_city("Tokyo")` | List of hotels in Tokyo |
| Hotel by ID | `indexes.get_hotel("HTL-TYO-001")` | Hotel record |
| Rooms by hotel ID | `indexes.get_rooms_by_hotel("HTL-TYO-001")` | List of rooms for hotel |
| Availability by room & date | `indexes.get_rooms_left("RM-TYO-001-A", "2027-04-01")` | Number of free rooms |
| Multi-night room check | `indexes.check_room_availability("RM-TYO-001-A", ["2027-04-01", ...], required_rooms=2)` | `True` / `False` |
| Intercity transfers | `indexes.get_transfers_by_route("Tokyo", "Kyoto")` | List of transfer services |
| Airport transfers | `indexes.get_airport_transfers("NRT", city="Tokyo", area="Ginza")` | Matching airport shuttles |
| Attractions by city | `indexes.get_attractions_by_city("Kyoto")` | List of attractions |
| Airports for destination city | `indexes.get_airports_for_destination_city("Kyoto")` | `["KIX"]` |
| Departure city to airport | `indexes.get_departure_airport("Bengaluru")` | `"BLR"` |

> [!NOTE]
> Intercity transfer routes are directional and not assumed to be bidirectional.

---

## 5. Catalogue Validator (`catalog_validator.py`)

Validates the integrity of the read-only catalog:
1. All 8 required JSON files exist and are valid JSON.
2. Identifiers are unique (`code`, `flight_id`, `hotel_id`, `room_id`, `transfer_id`, `attraction_id`).
3. Availability composite key `(room_id, date)` is unique.
4. Foreign key references exist:
   - `rooms.hotel_id` $\rightarrow$ `hotels.hotel_id`
   - `availability.room_id` $\rightarrow$ `rooms.room_id`
   - `flights.from` and `flights.to` $\rightarrow$ `airports.code`
   - `destinations.links.transfer_ids` $\rightarrow$ `transfers.transfer_id`
   - Departure and destination cities airports $\rightarrow$ `airports.code`
   - Airport transfers $\rightarrow$ `airports.code`

### Running the Validator CLI

```bash
python database/catalog_validator.py
```

Expected output:
```text
======================================================================
BUILD MY HOLIDAY - TRAVEL CATALOGUE VALIDATION REPORT
======================================================================
Overall Status : PASSED (VALID)
Total Errors   : 0
Total Warnings : 0
----------------------------------------------------------------------
Dataset Record Counts:
  - airports                : 10
  - flights                 : 469
  - hotels                  : 49
  - rooms                   : 125
  - availability            : 2500
  - transfers               : 66
  - attractions             : 56
  - destination_countries   : 2
  - departure_cities        : 4
======================================================================
```

---

## 6. MySQL Database Schema (`schema.sql`)

The schema defines tables for application-owned data:

### `trips`
- `trip_id` (VARCHAR(64), PK): Unique trip identifier.
- `departure_city` (VARCHAR(100)): Origin city (e.g. Bengaluru).
- `destination_country` (VARCHAR(100)): Destination country (e.g. Japan, UAE).
- `start_date` (DATE): Holiday arrival date.
- `nights` (INT): Total duration (3–10 nights per data dictionary rules).
- `adults` (INT): Number of adult travelers ($\ge 1$).
- `children` (INT): Number of children travelers ($\ge 0$).
- `child_ages` (JSON): Ages of traveling children (0–17).
- `budget` (DECIMAL(12, 2)): Budget constraint in INR.
- `status` (VARCHAR(32)): `DRAFT`, `PLANNED`, `BOOKED`, `CANCELLED`.
- `created_at`, `updated_at` (DATETIME).

### `trip_cities`
- `trip_city_id` (VARCHAR(64), PK).
- `trip_id` (VARCHAR(64), FK $\rightarrow$ `trips.trip_id` ON DELETE CASCADE).
- `city_name` (VARCHAR(100)).
- `nights` (INT, $\ge 1$).
- `sequence_order` (INT, UNIQUE with `trip_id`).

### `trip_items`
- `item_id` (VARCHAR(64), PK).
- `trip_id` (VARCHAR(64), FK $\rightarrow$ `trips.trip_id` ON DELETE CASCADE).
- `item_type` (VARCHAR(32)): `flight`, `hotel`, `transfer`, `attraction`.
- `catalogue_id` (VARCHAR(64)): Reference to catalogue item (e.g., `FL-401`, `HTL-TYO-001`).
- `city_name` (VARCHAR(100), nullable).
- `start_datetime`, `end_datetime` (DATETIME).
- `price` (DECIMAL(12, 2)): Computed item price in INR.
- `quantity` (INT, default 1).
- `item_details` (JSON): Item metadata, room type, warnings, etc.

### `reservations`
- `reservation_id` (VARCHAR(64), PK).
- `trip_id` (VARCHAR(64), FK $\rightarrow$ `trips.trip_id`).
- `reference` (VARCHAR(10), UNIQUE): Exactly 10 numeric digits (`^[0-9]{10}$`).
- `status` (VARCHAR(32), default `'CONFIRMED'`).
- `total_price` (DECIMAL(12, 2)).
- `created_at` (DATETIME).

### `reservation_items`
- `reservation_item_id` (VARCHAR(64), PK).
- `reservation_id` (VARCHAR(64), FK $\rightarrow$ `reservations.reservation_id` ON DELETE CASCADE).
- `item_type` (VARCHAR(32)).
- `catalogue_id` (VARCHAR(64)).
- `item_snapshot` (JSON): Complete immutable snapshot of the booked item.
- `price` (DECIMAL(12, 2)).
- `quantity` (INT).

### Applying the Schema to MySQL

```bash
mysql -u root -p < database/schema.sql
```

---

## 7. Database Connection & Configuration

Credentials and connection pool settings are configured via environment variables or a `.env` file at the project root.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DB_HOST` | `localhost` | MySQL hostname |
| `DB_PORT` | `3306` | MySQL port |
| `DB_USER` | `root` | Database username |
| `DB_PASSWORD` | *(empty)* | Database password |
| `DB_NAME` | `build_my_holiday` | Database name |
| `DB_POOL_SIZE` | `5` | Connection pool size |
| `DB_MAX_OVERFLOW` | `10` | Max overflow connections |
| `DB_POOL_RECYCLE` | `3600` | Connection recycle timeout in seconds |
| `DB_POOL_TIMEOUT` | `30` | Connection checkout timeout |
| `DATABASE_URL` | *(optional)* | Full SQLAlchemy database URL override |

### Context Manager Example

```python
from database import get_db_session, TripRepository

with get_db_session() as session:
    repo = TripRepository(session)
    trip = repo.get_trip_by_id("trip-1")
    # Changes are committed automatically on exit, rolled back on exception
```

---

## 8. Repositories

### `TripRepository`

Handles creating, retrieving, updating, and exporting trips:

```python
from database import get_db_session, TripRepository, Trip

with get_db_session() as session:
    repo = TripRepository(session)
    
    # Save a trip
    trip = repo.save_trip(trip_entity)
    
    # Query a trip
    trip = repo.get_trip_by_id("trip-menon-001")
    
    # Export in Problem 1 Section 4 format
    export_json = trip.to_export_format(traveler_name="Menon family")
```

### `ReservationRepository`

Handles booking confirmations and 10-digit references with collision retries:

```python
from database import get_db_session, ReservationRepository, TripRepository

with get_db_session() as session:
    trip_repo = TripRepository(session)
    res_repo = ReservationRepository(session)
    
    trip = trip_repo.get_trip_by_id("trip-menon-001")
    
    # Creates reservation, captures frozen item snapshots, transitions trip to BOOKED
    reservation = res_repo.create_reservation_from_trip(trip)
    print(f"Booking reference: {reservation.reference}")  # e.g., '4146937295'
    
    # Lookup by 10-digit reference (for /reservation/:ref endpoint)
    booking = res_repo.get_by_reference("4146937295")
```

---

## 9. Running Tests

To run the complete test suite verifying loader, indexes, validator, and SQLAlchemy repositories:

```bash
python database/test_database.py
```
