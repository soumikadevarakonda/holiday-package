-- App state: one row per built package (M2). Survives page refresh and backend restart.
-- ORM model: backend/app/models/package.py (Package)

CREATE TABLE IF NOT EXISTS packages (
    package_id         VARCHAR(64)   NOT NULL,
    trip_id            VARCHAR(64)   NULL,
    status             VARCHAR(32)   NOT NULL DEFAULT 'PLANNED',
    current_version_no INT           NOT NULL DEFAULT 1,
    total_price        DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    city_plans         JSON          NULL,            -- G3: ranked city plans from the build
    created_at         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (package_id),
    KEY idx_packages_trip_id (trip_id),
    KEY idx_packages_status (status),
    CONSTRAINT fk_packages_trip FOREIGN KEY (trip_id) REFERENCES trips (trip_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_packages_status CHECK (status IN ('DRAFT', 'PLANNED', 'BOOKED', 'CANCELLED', 'OVER_BUDGET')),
    CONSTRAINT chk_packages_version_no CHECK (current_version_no >= 1),
    CONSTRAINT chk_packages_total_price CHECK (total_price >= 0.00)
);
