-- Catalog: countries, cities, airports (ER: COUNTRY, DESTINATION_CITY, AIRPORT, CITY_AIRPORT, DEPARTURE_CITY)
-- Source: data/catalog/destinations.json, airports.json. Filled by `python -m app.catalog.seed`.

CREATE TABLE IF NOT EXISTS country (
    code        CHAR(2)      NOT NULL,
    name        VARCHAR(64)  NOT NULL,
    timezone    VARCHAR(64)  NOT NULL,
    PRIMARY KEY (code)
);

CREATE TABLE IF NOT EXISTS destination_city (
    country_code CHAR(2)     NOT NULL,
    name         VARCHAR(64) NOT NULL,
    PRIMARY KEY (country_code, name),
    UNIQUE KEY uq_destination_city_name (name),  -- lets hotel / transfer tables reference the city by name
    CONSTRAINT fk_city_country FOREIGN KEY (country_code) REFERENCES country (code)
);

CREATE TABLE IF NOT EXISTS airport (
    code        CHAR(3)       NOT NULL,
    name        VARCHAR(128)  NOT NULL,
    city        VARCHAR(64)   NOT NULL,           -- the airport's own city; use city_airport to find the cities it serves
    country     CHAR(2)       NOT NULL,           -- includes IN (departure side), so no FK to country
    timezone    VARCHAR(64)   NOT NULL,
    lat         DECIMAL(9,6)  NULL,
    lng         DECIMAL(9,6)  NULL,
    PRIMARY KEY (code)
);

-- airports.serves_cities: which destination cities an airport serves (KIX -> Osaka, Kyoto).
-- ITM serves no city and the Indian airports have no serves_cities, so they have no rows here.
CREATE TABLE IF NOT EXISTS city_airport (
    country_code CHAR(2)     NOT NULL,
    city_name    VARCHAR(64) NOT NULL,
    airport_code CHAR(3)     NOT NULL,
    PRIMARY KEY (country_code, city_name, airport_code),
    KEY ix_city_airport_airport (airport_code),
    CONSTRAINT fk_ca_city    FOREIGN KEY (country_code, city_name) REFERENCES destination_city (country_code, name),
    CONSTRAINT fk_ca_airport FOREIGN KEY (airport_code) REFERENCES airport (code)
);

CREATE TABLE IF NOT EXISTS departure_city (
    city         VARCHAR(64) NOT NULL,
    airport_code CHAR(3)     NOT NULL,
    PRIMARY KEY (city, airport_code),
    CONSTRAINT fk_dep_airport FOREIGN KEY (airport_code) REFERENCES airport (code)
);

-- destinations.json `rules` block + the hash of the seeded catalog files (not in the ER diagram).
CREATE TABLE IF NOT EXISTS catalog_meta (
    meta_key    VARCHAR(64) NOT NULL,
    meta_value  JSON        NOT NULL,
    PRIMARY KEY (meta_key)
);
