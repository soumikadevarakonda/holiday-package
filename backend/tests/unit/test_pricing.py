"""Unit tests for pricing calculations and package totals (M5, P1)."""

from app.core.package_model import Item
from app.pricing.calculator import (
    calculate_attraction_price,
    calculate_flight_price,
    calculate_hotel_price,
    calculate_transfer_price,
)
from app.pricing.totals import compute_totals


def test_flight_pricing():
    # AV 520 BLR -> NRT: 25,200 INR per seat, 3 travelers
    assert calculate_flight_price(25200, 3) == 75600
    assert calculate_flight_price(25200, 1) == 25200


def test_hotel_pricing():
    # RM-TYO-004-B: 9,464 INR per night, 1 room, 3 nights
    assert calculate_hotel_price(9464, 1, 3) == 28392
    # 2 rooms, 4 nights
    assert calculate_hotel_price(5000, 2, 4) == 40000


def test_transfer_per_vehicle_rounding():
    # 4-passenger taxi at 13,440 INR
    # 3 travelers -> 1 vehicle
    assert calculate_transfer_price("PER_VEHICLE", 13440, None, 4, adults=2, children=1) == 13440
    # 4 travelers -> 1 vehicle
    assert calculate_transfer_price("PER_VEHICLE", 13440, None, 4, adults=2, children=2) == 13440
    # 5 travelers -> 2 vehicles
    assert calculate_transfer_price("PER_VEHICLE", 13440, None, 4, adults=3, children=2) == 26880
    # 8 travelers -> 2 vehicles
    assert calculate_transfer_price("PER_VEHICLE", 13440, None, 4, adults=4, children=4) == 26880
    # 9 travelers -> 3 vehicles
    assert calculate_transfer_price("PER_VEHICLE", 13440, None, 4, adults=5, children=4) == 40320


def test_transfer_per_person():
    # Bus with child discount: price 1,680, child 1,120
    # 2 adults + 1 child: 2 * 1680 + 1 * 1120 = 3360 + 1120 = 4480
    assert calculate_transfer_price("PER_PERSON", 1680, 1120, 99, adults=2, children=1) == 4480

    # Transfer with child_price None: child pays adult price
    # 2 adults + 1 child: 3 * 2000 = 6000
    assert calculate_transfer_price("PER_PERSON", 2000, None, 99, adults=2, children=1) == 6000

    # Transfer with child_price 0: child travels free!
    # 2 adults + 2 children: 2 * 1000 + 0 = 2000
    assert calculate_transfer_price("PER_PERSON", 1000, 0, 99, adults=2, children=2) == 2000


def test_attraction_pricing():
    # Paid attraction with child price: adults 280, child 112
    # 2 adults + 1 child: 2 * 280 + 112 = 672
    assert calculate_attraction_price(280, 112, adults=2, children=1) == 672

    # Attraction where child_price is 0 (free for children! e.g. ATT-OSA-003)
    # 2 adults + 1 child: 2 * 300 + 0 = 600
    assert calculate_attraction_price(300, 0, adults=2, children=1) == 600

    # Attraction with no child price (child pays adult price)
    # 2 adults + 1 child: 3 * 500 = 1500
    assert calculate_attraction_price(500, None, adults=2, children=1) == 1500

    # Free attraction (price 0)
    assert calculate_attraction_price(0, None, adults=2, children=1) == 0


def test_compute_totals():
    items = [
        Item(
            item_id="1",
            type="flight",
            name="Flight 1",
            city="Tokyo",
            catalog_id="FL-1",
            start="2027-04-10T10:00",
            end=None,
            quantity=3,
            price_inr=75000,
        ),
        Item(
            item_id="2",
            type="hotel",
            name="Hotel 1",
            city="Tokyo",
            catalog_id="HTL-1",
            start="2027-04-10",
            end="2027-04-13",
            quantity=1,
            price_inr=30000,
        ),
        Item(
            item_id="3",
            type="transfer",
            name="Bus",
            city="Tokyo",
            catalog_id="TR-1",
            start="2027-04-10T12:00",
            end=None,
            quantity=3,
            price_inr=5000,
        ),
        Item(
            item_id="4",
            type="attraction",
            name="Attraction 1",
            city="Tokyo",
            catalog_id="ATT-1",
            start="2027-04-11T10:00",
            end=None,
            quantity=3,
            price_inr=1500,
        ),
    ]

    totals = compute_totals(items, budget_inr=150000)
    assert totals.total_inr == 75000 + 30000 + 5000 + 1500  # 111,500
    assert totals.budget_inr == 150000
    assert totals.left_inr == 150000 - 111500  # 38,500
    assert totals.over_budget is False
    assert totals.by_type["flight"] == 75000
    assert totals.by_type["hotel"] == 30000
    assert totals.by_type["transfer"] == 5000
    assert totals.by_type["attraction"] == 1500

    over_totals = compute_totals(items, budget_inr=100000)
    assert over_totals.left_inr == -11500
    assert over_totals.over_budget is True
