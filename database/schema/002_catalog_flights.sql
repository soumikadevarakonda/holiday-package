-- Catalog: flights (ER: FLIGHT). Source: data/catalog/flights.json.
-- Times are LOCAL times of each airport (no offset). Never subtract them across zones: use duration_minutes.

CREATE TABLE IF NOT EXISTS flight (
    flight_id        VARCHAR(16)  NOT NULL,
    airline          VARCHAR(64)  NOT NULL,
    flight_number    VARCHAR(16)  NOT NULL,
    from_airport     CHAR(3)      NOT NULL,
    to_airport       CHAR(3)      NOT NULL,
    departure_local  DATETIME     NOT NULL,
    arrival_local    DATETIME     NOT NULL,
    stops            TINYINT      NOT NULL,
    duration_minutes INT          NOT NULL,
    price_per_seat   INT          NOT NULL,     -- whole INR
    seats_left       INT          NOT NULL,     -- catalog value; bookings are tracked in inventory_usage
    cabin            VARCHAR(16)  NOT NULL,
    PRIMARY KEY (flight_id),
    KEY ix_flight_from_dep (from_airport, departure_local),
    KEY ix_flight_to_arr   (to_airport, arrival_local),
    CONSTRAINT fk_flight_from FOREIGN KEY (from_airport) REFERENCES airport (code),
    CONSTRAINT fk_flight_to   FOREIGN KEY (to_airport)   REFERENCES airport (code)
);
