-- Marts Fact Table (`fact_flights.sql`)
-- Joins staging flights with hourly weather and graph centrality
with flights as (
    select * from {{ ref('stg_flights') }}
),

weather as (
    select * from {{ ref('stg_weather') }}
)

select
    f.*,
    w.temp_fahrenheit as origin_forecast_temp,
    w.wind_speed_knots as origin_forecast_wind_speed,
    w.visibility_miles as origin_forecast_visibility,
    w.weather_condition as origin_weather_condition,
    case when f.arrival_delay_minutes >= 15 then 1 else 0 end as is_delayed_15m
from flights f
left join weather w
    on f.origin_airport_code = w.airport_code
    and date_trunc('hour', f.scheduled_departure_time) = w.weather_join_hour
