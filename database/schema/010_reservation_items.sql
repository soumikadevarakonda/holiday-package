-- App state: one row per booked item, frozen at confirm.
-- ORM model: backend/app/models/reservation.py (ReservationItem)

CREATE TABLE IF NOT EXISTS reservation_items (
    reservation_item_id VARCHAR(64)   NOT NULL,
    reservation_id      VARCHAR(64)   NOT NULL,
    item_type           VARCHAR(32)   NOT NULL,
    catalogue_id        VARCHAR(64)   NOT NULL,
    item_snapshot       JSON          NOT NULL,
    price               DECIMAL(12,2) NOT NULL,
    quantity            INT           NOT NULL DEFAULT 1,
    PRIMARY KEY (reservation_item_id),
    KEY idx_res_items_reservation_id (reservation_id),
    KEY idx_res_items_catalogue_id (catalogue_id),
    CONSTRAINT fk_res_items_reservation FOREIGN KEY (reservation_id) REFERENCES reservations (reservation_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_res_items_price CHECK (price >= 0.00),
    CONSTRAINT chk_res_items_quantity CHECK (quantity >= 1)
);
