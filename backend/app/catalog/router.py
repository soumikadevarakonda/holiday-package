
from fastapi import APIRouter, HTTPException, Query

from backend.app.catalog.service import (
    load_catalog,
    get_records,
    get_summary,
    filter_records,
)

router = APIRouter(prefix="/api/catalog", tags=["Catalogue"])


@router.get("/summary")
def catalogue_summary():
    return get_summary()


@router.get("/destinations")
def destinations():
    return load_catalog()["destinations"]


@router.get("/airports")
def airports():
    return get_records("airports")


@router.get("/flights")
def flights(
    origin: str | None = None,
    destination: str | None = None,
    cabin: str | None = None,
    max_price: float | None = Query(default=None, ge=0),
):
    return filter_records(
        "flights",
        origin=origin,
        destination=destination,
        cabin=cabin,
        max_price=max_price,
    )


@router.get("/hotels")
def hotels(
    city: str | None = None,
    min_rating: float | None = Query(default=None, ge=0, le=10),
):
    return filter_records(
        "hotels",
        city=city,
        min_rating=min_rating,
    )


@router.get("/attractions")
def attractions(
    city: str | None = None,
    category: str | None = None,
):
    return filter_records(
        "attractions",
        city=city,
        category=category,
    )


@router.get("/rooms")
def rooms():
    return get_records("rooms")


@router.get("/transfers")
def transfers(city: str | None = None):
    return filter_records("transfers", city=city)


@router.get("/availability")
def availability():
    return get_records("availability")
