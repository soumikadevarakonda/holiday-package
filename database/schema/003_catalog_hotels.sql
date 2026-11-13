-- Catalog: hotels, room types, availability (ER: HOTEL, ROOM, ROOM_AVAILABILITY).
-- Source: data/catalog/hotels.json, rooms.json, availability.json.

CREATE TABLE IF NOT EXISTS hotel (
    hotel_id        VARCHAR(16)   NOT NULL,
    name            VARCHAR(128)  NOT NULL,
    aliases         JSON          NOT NULL,
    city            VARCHAR(64)   NOT NULL,
    area            VARCHAR(64)   NOT NULL,
    lat             DECIMAL(9,6)  NULL,
    lng             DECIMAL(9,6)  NULL,
    stars           TINYINT       NOT NULL,     -- G4 "best rated" uses stars
    rating          DECIMAL(3,1)  NOT NULL,     -- guest rating, display only
    check_in_from   CHAR(5)       NOT NULL,     -- display only
    check_out_until CHAR(5)       NOT NULL,     -- display only
    family_friendly BOOLEAN       NOT NULL,
    image           VARCHAR(255)  NULL,         -- relative to data/, served at /images
    PRIMARY KEY (hotel_id),
    KEY ix_hotel_city_area (city, area),
    CONSTRAINT fk_hotel_city FOREIGN KEY (city) REFERENCES destination_city (name)
);

CREATE TABLE IF NOT EXISTS room (
    room_id         VARCHAR(24)  NOT NULL,
    hotel_id        VARCHAR(16)  NOT NULL,
    room_type       VARCHAR(24)  NOT NULL,      -- TWIN, DOUBLE, SINGLE, TRIPLE, FAMILY, FAMILY_SUITE
    name            VARCHAR(64)  NOT NULL,
    max_adults      TINYINT      NOT NULL,
    max_children    TINYINT      NOT NULL,
    price_per_night INT          NOT NULL,      -- whole INR, per room
    refundable      BOOLEAN      NOT NULL,
    PRIMARY KEY (room_id),
    KEY ix_room_hotel (hotel_id),
    CONSTRAINT fk_room_hotel FOREIGN KEY (hotel_id) REFERENCES hotel (hotel_id)
);

CREATE TABLE IF NOT EXISTS room_availability (
    room_id     VARCHAR(24) NOT NULL,
    date        DATE        NOT NULL,           -- the night (check-in date of that night)
    rooms_left  INT         NOT NULL,           -- 0 = sold out that night
    PRIMARY KEY (room_id, date),
    CONSTRAINT fk_avail_room FOREIGN KEY (room_id) REFERENCES room (room_id)
);
