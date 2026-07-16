-- Airport Operations & Bottleneck Analytics (`airport_analysis.sql`)
SELECT 
    f.origin_airport AS airport_code,
    a.airport_name,
    COUNT(*) AS scheduled_departures,
    ROUND(AVG(f.taxi_out_mins), 2) AS avg_tarmac_taxi_out,
    SUM(CASE WHEN f.dep_delay_mins >= 15 THEN 1 ELSE 0 END) AS delayed_departures,
    ROUND(SUM(CASE WHEN f.dep_delay_mins >= 15 THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 2) AS dep_delay_rate_pct,
    ROUND(AVG(f.carrier_delay_mins), 2) AS avg_carrier_delay,
    ROUND(AVG(f.weather_delay_mins), 2) AS avg_weather_delay
FROM fact_flights f
JOIN dim_airports a ON f.origin_airport = a.airport_code
GROUP BY f.origin_airport, a.airport_name
ORDER BY scheduled_departures DESC;
