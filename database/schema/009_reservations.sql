-- App state: confirmed bookings (M7). GET /api/reservations/{ref} reads the frozen package_snapshot.
-- ORM model: backend/app/models/reservation.py (Reservation)

CREATE TABLE IF NOT EXISTS reservations (
    reservation_id   VARCHAR(64)   NOT NULL,
    trip_id          VARCHAR(64)   NULL,
    package_id       VARCHAR(64)   NULL,
    reference        VARCHAR(10)   NOT NULL,          -- 10 digits, no leading zero, stored as text
    status           VARCHAR(32)   NOT NULL DEFAULT 'CONFIRMED',
    total_price      DECIMAL(12,2) NOT NULL,
    package_snapshot JSON          NULL,              -- trip format, items BOOKED with booking.reference
    created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (reservation_id),
    UNIQUE KEY uq_reservations_reference (reference),
    KEY idx_reservations_trip_id (trip_id),
    KEY idx_reservations_status (status),
    CONSTRAINT fk_reservations_trip FOREIGN KEY (trip_id) REFERENCES trips (trip_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_reservations_package FOREIGN KEY (package_id) REFERENCES packages (package_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_reservations_reference_len CHECK (CHAR_LENGTH(reference) = 10),
    CONSTRAINT chk_reservations_total_price CHECK (total_price >= 0.00)
);
