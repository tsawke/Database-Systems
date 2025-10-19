-- -- ImportDatasets.sql
-- -- 0) Schema & search_path
-- CREATE SCHEMA IF NOT EXISTS openflights;
-- SET search_path = openflights, public;

-- -- 1) Tables (match OpenFlights fields; see dataset docs)
-- -- airports.dat (14 columns)
-- CREATE TABLE IF NOT EXISTS airports (
--   airport_id     INT,
--   name           TEXT,
--   city           TEXT,
--   country        TEXT,
--   iata           TEXT,
--   icao           TEXT,
--   latitude       DOUBLE PRECISION,
--   longitude      DOUBLE PRECISION,
--   altitude_ft    INT,
--   tz_offset      REAL,
--   dst            TEXT,
--   tz_database    TEXT,
--   type           TEXT,
--   source         TEXT
-- );

-- -- airlines.dat (8 columns)
-- CREATE TABLE IF NOT EXISTS airlines (
--   airline_id   INT,
--   name         TEXT,
--   alias        TEXT,
--   iata         TEXT,
--   icao         TEXT,
--   callsign     TEXT,
--   country      TEXT,
--   active       TEXT
-- );

-- -- routes.dat (9 columns)
-- CREATE TABLE IF NOT EXISTS routes (
--   airline          TEXT,
--   airline_id       INT,
--   src_airport      TEXT,
--   src_airport_id   INT,
--   dst_airport      TEXT,
--   dst_airport_id   INT,
--   codeshare        TEXT,
--   stops            INT,
--   equipment        TEXT
-- );

-- -- planes.dat (3 columns)
-- CREATE TABLE IF NOT EXISTS planes (
--   name       TEXT,
--   iata       TEXT,
--   icao       TEXT
-- );

-- -- countries.dat (3 columns)
-- CREATE TABLE IF NOT EXISTS countries (
--   name        TEXT,
--   iso_code    TEXT,
--   dafif_code  TEXT
-- );

-- -- 2) Optional: clean tables before (only after they exist)
-- TRUNCATE airports, airlines, routes, planes, countries;

-- -- 3) Load CSVs via \copy (client-side). Pass -v data_dir=... when running psql.
-- \pset pager off
-- \timing on

-- \cd '/root/Database-Systems/Project-I/data/openflights'

-- \! pwd

-- CREATE SCHEMA IF NOT EXISTS openflights;
-- SET search_path TO openflights;

-- \copy airports   FROM 'airports.dat'   WITH (FORMAT csv, DELIMITER ',', NULL '\N', HEADER false, QUOTE '"');
-- \copy airlines   FROM 'airlines.dat'   WITH (FORMAT csv, DELIMITER ',', NULL '\N', HEADER false, QUOTE '"');
-- \copy routes     FROM 'routes.dat'     WITH (FORMAT csv, DELIMITER ',', NULL '\N', HEADER false, QUOTE '"');
-- \copy planes     FROM 'planes.dat'     WITH (FORMAT csv, DELIMITER ',', NULL '\N', HEADER false, QUOTE '"');
-- \copy countries  FROM 'countries.dat'  WITH (FORMAT csv, DELIMITER ',', NULL '\N', HEADER false, QUOTE '"');

-- -- 4) Analyze for planner stats
-- ANALYZE openflights.airports;
-- ANALYZE openflights.airlines;
-- ANALYZE openflights.routes;
-- ANALYZE openflights.planes;
-- ANALYZE openflights.countries;

-- -- 5) Quick sanity checks
-- SELECT 'airports' AS t, COUNT(*) FROM airports
-- UNION ALL SELECT 'airlines', COUNT(*) FROM airlines
-- UNION ALL SELECT 'routes', COUNT(*) FROM routes
-- UNION ALL SELECT 'planes', COUNT(*) FROM planes
-- UNION ALL SELECT 'countries', COUNT(*) FROM countries;

SET search_path = clickstream, public;

CREATE SCHEMA IF NOT EXISTS clickstream;
DROP TABLE IF EXISTS clickstream.events;
CREATE TABLE clickstream.events (
  prev TEXT,
  curr TEXT,
  type TEXT,
  n    INTEGER
);

\copy clickstream.events FROM PROGRAM 'gzip -cd /root/Database-Systems/Project-I/data/clickstream/clickstream-enwiki-2025-09.tsv.gz' WITH (FORMAT csv, DELIMITER E'\t', HEADER false, QUOTE E'\b');

ANALYZE clickstream.events;

SELECT COUNT(*) AS rows_loaded FROM clickstream.events;
SELECT * FROM clickstream.events LIMIT 5;