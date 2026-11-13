
from database.connection import get_engine
from database.models import Base

# Import models so SQLAlchemy registers all mapped tables.
from database.models.trip import Trip
from database.models.trip_city import TripCity
from database.models.trip_item import TripItem
from database.models.reservation import Reservation


def create_tables():
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    create_tables()
