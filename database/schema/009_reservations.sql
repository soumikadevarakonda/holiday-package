-- App state: frozen snapshot at confirm (M7). GET /api/reservations/{ref} reads only this table.

CREATE TABLE IF NOT EXISTS reservations (
    reference   CHAR(10)     NOT NULL,          -- 10 digits, no leading zero, stored as text
    package_id  CHAR(36)     NOT NULL,
    version_no  INT          NOT NULL,
    snapshot    JSON         NOT NULL,          -- trip format, status BOOKED, booking.reference set
    total_inr   INT          NOT NULL,
    booked_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (reference),
    UNIQUE KEY uq_reservation_package (package_id),
    CONSTRAINT fk_res_package FOREIGN KEY (package_id) REFERENCES packages (id)
);
