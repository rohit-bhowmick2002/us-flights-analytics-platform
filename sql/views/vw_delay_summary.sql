-- View: Delay Breakdown Summary (`vw_delay_summary.sql`)
CREATE OR REPLACE VIEW vw_delay_summary AS
SELECT 
    f.flight_date,
    f.origin_airport,
    f.airline_code,
    COUNT(*) AS total_flights,
    SUM(CASE WHEN f.arr_delay_mins >= 15 THEN 1 ELSE 0 END) AS delayed_flights,
    SUM(f.carrier_delay_mins) AS total_carrier_delay,
    SUM(f.weather_delay_mins) AS total_weather_delay,
    SUM(f.nas_delay_mins) AS total_nas_delay,
    SUM(f.late_aircraft_delay_mins) AS total_late_aircraft_delay
FROM fact_flights f
WHERE f.cancelled_flag = 0
GROUP BY f.flight_date, f.origin_airport, f.airline_code;
