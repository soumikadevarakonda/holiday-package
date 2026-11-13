"""
Comprehensive test script for Build My Holiday database and catalogue layer.
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import (
    Base,
    Catalog,
    CatalogIndexes,
    CatalogLoader,
    CatalogValidator,
    Reservation,
    ReservationItem,
    ReservationRepository,
    Trip,
    TripCity,
    TripItem,
    TripRepository,
    get_catalog,
    validate_catalog,
)


def run_tests() -> None:
    print("=" * 60)
    print("RUNNING BUILD MY HOLIDAY DATABASE LAYER TESTS")
    print("=" * 60)

    # --------------------------------------------------------------------------
    # 1. Catalogue Loader & Indexes
    # --------------------------------------------------------------------------
    print("\n[1/4] Testing Catalogue Loader & In-Memory Indexes...")
    catalog = get_catalog()
    stats = catalog.stats()
    print("Catalogue record counts:", stats)

    assert stats["airports"] == 10, f"Expected 10 airports, got {stats['airports']}"
    assert stats["flights"] == 469, f"Expected 469 flights, got {stats['flights']}"
    assert stats["hotels"] == 49, f"Expected 49 hotels, got {stats['hotels']}"
    assert stats["rooms"] == 125, f"Expected 125 rooms, got {stats['rooms']}"
    assert stats["availability"] == 2500, f"Expected 2500 availability records, got {stats['availability']}"
    assert stats["transfers"] == 66, f"Expected 66 transfers, got {stats['transfers']}"
    assert stats["attractions"] == 56, f"Expected 56 attractions, got {stats['attractions']}"

    indexes = catalog.indexes

    # Airport lookup
    blr = indexes.get_airport("BLR")
    assert blr is not None and blr["city"] == "Bengaluru"
    kix = indexes.get_airport("KIX")
    assert kix is not None and "Kyoto" in kix.get("serves_cities", [])

    # Departure city lookups
    assert indexes.get_departure_airport("Bengaluru") == "BLR"
    assert indexes.get_departure_airport("Delhi") == "DEL"
    assert indexes.get_departure_city("BLR") == "Bengaluru"

    # Destination city airports
    kyoto_airports = indexes.get_airports_for_destination_city("Kyoto")
    assert "KIX" in kyoto_airports
    tokyo_airports = indexes.get_airports_for_destination_city("Tokyo")
    assert "NRT" in tokyo_airports and "HND" in tokyo_airports

    # Flights lookups
    blr_to_kix = indexes.get_flights("BLR", "KIX")
    assert len(blr_to_kix) > 0
    # Flight on specific arrival date
    flights_apr1 = indexes.get_flights_by_arrival_date("BLR", "KIX", "2027-04-01")
    assert len(flights_apr1) > 0

    # Hotels & rooms lookups
    tokyo_hotels = indexes.get_hotels_by_city("Tokyo")
    assert len(tokyo_hotels) == 13
    first_hotel = tokyo_hotels[0]
    hotel_rooms = indexes.get_rooms_by_hotel(first_hotel["hotel_id"])
    assert len(hotel_rooms) >= 1
    first_room = hotel_rooms[0]

    # Availability lookup
    avail_count = indexes.get_rooms_left(first_room["room_id"], "2027-04-01")
    assert avail_count is not None
    assert indexes.check_room_availability(first_room["room_id"], ["2027-04-01", "2027-04-02"], 1)

    # Intercity Transfers lookup (non-bidirectional check)
    transfers_tyo_kyo = indexes.get_transfers_by_route("Tokyo", "Kyoto")
    assert len(transfers_tyo_kyo) >= 1
    transfers_kyo_tyo = indexes.get_transfers_by_route("Kyoto", "Tokyo")
    assert len(transfers_kyo_tyo) >= 1

    # Airport Transfers lookup
    nrt_transfers = indexes.get_airport_transfers("NRT", city="Tokyo")
    assert len(nrt_transfers) >= 1

    # Attractions lookup
    attractions_kyoto = indexes.get_attractions_by_city("Kyoto")
    assert len(attractions_kyoto) > 0

    print("Catalogue Loader & Indexes: PASSED")

    # --------------------------------------------------------------------------
    # 2. Catalogue Read-Only Integrity
    # --------------------------------------------------------------------------
    print("\n[2/4] Testing Catalogue Read-Only Immutability...")
    airports_copy = catalog.airports
    airports_copy.clear()
    assert len(catalog.airports) == 10, "Original catalog airports were mutated!"
    print("Catalogue Read-Only Immutability: PASSED")

    # --------------------------------------------------------------------------
    # 3. Catalogue Validator
    # --------------------------------------------------------------------------
    print("\n[3/4] Running Catalogue Validator on Real Catalog...")
    report = validate_catalog()
    if not report.is_valid:
        print(report.format_report())
        raise AssertionError("Catalogue validation failed!")
    print(f"Validation Report Status: {report.is_valid} (0 errors, 0 warnings)")
    print("Catalogue Validator: PASSED")

    # --------------------------------------------------------------------------
    # 4. SQLAlchemy 2.0 Models & Repositories
    # --------------------------------------------------------------------------
    print("\n[4/4] Testing SQLAlchemy 2.0 Models & Repositories with In-Memory DB...")
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as session:
        trip_repo = TripRepository(session)
        res_repo = ReservationRepository(session)

        # Create a sample Trip (Menon family scenario)
        trip = Trip(
            trip_id="trip-menon-001",
            departure_city="Bengaluru",
            destination_country="Japan",
            start_date=date(2027, 4, 10),
            nights=6,
            adults=2,
            children=1,
            child_ages=[6],
            budget=Decimal("350000.00"),
            status="PLANNED",
        )
        trip.cities.append(TripCity(city_name="Tokyo", nights=3, sequence_order=1))
        trip.cities.append(TripCity(city_name="Kyoto", nights=3, sequence_order=2))

        trip.items.append(
            TripItem(
                item_id="item-fl-outbound",
                item_type="flight",
                catalogue_id="FL-401",
                city_name="Tokyo",
                start_datetime=datetime(2027, 4, 9, 23, 50),
                end_datetime=datetime(2027, 4, 10, 10, 30),
                price=Decimal("75600.00"),
                quantity=3,
                item_details={"airline": "AirVeda"},
            )
        )
        trip.items.append(
            TripItem(
                item_id="item-htl-tokyo",
                item_type="hotel",
                catalogue_id="HTL-TYO-001",
                city_name="Tokyo",
                start_datetime=datetime(2027, 4, 10, 15, 0),
                end_datetime=datetime(2027, 4, 13, 11, 0),
                price=Decimal("26040.00"),
                quantity=1,
                item_details={"room_id": "RM-TYO-001-B"},
            )
        )

        trip_repo.create_trip(trip)
        session.commit()

    with session_factory() as session:
        trip_repo = TripRepository(session)
        res_repo = ReservationRepository(session)

        # Retrieve trip
        retrieved_trip = trip_repo.get_trip_by_id("trip-menon-001")
        assert retrieved_trip is not None
        assert retrieved_trip.departure_city == "Bengaluru"
        assert len(retrieved_trip.cities) == 2
        assert len(retrieved_trip.items) == 2
        assert retrieved_trip.total_price == Decimal("101640.00")

        # Test export format
        export_data = retrieved_trip.to_export_format(traveler_name="Menon family")
        assert export_data["trip_id"] == "trip-menon-001"
        assert export_data["traveler"]["adults"] == 2
        assert export_data["traveler"]["children"] == 1
        assert export_data["budget_inr"] == 350000
        assert export_data["total_inr"] == 101640
        assert len(export_data["items"]) == 2

        # Create Reservation from Trip
        reservation = res_repo.create_reservation_from_trip(retrieved_trip)
        session.commit()

        res_ref = reservation.reference
        assert len(res_ref) == 10, f"Expected 10-digit reference, got '{res_ref}'"
        assert res_ref.isdigit(), f"Reference must be numeric, got '{res_ref}'"
        print(f"Created reservation with 10-digit reference: {res_ref}")

    with session_factory() as session:
        res_repo = ReservationRepository(session)
        trip_repo = TripRepository(session)

        # Retrieve reservation by 10-digit reference
        found_res = res_repo.get_by_reference(res_ref)
        assert found_res is not None
        assert found_res.trip_id == "trip-menon-001"
        assert found_res.status == "CONFIRMED"
        assert len(found_res.items) == 2
        assert found_res.total_price == Decimal("101640.00")

        # Verify snapshot data preserved
        item_snapshot = found_res.items[0].item_snapshot
        assert item_snapshot["catalogue_id"] == "FL-401"
        assert item_snapshot["price"] == 75600.0

        # Non-existent reference returns None
        assert res_repo.get_by_reference("9999999999") is None

        # Verify trip status transitioned to BOOKED
        persisted_trip = trip_repo.get_trip_by_id("trip-menon-001")
        assert persisted_trip.status == "BOOKED"

        # Update and delete trip test
        persisted_trip.budget = Decimal("400000.00")
        trip_repo.save_trip(persisted_trip)
        session.commit()

        updated_trip = trip_repo.get_trip_by_id("trip-menon-001")
        assert updated_trip.budget == Decimal("400000.00")

    print("SQLAlchemy 2.0 Models & Repositories: PASSED")

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
