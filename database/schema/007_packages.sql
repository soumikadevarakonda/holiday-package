-- App state: one row per built package (M2). Survives page refresh and backend restart.

CREATE TABLE IF NOT EXISTS packages (
    id              CHAR(36)     NOT NULL,      -- UUID
    request_id      BIGINT       NOT NULL,
    status          ENUM('DRAFT','BOOKED') NOT NULL DEFAULT 'DRAFT',
    current_version INT          NOT NULL DEFAULT 1,
    total_inr       INT          NOT NULL,
    city_plan       JSON         NOT NULL,      -- [{"city": "Tokyo", "nights": 3}, ...]
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_pkg_request FOREIGN KEY (request_id) REFERENCES trip_requests (id)
);
