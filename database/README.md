# Database

MySQL 8, database `holiday`. Two groups of tables:

| Group | Tables | Filled by |
|---|---|---|
| **Catalog** (ER diagram: [travel_platform_er_diagram.md](travel_platform_er_diagram.md)) | `country`, `destination_city`, `airport`, `city_airport`, `departure_city`, `flight`, `hotel`, `room`, `room_availability`, `transfer`, `airport_transfer`, `city_transfer`, `intercity_transfer`, `intercity_link`, `link_transfer`, `attraction`, `catalog_meta` | `python -m app.catalog.seed`, from `data/catalog/*.json` (read-only source) |
| **App state** | `trip_requests`, `packages`, `package_versions`, `reservations`, `inventory_usage` | The API |

## Files

| Path | What it does |
|---|---|
| `init/000_create_database.sql` | Creates the `holiday` database and the dev user `holiday` / `holiday`. Run once as root. Docker runs it on first start. |
| `schema/001–005_catalog_*.sql` | Catalog tables from the ER diagram |
| `schema/006–010_*.sql` | App-state tables |
| `seeds/demo_reset.sql` | Clears app state before a demo (keeps the catalog) |
| `scripts/apply_schema.sh` | Applies the schema and seeds the catalog by hand |
| `scripts/reset_db.sh` | Drops and rebuilds everything (dev only) |

Every schema file uses `CREATE TABLE IF NOT EXISTS`, so applying it again is safe. **The backend applies `schema/` and seeds the catalog on every startup** (`DB_AUTO_INIT=true`). The seed is skipped when the JSON files' hash hasn't changed.

## Where the schema differs from the ER diagram

The ER diagram shows key columns only. The schema keeps every table, key and relationship from it, and adds:

- **Every other catalog field** the rules need: prices, `child_price` (NULL ≠ 0), service hours, opening days and hours, `closed_dates`, `frequency_minutes`, stars, images and so on.
- `destination_city.name` is **UNIQUE**, so `hotel.city` and the transfer tables can reference a city by name.
- `departure_city` gets a primary key `(city, airport_code)`.
- `frequency_minutes` sits on `intercity_transfer` (only trains and intercity buses have it).
- **No FK from `attraction.city`**: two attractions are in Nara, which is not a destination city. They stay in the table and are never offered.
- **No FK from `airport.country`**: Indian departure airports have no `country` row.
- `catalog_meta` (not in the diagram) stores the `rules` block from `destinations.json` and the source hash.
- The five app-state tables are not in the diagram.

## Reset

```bash
mysql -u holiday -pholiday holiday < database/seeds/demo_reset.sql   # clear packages + reservations
bash database/scripts/reset_db.sh                                    # rebuild everything (asks for root password)
```
