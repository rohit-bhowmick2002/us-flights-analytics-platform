-- Deep-Dive Delay Root Cause Breakdown (`delay_analysis.sql`)
SELECT 
    f.delay_reason,
    COUNT(*) AS incident_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM fact_flights WHERE arr_delay_mins >= 15), 2) AS pct_of_delayed_flights,
    ROUND(AVG(f.arr_delay_mins), 1) AS avg_duration_mins,
    SUM(f.arr_delay_mins) AS total_minutes_lost
FROM fact_flights f
WHERE f.arr_delay_mins >= 15 AND f.cancelled_flag = 0
GROUP BY f.delay_reason
ORDER BY total_minutes_lost DESC;
