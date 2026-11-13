-- App state: the validated request as entered (M1). ORM model: backend/app/models/trip.py

CREATE TABLE IF NOT EXISTS trips (
    trip_id             VARCHAR(64)   NOT NULL,
    departure_city      VARCHAR(100)  NOT NULL,
    destination_country VARCHAR(100)  NOT NULL,
    start_date          DATE          NOT NULL,
    nights              INT           NOT NULL,
    adults              INT           NOT NULL,
    children            INT           NOT NULL DEFAULT 0,
    child_ages          JSON          NULL,
    budget              DECIMAL(12,2) NOT NULL,
    traveler_name       VARCHAR(100)  NOT NULL DEFAULT 'Traveler',
    status              VARCHAR(32)   NOT NULL DEFAULT 'DRAFT',
    created_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (trip_id),
    KEY idx_trips_status (status),
    KEY idx_trips_start_date (start_date),
    CONSTRAINT chk_trips_nights   CHECK (nights >= 1 AND nights <= 30),
    CONSTRAINT chk_trips_adults   CHECK (adults >= 1),
    CONSTRAINT chk_trips_children CHECK (children >= 0),
    CONSTRAINT chk_trips_budget   CHECK (budget >= 0.00)
);
