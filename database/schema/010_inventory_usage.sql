-- App state (S2): seats and rooms consumed by confirmed bookings.
-- Effective seats_left / rooms_left = catalog value - SUM(qty). Catalog tables are never updated.

CREATE TABLE IF NOT EXISTS inventory_usage (
    id         BIGINT      NOT NULL AUTO_INCREMENT,
    reference  CHAR(10)    NOT NULL,
    item_type  ENUM('FLIGHT','ROOM') NOT NULL,
    item_id    VARCHAR(24) NOT NULL,            -- flight_id or room_id
    stay_date  DATE        NULL,                -- the night, for ROOM rows
    qty        INT         NOT NULL,
    PRIMARY KEY (id),
    KEY ix_usage_item (item_type, item_id, stay_date),
    CONSTRAINT fk_usage_reservation FOREIGN KEY (reference) REFERENCES reservations (reference)
);
