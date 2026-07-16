-- Staging Model: Flights (`stg_flights.sql`)
-- Cleans timestamps and standardizes raw schedule data
with source as (
    select * from {{ source('raw_aviation', 'flights_raw') }}
),

renamed as (
    select
        cast(flight_id as varchar) as flight_id,
        cast(flight_date as date) as flight_date,
        cast(crs_dep_time as timestamp) as scheduled_departure_time,
        cast(crs_arr_time as timestamp) as scheduled_arrival_time,
        cast(actual_dep_time as timestamp) as actual_departure_time,
        cast(actual_arr_time as timestamp) as actual_arrival_time,
        cast(airline_code as varchar) as carrier_code,
        cast(flight_number as integer) as flight_number,
        cast(tail_number as varchar) as aircraft_tail_number,
        cast(origin_airport as varchar) as origin_airport_code,
        cast(destination_airport as varchar) as dest_airport_code,
        cast(distance_miles as integer) as distance_miles,
        cast(air_time_mins as integer) as air_time_minutes,
        coalesce(cast(dep_delay_mins as integer), 0) as departure_delay_minutes,
        coalesce(cast(arr_delay_mins as integer), 0) as arrival_delay_minutes,
        cast(cancelled_flag as integer) as is_cancelled,
        coalesce(cancellation_reason, 'None') as cancellation_reason,
        cast(turnaround_buffer_mins as integer) as turnaround_buffer_minutes
    from source
    where flight_id is not null
)

select * from renamed
