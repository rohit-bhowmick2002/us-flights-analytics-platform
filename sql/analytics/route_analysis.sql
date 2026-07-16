-- Corridor Route Efficiency & Performance (`route_analysis.sql`)
SELECT 
    f.origin_airport || ' -> ' || f.destination_airport AS route_pair,
    f.distance_miles,
    COUNT(*) AS frequency,
    ROUND(AVG(f.air_time_mins), 1) AS avg_air_time,
    ROUND(AVG(f.arr_delay_mins), 1) AS avg_delay_mins,
    ROUND(SUM(CASE WHEN f.arr_delay_mins < 15 THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 1) AS ontime_pct
FROM fact_flights f
WHERE f.cancelled_flag = 0
GROUP BY f.origin_airport, f.destination_airport, f.distance_miles
HAVING frequency >= 15
ORDER BY frequency DESC;
