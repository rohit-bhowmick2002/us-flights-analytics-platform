-- Staging Model: Weather (`stg_weather.sql`)
with source as (
    select * from {{ source('raw_aviation', 'weather_hourly') }}
),

renamed as (
    select
        cast(airport_code as varchar) as airport_code,
        cast(utc_timestamp as timestamp) as observation_time,
        date_trunc('hour', cast(utc_timestamp as timestamp)) as weather_join_hour,
        cast(temperature as decimal(5,2)) as temp_fahrenheit,
        cast(wind_speed as decimal(5,2)) as wind_speed_knots,
        cast(visibility as decimal(5,2)) as visibility_miles,
        cast(precipitation as decimal(5,2)) as precip_inches,
        coalesce(weather_condition, 'Clear') as weather_condition
    from source
)

select * from renamed
