-- ==============================================================================
-- Build My Holiday - Application Database Schema (MySQL 8.0+)
-- Stores user-generated trips, itinerary items, and confirmed reservations.
-- Catalogue data remains in read-only JSON files and is referenced by catalogue_id.
-- ==============================================================================

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS build_my_holiday
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE build_my_holiday;

-- ------------------------------------------------------------------------------
-- Table: trips
-- Stores high-level holiday package requests and generated package metadata.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trips (
    trip_id VARCHAR(64) NOT NULL,
    departure_city VARCHAR(100) NOT NULL,
    destination_country VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    nights INT NOT NULL,
    adults INT NOT NULL,
    children INT NOT NULL DEFAULT 0,
    child_ages JSON NULL,
    budget DECIMAL(12, 2) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'DRAFT',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (trip_id),
    CONSTRAINT chk_trips_nights CHECK (nights >= 1 AND nights <= 30),
    CONSTRAINT chk_trips_adults CHECK (adults >= 1),
    CONSTRAINT chk_trips_children CHECK (children >= 0),
    CONSTRAINT chk_trips_budget CHECK (budget >= 0.00),
    CONSTRAINT chk_trips_status CHECK (status IN ('DRAFT', 'PLANNED', 'BOOKED', 'CANCELLED', 'EXPIRED')),
    INDEX idx_trips_status (status),
    INDEX idx_trips_start_date (start_date),
    INDEX idx_trips_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- Table: trip_cities
-- Ordered multi-city itinerary segments for a trip.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trip_cities (
    trip_city_id VARCHAR(64) NOT NULL,
    trip_id VARCHAR(64) NOT NULL,
    city_name VARCHAR(100) NOT NULL,
    nights INT NOT NULL,
    sequence_order INT NOT NULL,

    PRIMARY KEY (trip_city_id),
    CONSTRAINT fk_trip_cities_trip
        FOREIGN KEY (trip_id) REFERENCES trips (trip_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT uq_trip_city_sequence
        UNIQUE (trip_id, sequence_order),
    CONSTRAINT chk_trip_cities_nights CHECK (nights >= 1),
    CONSTRAINT chk_trip_cities_seq CHECK (sequence_order >= 1),
    INDEX idx_trip_cities_trip_id (trip_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- Table: trip_items
-- Concrete travel items in the package (flights, hotels, transfers, attractions).
-- Points to read-only catalogue data via catalogue_id.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trip_items (
    item_id VARCHAR(64) NOT NULL,
    trip_id VARCHAR(64) NOT NULL,
    item_type VARCHAR(32) NOT NULL,
    catalogue_id VARCHAR(64) NOT NULL,
    city_name VARCHAR(100) NULL,
    start_datetime DATETIME NOT NULL,
    end_datetime DATETIME NULL,
    price DECIMAL(12, 2) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    item_details JSON NULL,

    PRIMARY KEY (item_id),
    CONSTRAINT fk_trip_items_trip
        FOREIGN KEY (trip_id) REFERENCES trips (trip_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_trip_items_type CHECK (item_type IN ('flight', 'hotel', 'transfer', 'attraction')),
    CONSTRAINT chk_trip_items_price CHECK (price >= 0.00),
    CONSTRAINT chk_trip_items_quantity CHECK (quantity >= 1),
    INDEX idx_trip_items_trip_id (trip_id),
    INDEX idx_trip_items_type (item_type),
    INDEX idx_trip_items_catalogue_id (catalogue_id),
    INDEX idx_trip_items_dates (start_datetime, end_datetime)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- Table: reservations
-- Confirmed bookings with a guaranteed unique 10-digit reference number.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reservations (
    reservation_id VARCHAR(64) NOT NULL,
    trip_id VARCHAR(64) NOT NULL,
    reference VARCHAR(10) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'CONFIRMED',
    total_price DECIMAL(12, 2) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (reservation_id),
    CONSTRAINT uq_reservations_reference UNIQUE (reference),
    CONSTRAINT fk_reservations_trip
        FOREIGN KEY (trip_id) REFERENCES trips (trip_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_reservations_reference_len CHECK (CHAR_LENGTH(reference) = 10 AND reference REGEXP '^[0-9]{10}$'),
    CONSTRAINT chk_reservations_status CHECK (status IN ('CONFIRMED', 'CANCELLED', 'REFUNDED')),
    CONSTRAINT chk_reservations_total_price CHECK (total_price >= 0.00),
    INDEX idx_reservations_trip_id (trip_id),
    INDEX idx_reservations_status (status),
    INDEX idx_reservations_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- Table: reservation_items
-- Frozen immutable snapshots of booked items at the exact moment of reservation.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reservation_items (
    reservation_item_id VARCHAR(64) NOT NULL,
    reservation_id VARCHAR(64) NOT NULL,
    item_type VARCHAR(32) NOT NULL,
    catalogue_id VARCHAR(64) NOT NULL,
    item_snapshot JSON NOT NULL,
    price DECIMAL(12, 2) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,

    PRIMARY KEY (reservation_item_id),
    CONSTRAINT fk_reservation_items_reservation
        FOREIGN KEY (reservation_id) REFERENCES reservations (reservation_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_res_items_price CHECK (price >= 0.00),
    CONSTRAINT chk_res_items_quantity CHECK (quantity >= 1),
    INDEX idx_res_items_reservation_id (reservation_id),
    INDEX idx_res_items_catalogue_id (catalogue_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
