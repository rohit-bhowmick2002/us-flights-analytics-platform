-- =============================================================================
-- Enterprise Aviation Analytics Platform — Master Schema Definition (`schema.sql`)
-- Multi-Table Star Schema supporting Pre-Flight & Post-Flight Analytics
-- Compatible with DuckDB, PostgreSQL, and SQLite
-- =============================================================================

-- 1. Dimension Table: Airlines
CREATE TABLE IF NOT EXISTS dim_airlines (
    airline_code VARCHAR(10) PRIMARY KEY,
    airline_name VARCHAR(100) NOT NULL,
    alliance VARCHAR(50),
    fleet_size INTEGER
);

-- 2. Dimension Table: Airports
CREATE TABLE IF NOT EXISTS dim_airports (
    airport_code VARCHAR(10) PRIMARY KEY,
    airport_name VARCHAR(150) NOT NULL,
    city VARCHAR(100),
    state VARCHAR(50),
    latitude DECIMAL(9, 6),
    longitude DECIMAL(9, 6),
    hub_status VARCHAR(50)
);

-- 3. Dimension Table: Aircraft Fleet Demographics
CREATE TABLE IF NOT EXISTS dim_aircraft (
    tail_number VARCHAR(20) PRIMARY KEY,
    manufacturer VARCHAR(50),
    model VARCHAR(50),
    capacity INTEGER,
    year_built INTEGER,
    engine_type VARCHAR(50)
);

-- 4. Dimension Table: Hourly Weather Observations (NOAA ASOS/METAR)
CREATE TABLE IF NOT EXISTS dim_weather_hourly (
    weather_id VARCHAR(50) PRIMARY KEY,
    airport_code VARCHAR(10) NOT NULL,
    utc_timestamp TIMESTAMP NOT NULL,
    temperature DECIMAL(5, 2),
    wind_speed DECIMAL(5, 2),
    visibility DECIMAL(5, 2),
    precipitation DECIMAL(5, 2),
    snowfall DECIMAL(5, 2),
    weather_condition VARCHAR(100),
    FOREIGN KEY (airport_code) REFERENCES dim_airports(airport_code)
);

-- 5. Dimension Table: Holiday & Calendar Reference
CREATE TABLE IF NOT EXISTS dim_calendar (
    calendar_date DATE PRIMARY KEY,
    day_of_week INTEGER,
    day_name VARCHAR(20),
    month_number INTEGER,
    month_name VARCHAR(20),
    quarter INTEGER,
    year INTEGER,
    is_weekend BOOLEAN,
    is_holiday BOOLEAN,
    holiday_name VARCHAR(100)
);

-- 6. Dimension Table: Monthly Jet Fuel Prices
CREATE TABLE IF NOT EXISTS dim_fuel_prices (
    year_month VARCHAR(7) PRIMARY KEY,
    region VARCHAR(50),
    jet_fuel_price_per_gal DECIMAL(6, 3)
);

-- 7. Fact Table: Commercial Flights (Core Operations)
CREATE TABLE IF NOT EXISTS fact_flights (
    flight_id VARCHAR(50) PRIMARY KEY,
    flight_date DATE NOT NULL,
    crs_dep_time TIMESTAMP NOT NULL,
    crs_arr_time TIMESTAMP NOT NULL,
    actual_dep_time TIMESTAMP,
    actual_arr_time TIMESTAMP,
    airline_code VARCHAR(10) NOT NULL,
    flight_number INTEGER,
    tail_number VARCHAR(20),
    origin_airport VARCHAR(10) NOT NULL,
    destination_airport VARCHAR(10) NOT NULL,
    distance_miles INTEGER,
    crs_duration_mins INTEGER,
    air_time_mins INTEGER,
    dep_delay_mins INTEGER DEFAULT 0,
    arr_delay_mins INTEGER DEFAULT 0,
    taxi_out_mins INTEGER DEFAULT 0,
    taxi_in_mins INTEGER DEFAULT 0,
    cancelled_flag INTEGER DEFAULT 0,
    cancellation_reason VARCHAR(50),
    diversion_flag INTEGER DEFAULT 0,
    delay_reason VARCHAR(50),
    carrier_delay_mins INTEGER DEFAULT 0,
    weather_delay_mins INTEGER DEFAULT 0,
    nas_delay_mins INTEGER DEFAULT 0,
    late_aircraft_delay_mins INTEGER DEFAULT 0,
    turnaround_buffer_mins INTEGER,
    FOREIGN KEY (airline_code) REFERENCES dim_airlines(airline_code),
    FOREIGN KEY (origin_airport) REFERENCES dim_airports(airport_code),
    FOREIGN KEY (destination_airport) REFERENCES dim_airports(airport_code),
    FOREIGN KEY (tail_number) REFERENCES dim_aircraft(tail_number)
);

-- Indexes for Fast Analytics
CREATE INDEX IF NOT EXISTS idx_flights_date ON fact_flights(flight_date);
CREATE INDEX IF NOT EXISTS idx_flights_origin ON fact_flights(origin_airport);
CREATE INDEX IF NOT EXISTS idx_flights_dest ON fact_flights(destination_airport);
CREATE INDEX IF NOT EXISTS idx_flights_airline ON fact_flights(airline_code);
CREATE INDEX IF NOT EXISTS idx_flights_delay ON fact_flights(arr_delay_mins);
