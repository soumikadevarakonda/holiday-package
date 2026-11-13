-- App state: every accepted change is a new version (M6). Gives undo, audit trail, optimistic locking.
-- ORM model: backend/app/models/package.py (PackageVersion)

CREATE TABLE IF NOT EXISTS package_versions (
    version_id     VARCHAR(64)  NOT NULL,
    package_id     VARCHAR(64)  NOT NULL,
    version_no     INT          NOT NULL,
    snapshot       JSON         NOT NULL,             -- package in the shared trip format
    change_summary VARCHAR(255) NULL,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (version_id),
    UNIQUE KEY uq_package_version_no (package_id, version_no),
    KEY idx_package_versions_pkg_id (package_id),
    CONSTRAINT fk_versions_package FOREIGN KEY (package_id) REFERENCES packages (package_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_package_version_num CHECK (version_no >= 1)
);
