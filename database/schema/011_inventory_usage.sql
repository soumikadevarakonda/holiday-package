-- App state (S2): seats and rooms consumed by confirmed bookings.
-- Effective seats / rooms left = catalog value - SUM(quantity). Catalog tables are never updated.
-- ORM model: backend/app/models/inventory.py (InventoryUsage)

CREATE TABLE IF NOT EXISTS inventory_usage (
    usage_id       VARCHAR(64) NOT NULL,
    reservation_id VARCHAR(64) NOT NULL,
    item_type      VARCHAR(32) NOT NULL,               -- 'flight' or 'room'
    catalogue_id   VARCHAR(64) NOT NULL,               -- flight_id or room_id
    allocated_date DATE        NOT NULL,               -- flight departure date / room night
    quantity       INT         NOT NULL DEFAULT 1,
    created_at     DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (usage_id),
    KEY idx_inv_usage_res_id (reservation_id),
    KEY idx_inv_usage_item_date (item_type, catalogue_id, allocated_date),
    CONSTRAINT fk_inv_usage_reservation FOREIGN KEY (reservation_id) REFERENCES reservations (reservation_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_inv_usage_type CHECK (item_type IN ('flight', 'room')),
    CONSTRAINT chk_inv_usage_quantity CHECK (quantity >= 1)
);
