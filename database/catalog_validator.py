"""
Catalogue validation for Build My Holiday.

Verifies structural integrity, unique identifier constraints, and referential
integrity across all eight travel catalogue datasets as specified in DATA_DICTIONARY.md.
"""

from __future__ import annotations

import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path when executed directly
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from database.catalog_loader import (
    CATALOG_FILENAMES,
    Catalog,
    CatalogError,
    CatalogFileNotFoundError,
    CatalogLoader,
    CatalogParseError,
    get_catalog,
)


@dataclass
class ValidationReport:
    """Detailed report produced by the catalogue validator."""

    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    def add_error(self, message: str) -> None:
        """Record a validation error and mark the report invalid."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Record a non-fatal warning."""
        self.warnings.append(message)

    def format_report(self) -> str:
        """Format the report as human-readable text."""
        lines = [
            "=" * 70,
            "BUILD MY HOLIDAY - TRAVEL CATALOGUE VALIDATION REPORT",
            "=" * 70,
            f"Overall Status : {'PASSED (VALID)' if self.is_valid else 'FAILED (INVALID)'}",
            f"Total Errors   : {len(self.errors)}",
            f"Total Warnings : {len(self.warnings)}",
            "-" * 70,
            "Dataset Record Counts:",
        ]
        for key, count in self.summary.get("record_counts", {}).items():
            lines.append(f"  - {key:<24}: {count}")

        if self.errors:
            lines.append("-" * 70)
            lines.append("ERRORS:")
            for i, err in enumerate(self.errors, start=1):
                lines.append(f"  [{i}] {err}")

        if self.warnings:
            lines.append("-" * 70)
            lines.append("WARNINGS:")
            for i, warn in enumerate(self.warnings, start=1):
                lines.append(f"  [{i}] {warn}")

        lines.append("=" * 70)
        return "\n".join(lines)


class CatalogValidator:
    """
    Validates existence, JSON syntax, ID uniqueness, and referential integrity
    across all catalogue files.
    """

    def __init__(self, catalog_dir: Path | str | None = None) -> None:
        self.catalog_dir = CatalogLoader.get_catalog_dir(catalog_dir)

    def validate_files_exist_and_parseable(
        self, report: ValidationReport
    ) -> dict[str, Any] | None:
        """
        Step 1: Verify all 8 files exist and contain valid JSON.
        Returns dictionary of parsed data if all pass, or records errors into report.
        """
        data: dict[str, Any] = {}
        for fname in CATALOG_FILENAMES:
            fpath = self.catalog_dir / fname
            if not fpath.is_file():
                report.add_error(f"Missing required catalogue file: {fpath}")
                continue

            try:
                content = CatalogLoader.load_file(fpath)
                data[fname] = content
            except CatalogParseError as pe:
                report.add_error(f"JSON syntax error in {fname}: {pe.original_error}")
            except Exception as exc:
                report.add_error(f"Failed to read {fname}: {exc}")

        if len(data) != len(CATALOG_FILENAMES):
            return None
        return data

    def validate_catalog(
        self, catalog: Catalog | None = None
    ) -> ValidationReport:
        """
        Full validation run. Can validate an already loaded Catalog or load fresh files.
        """
        report = ValidationReport()

        raw_data: dict[str, Any] | None = None
        if catalog is None:
            raw_data = self.validate_files_exist_and_parseable(report)
            if raw_data is None:
                # Fatal loading error, abort deeper integrity checks
                return report

            try:
                catalog = CatalogLoader.load_all(self.catalog_dir)
            except CatalogError as exc:
                report.add_error(f"Could not build catalog object: {exc}")
                return report

        # Extract datasets
        destinations = catalog.destinations
        airports = catalog.airports
        flights = catalog.flights
        hotels = catalog.hotels
        rooms = catalog.rooms
        availability = catalog.availability
        transfers = catalog.transfers
        attractions = catalog.attractions

        # Populate summary record counts
        report.summary["record_counts"] = {
            "airports": len(airports),
            "flights": len(flights),
            "hotels": len(hotels),
            "rooms": len(rooms),
            "availability": len(availability),
            "transfers": len(transfers),
            "attractions": len(attractions),
            "destination_countries": len(destinations.get("countries", [])),
            "departure_cities": len(destinations.get("departure_cities", [])),
        }

        # ----------------------------------------------------------------------
        # 1. ID Uniqueness Checks
        # ----------------------------------------------------------------------
        # Airports: code
        airport_codes = [a.get("code") for a in airports if a.get("code")]
        dup_airports = [code for code, count in Counter(airport_codes).items() if count > 1]
        if dup_airports:
            report.add_error(f"Duplicate airport codes found: {dup_airports}")

        # Flights: flight_id
        flight_ids = [f.get("flight_id") for f in flights if f.get("flight_id")]
        dup_flights = [fid for fid, count in Counter(flight_ids).items() if count > 1]
        if dup_flights:
            report.add_error(f"Duplicate flight_id found: {dup_flights[:10]}")

        # Hotels: hotel_id
        hotel_ids = [h.get("hotel_id") for h in hotels if h.get("hotel_id")]
        dup_hotels = [hid for hid, count in Counter(hotel_ids).items() if count > 1]
        if dup_hotels:
            report.add_error(f"Duplicate hotel_id found: {dup_hotels}")

        # Rooms: room_id
        room_ids = [r.get("room_id") for r in rooms if r.get("room_id")]
        dup_rooms = [rid for rid, count in Counter(room_ids).items() if count > 1]
        if dup_rooms:
            report.add_error(f"Duplicate room_id found: {dup_rooms}")

        # Transfers: transfer_id
        transfer_ids = [t.get("transfer_id") for t in transfers if t.get("transfer_id")]
        dup_transfers = [tid for tid, count in Counter(transfer_ids).items() if count > 1]
        if dup_transfers:
            report.add_error(f"Duplicate transfer_id found: {dup_transfers}")

        # Attractions: attraction_id
        attraction_ids = [a.get("attraction_id") for a in attractions if a.get("attraction_id")]
        dup_attractions = [aid for aid, count in Counter(attraction_ids).items() if count > 1]
        if dup_attractions:
            report.add_error(f"Duplicate attraction_id found: {dup_attractions}")

        # Availability: composite (room_id, date) uniqueness
        avail_pairs = [
            (av.get("room_id"), av.get("date"))
            for av in availability
            if av.get("room_id") and av.get("date")
        ]
        dup_avail = [pair for pair, count in Counter(avail_pairs).items() if count > 1]
        if dup_avail:
            report.add_error(f"Duplicate availability (room_id, date) pairs found: {dup_avail[:10]}")

        # ----------------------------------------------------------------------
        # 2. Referential Integrity Checks
        # ----------------------------------------------------------------------
        hotel_id_set = set(hotel_ids)
        room_id_set = set(room_ids)
        airport_code_set = set(airport_codes)
        transfer_id_set = set(transfer_ids)

        # Rooms -> Hotels (hotel_id must exist in hotels.json)
        missing_hotel_refs = [
            r.get("room_id")
            for r in rooms
            if r.get("hotel_id") not in hotel_id_set
        ]
        if missing_hotel_refs:
            report.add_error(
                f"Rooms referencing non-existent hotel_id: {missing_hotel_refs[:10]}"
            )

        # Availability -> Rooms (room_id must exist in rooms.json)
        missing_room_refs = [
            av.get("room_id")
            for av in availability
            if av.get("room_id") not in room_id_set
        ]
        if missing_room_refs:
            report.add_error(
                f"Availability records referencing non-existent room_id: {set(missing_room_refs)}"
            )

        # Flights -> Airports (from and to must exist in airports.json)
        invalid_flight_from = [
            fl.get("flight_id")
            for fl in flights
            if fl.get("from") not in airport_code_set
        ]
        if invalid_flight_from:
            report.add_error(
                f"Flights referencing non-existent departure airport: {invalid_flight_from[:10]}"
            )

        invalid_flight_to = [
            fl.get("flight_id")
            for fl in flights
            if fl.get("to") not in airport_code_set
        ]
        if invalid_flight_to:
            report.add_error(
                f"Flights referencing non-existent arrival airport: {invalid_flight_to[:10]}"
            )

        # Destinations -> Transfers (transfer_ids in country links must exist in transfers.json)
        missing_link_transfers: list[str] = []
        for country in destinations.get("countries", []):
            for link in country.get("links", []):
                for tid in link.get("transfer_ids", []):
                    if tid not in transfer_id_set:
                        missing_link_transfers.append(tid)
        if missing_link_transfers:
            report.add_error(
                f"Destination links reference missing transfer_ids: {missing_link_transfers}"
            )

        # Destinations -> Airports (departure_cities airport must exist in airports.json)
        for dep in destinations.get("departure_cities", []):
            ap = dep.get("airport")
            if ap and ap not in airport_code_set:
                report.add_error(
                    f"Departure city '{dep.get('city')}' references unknown airport: {ap}"
                )

        # Destinations -> Airports (countries[].cities[].airports must exist in airports.json)
        for country in destinations.get("countries", []):
            for city in country.get("cities", []):
                for ap in city.get("airports", []):
                    if ap not in airport_code_set:
                        report.add_error(
                            f"Destination city '{city.get('name')}' references unknown airport: {ap}"
                        )

        # Transfers -> Airports (if airport is provided, must exist in airports.json)
        for t in transfers:
            ap = t.get("airport")
            if ap and ap not in airport_code_set:
                report.add_error(
                    f"Transfer '{t.get('transfer_id')}' references unknown airport: {ap}"
                )

        return report


def validate_catalog(catalog_dir: Path | str | None = None) -> ValidationReport:
    """Convenience function to run catalogue validation."""
    validator = CatalogValidator(catalog_dir)
    return validator.validate_catalog()


if __name__ == "__main__":
    report = validate_catalog()
    print(report.format_report())
    sys.exit(0 if report.is_valid else 1)
