-- Catalog: attractions (ER: ATTRACTION). Source: data/catalog/attractions.json.
-- No FK from `city` to destination_city: 2 attractions are in Nara, which is not a destination city
-- (no hotels). They are kept as data and never offered by the builder.

CREATE TABLE IF NOT EXISTS attraction (
    attraction_id    VARCHAR(16)   NOT NULL,
    name             VARCHAR(128)  NOT NULL,
    name_ja          VARCHAR(128)  NULL,
    city             VARCHAR(64)   NOT NULL,
    category         VARCHAR(32)   NOT NULL,
    lat              DECIMAL(9,6)  NULL,
    lng              DECIMAL(9,6)  NULL,
    open_days        JSON          NOT NULL,    -- ["MON", ..., "SUN"]
    open_from        CHAR(5)       NOT NULL,
    open_until       CHAR(5)       NOT NULL,    -- "24:00" = end of day
    closed_dates     JSON          NOT NULL,    -- ["2027-04-12", ...]; [] when none
    aliases          JSON          NOT NULL,
    visit_minutes    INT           NOT NULL,
    child_friendly   BOOLEAN       NOT NULL,
    `accessible`     BOOLEAN       NOT NULL,    -- ACCESSIBLE is a reserved word in MySQL: always quote it
    price_per_person INT           NOT NULL,    -- whole INR; 0 = free
    child_price      INT           NULL,        -- NULL = children pay price_per_person; 0 = free for children
    image            VARCHAR(255)  NULL,
    PRIMARY KEY (attraction_id),
    KEY ix_attraction_city (city)
);
