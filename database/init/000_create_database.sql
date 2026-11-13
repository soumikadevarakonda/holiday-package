-- Run once as the MySQL root user.
-- Docker runs this automatically on the first `docker compose up` (mounted into /docker-entrypoint-initdb.d).
-- Without Docker:  mysql -u root -p < database/init/000_create_database.sql
-- Dev-only credentials: change them for anything shared.

CREATE DATABASE IF NOT EXISTS holiday CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE USER IF NOT EXISTS 'holiday'@'%' IDENTIFIED BY 'holiday';
CREATE USER IF NOT EXISTS 'holiday'@'localhost' IDENTIFIED BY 'holiday';

GRANT ALL PRIVILEGES ON holiday.* TO 'holiday'@'%';
GRANT ALL PRIVILEGES ON holiday.* TO 'holiday'@'localhost';
FLUSH PRIVILEGES;
