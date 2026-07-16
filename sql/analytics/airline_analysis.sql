-- Airline Reliability & Fleet Operations (`airline_analysis.sql`)
SELECT 
    f.airline_code,
    al.airline_name,
    COUNT(*) AS total_flights,
    ROUND(SUM(CASE WHEN f.arr_delay_mins < 15 THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 2) AS ontime_pct,
    ROUND(AVG(f.arr_delay_mins), 2) AS avg_arrival_delay,
    SUM(f.cancelled_flag) AS cancellations,
    ROUND(SUM(f.cancelled_flag * 1.0) / COUNT(*) * 100, 2) AS cancel_rate_pct,
    SUM(f.late_aircraft_delay_mins) AS cumulative_late_aircraft_mins
FROM fact_flights f
JOIN dim_airlines al ON f.airline_code = al.airline_code
GROUP BY f.airline_code, al.airline_name
ORDER BY ontime_pct DESC;
