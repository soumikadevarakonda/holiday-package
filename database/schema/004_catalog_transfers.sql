-- Catalog: transfers (ER: TRANSFER + subtypes AIRPORT_TRANSFER, CITY_TRANSFER, INTERCITY_TRANSFER;
-- INTERCITY_LINK, LINK_TRANSFER). Source: data/catalog/transfers.json, destinations.json (links).
--
-- Every transfer has one row in `transfer` and exactly one row in one subtype table:
--   AIRPORT_TAXI / AIRPORT_BUS / AIRPORT_VAN  -> airport_transfer
--   CITY_TAXI / CITY_BUS                      -> city_transfer
--   TRAIN / INTERCITY_BUS / INTERCITY_TAXI    -> intercity_transfer

CREATE TABLE IF NOT EXISTS transfer (
    transfer_id      VARCHAR(24)  NOT NULL,
    type             VARCHAR(24)  NOT NULL,
    name             VARCHAR(128) NOT NULL,
    from_point       VARCHAR(128) NOT NULL,
    to_point         VARCHAR(128) NOT NULL,
    max_passengers   INT          NOT NULL,
    service_from     CHAR(5)      NOT NULL,     -- "HH:MM"
    service_until    CHAR(5)      NOT NULL,     -- "HH:MM", "24:00" = end of day; may be < service_from (past midnight)
    duration_minutes INT          NOT NULL,
    pricing          ENUM('PER_PERSON','PER_VEHICLE') NOT NULL,
    price            INT          NOT NULL,     -- whole INR
    child_price      INT          NULL,         -- NULL = children pay `price`; 0 is a real price
    PRIMARY KEY (transfer_id)
);

CREATE TABLE IF NOT EXISTS airport_transfer (
    transfer_id  VARCHAR(24) NOT NULL,
    airport_code CHAR(3)     NOT NULL,
    city         VARCHAR(64) NOT NULL,
    area         VARCHAR(64) NULL,              -- NULL = serves the whole city
    PRIMARY KEY (transfer_id),
    KEY ix_at_lookup (airport_code, city, area),
    CONSTRAINT fk_at_transfer FOREIGN KEY (transfer_id)  REFERENCES transfer (transfer_id),
    CONSTRAINT fk_at_airport  FOREIGN KEY (airport_code) REFERENCES airport (code),
    CONSTRAINT fk_at_city     FOREIGN KEY (city)         REFERENCES destination_city (name)
);

CREATE TABLE IF NOT EXISTS city_transfer (
    transfer_id VARCHAR(24) NOT NULL,
    city        VARCHAR(64) NOT NULL,
    PRIMARY KEY (transfer_id),
    KEY ix_ct_city (city),
    CONSTRAINT fk_ct_transfer FOREIGN KEY (transfer_id) REFERENCES transfer (transfer_id),
    CONSTRAINT fk_ct_city     FOREIGN KEY (city)        REFERENCES destination_city (name)
);

CREATE TABLE IF NOT EXISTS intercity_transfer (
    transfer_id       VARCHAR(24) NOT NULL,
    from_city         VARCHAR(64) NOT NULL,
    to_city           VARCHAR(64) NOT NULL,
    frequency_minutes INT         NULL,         -- departures on service_from + n * frequency (trains, buses)
    door_to_door      BOOLEAN     NULL,
    PRIMARY KEY (transfer_id),
    KEY ix_it_route (from_city, to_city),
    CONSTRAINT fk_it_transfer FOREIGN KEY (transfer_id) REFERENCES transfer (transfer_id),
    CONSTRAINT fk_it_from     FOREIGN KEY (from_city)   REFERENCES destination_city (name),
    CONSTRAINT fk_it_to       FOREIGN KEY (to_city)     REFERENCES destination_city (name)
);

-- destinations.json countries[].links: which city pairs are connected.
CREATE TABLE IF NOT EXISTS intercity_link (
    country_code CHAR(2)     NOT NULL,
    from_city    VARCHAR(64) NOT NULL,
    to_city      VARCHAR(64) NOT NULL,
    PRIMARY KEY (country_code, from_city, to_city),
    CONSTRAINT fk_link_from FOREIGN KEY (country_code, from_city) REFERENCES destination_city (country_code, name),
    CONSTRAINT fk_link_to   FOREIGN KEY (country_code, to_city)   REFERENCES destination_city (country_code, name)
);

-- destinations.json links[].transfer_ids: the transfers allowed on a link (rule CT1).
CREATE TABLE IF NOT EXISTS link_transfer (
    country_code CHAR(2)     NOT NULL,
    from_city    VARCHAR(64) NOT NULL,
    to_city      VARCHAR(64) NOT NULL,
    transfer_id  VARCHAR(24) NOT NULL,
    PRIMARY KEY (country_code, from_city, to_city, transfer_id),
    CONSTRAINT fk_lt_link     FOREIGN KEY (country_code, from_city, to_city)
        REFERENCES intercity_link (country_code, from_city, to_city),
    CONSTRAINT fk_lt_transfer FOREIGN KEY (transfer_id) REFERENCES transfer (transfer_id)
);
