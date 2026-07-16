-- Weather Severity vs Operational Disruptions (`weather_analysis.sql`)
SELECT 
    w.weather_condition,
    COUNT(f.flight_id) AS total_flights,
    ROUND(SUM(CASE WHEN f.arr_delay_mins >= 15 THEN 1.0 ELSE 0.0 END) / COUNT(f.flight_id) * 100, 2) AS delay_rate_pct,
    ROUND(AVG(f.arr_delay_mins), 2) AS avg_delay_mins,
    SUM(f.cancelled_flag) AS total_cancellations
FROM fact_flights f
JOIN dim_weather_hourly w ON f.origin_airport = w.airport_code 
    AND STRFTIME('%Y-%m-%d %H:00:00', f.crs_dep_time) = w.utc_timestamp
GROUP BY w.weather_condition
HAVING total_flights >= 10
ORDER BY delay_rate_pct DESC;
