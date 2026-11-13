-- DEV ONLY: clear app state before a demo. Catalog tables are kept.
-- mysql -u holiday -pholiday holiday < database/seeds/demo_reset.sql

SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE inventory_usage;
TRUNCATE TABLE reservations;
TRUNCATE TABLE package_versions;
TRUNCATE TABLE packages;
TRUNCATE TABLE trip_requests;
SET FOREIGN_KEY_CHECKS = 1;
