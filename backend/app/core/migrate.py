"""Apply database/schema/*.sql in file-name order.

Every file uses CREATE TABLE IF NOT EXISTS, so running this again is safe.
Run by hand:  python -m app.core.migrate
"""

import logging
import re
from pathlib import Path

from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import get_engine

log = logging.getLogger(__name__)


def _statements(sql: str) -> list[str]:
    sql = re.sub(r"--[^\n]*", "", sql)  # strip line comments (schema files use no ';' inside strings)
    return [s.strip() for s in sql.split(";") if s.strip()]


def apply_schema(schema_dir: Path | None = None) -> list[str]:
    schema_dir = schema_dir or get_settings().schema_dir
    files = sorted(schema_dir.glob("*.sql"))
    with get_engine().begin() as conn:
        for f in files:
            for stmt in _statements(f.read_text(encoding="utf-8")):
                conn.execute(text(stmt))
    log.info("Schema applied: %s", ", ".join(f.name for f in files))
    return [f.name for f in files]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Applied:", ", ".join(apply_schema()))
