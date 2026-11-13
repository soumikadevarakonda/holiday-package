-- App state: the validated request as entered (M1).

CREATE TABLE IF NOT EXISTS trip_requests (
    id             BIGINT        NOT NULL AUTO_INCREMENT,
    departure_city VARCHAR(64)   NOT NULL,
    country        VARCHAR(64)   NOT NULL,
    start_date     DATE          NOT NULL,
    nights         TINYINT       NOT NULL,
    adults         TINYINT       NOT NULL,
    children_ages  JSON          NOT NULL,
    budget_inr     INT           NOT NULL,
    created_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);
