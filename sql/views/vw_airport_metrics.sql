-- View: Hub Airport Operational Metrics (`vw_airport_metrics.sql`)
CREATE OR REPLACE VIEW vw_airport_metrics AS
SELECT 
    a.airport_code,
    a.airport_name,
    a.city,
    a.hub_status,
    COUNT(f.flight_id) AS scheduled_departures,
    ROUND(AVG(f.taxi_out_mins), 1) AS avg_taxi_out_tarmac,
    ROUND(SUM(CASE WHEN f.dep_delay_mins >= 15 THEN 1.0 ELSE 0.0 END) / COUNT(f.flight_id) * 100, 2) AS departure_delay_rate_pct,
    SUM(f.cancelled_flag) AS total_cancellations
FROM dim_airports a
LEFT JOIN fact_flights f ON a.airport_code = f.origin_airport
GROUP BY a.airport_code, a.airport_name, a.city, a.hub_status;
