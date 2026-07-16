-- =============================================================================
-- Bulk Data Loading Script (`load_data.sql`)
-- Imports raw and processed CSV/Parquet files into the relational SQL engine
-- DuckDB / SQLite / PostgreSQL compatible syntax
-- =============================================================================

-- For DuckDB:
-- INSERT INTO dim_airlines SELECT * FROM read_csv_auto('data/raw/airlines/airlines.csv');
-- INSERT INTO dim_airports SELECT * FROM read_csv_auto('data/raw/airports/airports.csv');
-- INSERT INTO dim_aircraft SELECT * FROM read_csv_auto('data/raw/flights/aircraft.csv');
-- INSERT INTO fact_flights SELECT * FROM read_csv_auto('data/raw/flights/flights_raw.csv');

-- For SQLite (using command line dot-commands):
.mode csv
.import data/raw/airlines/airlines.csv dim_airlines
.import data/raw/airports/airports.csv dim_airports
.import data/raw/flights/aircraft.csv dim_aircraft
.import data/raw/flights/flights_raw.csv fact_flights
