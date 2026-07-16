-- View: Airline Performance (`vw_airline_performance.sql`)
CREATE OR REPLACE VIEW vw_airline_performance AS
SELECT 
    al.airline_code,
    al.airline_name,
    al.alliance,
    COUNT(f.flight_id) AS total_flights,
    ROUND(SUM(CASE WHEN f.arr_delay_mins < 15 AND f.cancelled_flag = 0 THEN 1.0 ELSE 0.0 END) / COUNT(f.flight_id) * 100, 2) AS on_time_pct,
    ROUND(AVG(CASE WHEN f.cancelled_flag = 0 THEN f.arr_delay_mins ELSE NULL END), 2) AS avg_delay_mins,
    ROUND(SUM(f.cancelled_flag * 1.0) / COUNT(f.flight_id) * 100, 2) AS cancellation_rate_pct
FROM dim_airlines al
LEFT JOIN fact_flights f ON al.airline_code = f.airline_code
GROUP BY al.airline_code, al.airline_name, al.alliance;
