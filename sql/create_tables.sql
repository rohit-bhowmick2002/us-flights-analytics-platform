-- =============================================================================
-- Table Creation Script (`create_tables.sql`)
-- Executes standard schema DDL and initializes lookup tables
-- =============================================================================

-- Execute master schema creation
-- (Run this file in your SQL engine of choice: sqlite3 aviation.db < create_tables.sql)

DROP TABLE IF EXISTS fact_flights;
DROP TABLE IF EXISTS dim_weather_hourly;
DROP TABLE IF EXISTS dim_fuel_prices;
DROP TABLE IF EXISTS dim_calendar;
DROP TABLE IF EXISTS dim_aircraft;
DROP TABLE IF EXISTS dim_airports;
DROP TABLE IF EXISTS dim_airlines;

-- Include schema definition
.read sql/schema.sql
