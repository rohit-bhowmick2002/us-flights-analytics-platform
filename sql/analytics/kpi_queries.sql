-- =============================================================================
-- Enterprise KPI Queries (`kpi_queries.sql`)
-- Answers the Top 10 Executive SQL Questions across Aviation Operations
-- =============================================================================

-- 1. Top 10 Busiest Airports (by total flight departures)
SELECT 
    f.origin_airport AS airport_code,
    a.airport_name,
    a.city,
    COUNT(*) AS total_departures,
    ROUND(AVG(f.dep_delay_mins), 2) AS avg_departure_delay
FROM fact_flights f
JOIN dim_airports a ON f.origin_airport = a.airport_code
GROUP BY f.origin_airport, a.airport_name, a.city
ORDER BY total_departures DESC
LIMIT 10;

-- 2. Airline with Lowest Delay (On-Time Performance Rate %)
SELECT 
    f.airline_code,
    al.airline_name,
    COUNT(*) AS total_flights,
    SUM(CASE WHEN f.arr_delay_mins < 15 THEN 1 ELSE 0 END) AS ontime_flights,
    ROUND(SUM(CASE WHEN f.arr_delay_mins < 15 THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 2) AS ontime_pct,
    ROUND(AVG(f.arr_delay_mins), 2) AS avg_arrival_delay
FROM fact_flights f
JOIN dim_airlines al ON f.airline_code = al.airline_code
WHERE f.cancelled_flag = 0
GROUP BY f.airline_code, al.airline_name
ORDER BY ontime_pct DESC;

-- 3. Monthly Delay Trend
SELECT 
    STRFTIME('%Y-%m', f.flight_date) AS year_month,
    COUNT(*) AS total_flights,
    SUM(CASE WHEN f.arr_delay_mins >= 15 THEN 1 ELSE 0 END) AS delayed_flights,
    ROUND(SUM(CASE WHEN f.arr_delay_mins >= 15 THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 2) AS delay_rate_pct,
    ROUND(AVG(f.arr_delay_mins), 2) AS avg_delay_mins
FROM fact_flights f
WHERE f.cancelled_flag = 0
GROUP BY STRFTIME('%Y-%m', f.flight_date)
ORDER BY year_month ASC;

-- 4. Average Delay by Airport (Origin & Destination Impact)
SELECT 
    a.airport_code,
    a.airport_name,
    ROUND(AVG(f_dep.dep_delay_mins), 2) AS avg_dep_delay_mins,
    ROUND(AVG(f_arr.arr_delay_mins), 2) AS avg_arr_delay_mins
FROM dim_airports a
LEFT JOIN fact_flights f_dep ON a.airport_code = f_dep.origin_airport AND f_dep.cancelled_flag = 0
LEFT JOIN fact_flights f_arr ON a.airport_code = f_arr.destination_airport AND f_arr.cancelled_flag = 0
GROUP BY a.airport_code, a.airport_name
ORDER BY avg_arr_delay_mins DESC;

-- 5. Cancellation Rate by Airline & Primary Reason
SELECT 
    f.airline_code,
    al.airline_name,
    COUNT(*) AS total_flights,
    SUM(f.cancelled_flag) AS total_cancellations,
    ROUND(SUM(f.cancelled_flag * 1.0) / COUNT(*) * 100, 2) AS cancellation_rate_pct,
    SUM(CASE WHEN f.cancellation_reason = 'Weather' THEN 1 ELSE 0 END) AS weather_cancels,
    SUM(CASE WHEN f.cancellation_reason = 'Carrier' THEN 1 ELSE 0 END) AS carrier_cancels,
    SUM(CASE WHEN f.cancellation_reason = 'NAS' THEN 1 ELSE 0 END) AS nas_cancels
FROM fact_flights f
JOIN dim_airlines al ON f.airline_code = al.airline_code
GROUP BY f.airline_code, al.airline_name
ORDER BY cancellation_rate_pct DESC;

-- 6. Peak Travel Hour (Hourly Departure Distribution & Congestion)
SELECT 
    STRFTIME('%H', f.crs_dep_time) AS scheduled_hour,
    COUNT(*) AS total_departures,
    ROUND(AVG(f.taxi_out_mins), 2) AS avg_taxi_out_tarmac_mins,
    ROUND(SUM(CASE WHEN f.dep_delay_mins >= 15 THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 2) AS dep_delay_rate_pct
FROM fact_flights f
WHERE f.cancelled_flag = 0
GROUP BY STRFTIME('%H', f.crs_dep_time)
ORDER BY total_departures DESC;

-- 7. Weather Impact on Delays (By Weather Category Breakdown)
SELECT 
    CASE 
        WHEN f.weather_delay_mins > 0 THEN 'Direct Weather Delay'
        WHEN f.late_aircraft_delay_mins > 0 THEN 'Late Aircraft (Cascading)'
        WHEN f.carrier_delay_mins > 0 THEN 'Carrier Operations'
        WHEN f.nas_delay_mins > 0 THEN 'NAS / ATC Bottleneck'
        ELSE 'On-Time / Minor'
    END AS delay_category,
    COUNT(*) AS flight_count,
    ROUND(AVG(f.arr_delay_mins), 2) AS avg_minutes_delayed,
    SUM(f.arr_delay_mins) AS total_cumulative_delay_mins
FROM fact_flights f
WHERE f.cancelled_flag = 0 AND f.arr_delay_mins >= 15
GROUP BY delay_category
ORDER BY total_cumulative_delay_mins DESC;

-- 8. Longest Routes (Air Time vs Scheduled Distance)
SELECT 
    f.origin_airport || ' -> ' || f.destination_airport AS route_pair,
    a1.city || ' to ' || a2.city AS city_pair,
    f.distance_miles,
    ROUND(AVG(f.air_time_mins), 1) AS avg_air_time_mins,
    COUNT(*) AS flights_operating
FROM fact_flights f
JOIN dim_airports a1 ON f.origin_airport = a1.airport_code
JOIN dim_airports a2 ON f.destination_airport = a2.airport_code
GROUP BY f.origin_airport, f.destination_airport, a1.city, a2.city, f.distance_miles
ORDER BY f.distance_miles DESC
LIMIT 10;

-- 9. Route Profitability & Efficiency Proxy (Seat-Miles per Flight Hour)
SELECT 
    f.origin_airport || ' -> ' || f.destination_airport AS route_pair,
    COUNT(*) AS total_flights,
    ROUND(AVG(f.distance_miles * ac.capacity), 0) AS avg_available_seat_miles,
    ROUND(AVG(f.arr_delay_mins), 1) AS avg_delay_mins,
    ROUND(SUM(CASE WHEN f.arr_delay_mins < 15 THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 1) AS operational_reliability_pct
FROM fact_flights f
LEFT JOIN dim_aircraft ac ON f.tail_number = ac.tail_number
GROUP BY f.origin_airport, f.destination_airport
HAVING total_flights >= 10
ORDER BY avg_available_seat_miles DESC
LIMIT 10;

-- 10. Delay Distribution by Weekday (0 = Monday, 6 = Sunday)
SELECT 
    CASE STRFTIME('%w', f.flight_date)
        WHEN '0' THEN 'Sunday'
        WHEN '1' THEN 'Monday'
        WHEN '2' THEN 'Tuesday'
        WHEN '3' THEN 'Wednesday'
        WHEN '4' THEN 'Thursday'
        WHEN '5' THEN 'Friday'
        WHEN '6' THEN 'Saturday'
    END AS day_of_week,
    COUNT(*) AS total_flights,
    ROUND(SUM(CASE WHEN f.arr_delay_mins >= 15 THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 2) AS delay_pct,
    ROUND(AVG(f.arr_delay_mins), 2) AS avg_arrival_delay_mins
FROM fact_flights f
WHERE f.cancelled_flag = 0
GROUP BY STRFTIME('%w', f.flight_date)
ORDER BY STRFTIME('%w', f.flight_date) ASC;
