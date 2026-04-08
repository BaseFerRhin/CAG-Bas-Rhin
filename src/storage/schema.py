"""DuckDB schema creation for CAG 67/1 data."""

from __future__ import annotations

from pathlib import Path

import duckdb

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS communes (
    commune_id    VARCHAR PRIMARY KEY,
    commune_name  VARCHAR NOT NULL,
    page_start    INTEGER,
    page_end      INTEGER,
    latitude      DOUBLE,
    longitude     DOUBLE,
    x_l93         DOUBLE,
    y_l93         DOUBLE
);

CREATE TABLE IF NOT EXISTS notices (
    notice_id         VARCHAR PRIMARY KEY,
    commune_id        VARCHAR NOT NULL,
    sous_notice_code  VARCHAR,
    lieu_dit          VARCHAR,
    type_site         VARCHAR,
    raw_text          VARCHAR,
    full_text         VARCHAR,
    page_number       INTEGER,
    has_iron_age      BOOLEAN DEFAULT false
);

CREATE TABLE IF NOT EXISTS periodes (
    notice_id     VARCHAR NOT NULL,
    periode       VARCHAR NOT NULL,
    is_iron_age   BOOLEAN DEFAULT false
);

CREATE TABLE IF NOT EXISTS vestiges (
    notice_id     VARCHAR NOT NULL,
    vestige       VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS bibliographie (
    notice_id     VARCHAR NOT NULL,
    reference     VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS figures (
    notice_id     VARCHAR NOT NULL,
    figure_ref    VARCHAR NOT NULL,
    page_number   INTEGER
);

CREATE OR REPLACE VIEW v_fer_notices AS
SELECT n.*, c.commune_name AS commune, c.latitude, c.longitude
FROM notices n JOIN communes c ON n.commune_id = c.commune_id
WHERE n.has_iron_age = true;

CREATE OR REPLACE VIEW v_stats_by_commune AS
SELECT c.commune_id, c.commune_name, c.latitude, c.longitude,
       COUNT(*) AS total_notices,
       COUNT(*) FILTER (WHERE n.has_iron_age) AS fer_notices,
       COUNT(DISTINCT n.type_site) AS type_count
FROM communes c LEFT JOIN notices n ON c.commune_id = n.commune_id
GROUP BY c.commune_id, c.commune_name, c.latitude, c.longitude;

CREATE OR REPLACE VIEW v_stats_by_type AS
SELECT type_site, COUNT(*) AS count,
       COUNT(*) FILTER (WHERE has_iron_age) AS fer_count
FROM notices GROUP BY type_site ORDER BY count DESC;

CREATE OR REPLACE VIEW v_stats_by_periode AS
SELECT p.periode, p.is_iron_age, COUNT(DISTINCT p.notice_id) AS notice_count
FROM periodes p GROUP BY p.periode, p.is_iron_age ORDER BY notice_count DESC;
"""


def init_db(db_path: Path) -> None:
    """Create all tables and views in the DuckDB database."""
    con = duckdb.connect(str(db_path))
    con.execute(_SCHEMA_SQL)
    con.close()
