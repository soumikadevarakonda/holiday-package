-- App state: every accepted change is a new version (M6). Gives undo, audit trail, optimistic locking.

CREATE TABLE IF NOT EXISTS package_versions (
    id          BIGINT        NOT NULL AUTO_INCREMENT,
    package_id  CHAR(36)      NOT NULL,
    version_no  INT           NOT NULL,
    body        JSON          NOT NULL,         -- package in the shared trip format
    total_inr   INT           NOT NULL,
    change_note VARCHAR(255)  NULL,
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_package_version (package_id, version_no),
    CONSTRAINT fk_ver_package FOREIGN KEY (package_id) REFERENCES packages (id)
);
