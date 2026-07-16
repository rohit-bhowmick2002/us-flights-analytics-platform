# Enterprise Aviation Analytics — KPI & Metric Documentation (`kpi_documentation.md`)

This document defines the formal business definitions, mathematical formulas, SQL query mappings, and data sources for all Key Performance Indicators (KPIs) presented in the **Executive Business Intelligence & Operations Dashboard**.

---

## 1. Core Operational & Reliability KPIs

### 1.1 Total Scheduled Flights (`Total_Flights`)
* **Definition:** The total count of commercial passenger flights scheduled to depart during the selected time window.
* **Formula:** $\text{Total Flights} = \sum_{i=1}^{N} 1$
* **SQL Query Mapping:** `SELECT COUNT(*) FROM fact_flights;`
* **Source Table:** `fact_flights`

### 1.2 On-Time Performance Percentage (`On_Time_Pct`)
* **Definition:** The percentage of non-cancelled commercial flights that arrive at their destination gate within 15 minutes of the published scheduled arrival time ($\text{arr\_delay\_mins} < 15$). This matches the U.S. Department of Transportation (DOT) official standard ($A_{14}$ metric).
* **Formula:**
  $$\text{On-Time \%} = \left( \frac{\text{Count of Flights where } \text{arr\_delay\_mins} < 15 \text{ AND } \text{cancelled\_flag} = 0}{\text{Total Flights} - \text{Cancelled Flights}} \right) \times 100$$
* **SQL Query Mapping:**
  ```sql
  SELECT ROUND(SUM(CASE WHEN arr_delay_mins < 15 THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 2) AS ontime_pct
  FROM fact_flights WHERE cancelled_flag = 0;
  ```

### 1.3 Cancellation Rate Percentage (`Cancellation_Rate_Pct`)
* **Definition:** The proportion of scheduled flights that were formally cancelled by the airline or air traffic control prior to departure.
* **Formula:** $\text{Cancellation Rate \%} = \left( \frac{\sum \text{cancelled\_flag}}{\text{Total Scheduled Flights}} \right) \times 100$
* **SQL Query Mapping:** `SELECT ROUND(SUM(cancelled_flag * 1.0) / COUNT(*) * 100, 2) FROM fact_flights;`

### 1.4 Average Arrival Delay Minutes (`Average_Delay_Mins`)
* **Definition:** The arithmetic mean of arrival delay duration (in minutes) across all flights that experienced a delay of 15 minutes or greater. Early arrivals ($\text{arr\_delay\_mins} < 0$) are excluded from this specific severity average to prevent skewing the true burden on disrupted passengers.
* **Formula:**
  $$\text{Average Delay (Delayed Flights Only)} = \frac{\sum_{i \in \text{Delayed}} \text{arr\_delay\_mins}_i}{N_{\text{Delayed}}}$$

---

## 2. Root Cause Delay Breakdown KPIs (DOT Standard Categories)

When a flight arrives 15+ minutes late, the U.S. DOT requires carriers to apportion the delay across 5 standard operational categories:

| Category | Definition | Primary Drivers | SQL Column |
| :--- | :--- | :--- | :--- |
| **1. Carrier Delay** | Delay within the direct control of the airline operations team. | Aircraft maintenance/mechanical checks, crew scheduling, baggage loading, fueling delays. | `carrier_delay_mins` |
| **2. Weather Delay** | Significant meteorological conditions preventing safe takeoff or landing. | Tornadoes, blizzards, hurricanes, zero-visibility fog, severe icing, or wind shear at origin/destination. | `weather_delay_mins` |
| **3. NAS Delay** | Delays attributable to the National Airspace System (NAS) and Federal Aviation Administration (FAA). | Air Traffic Control (ATC) ground stops, runway congestion, non-extreme weather volume metering. | `nas_delay_mins` |
| **4. Security Delay** | Delays caused by airport terminal or aircraft security incidents. | TSA checkpoint breaches, bomb threats, re-screening of passengers or baggage. | `security_delay_mins` |
| **5. Late Aircraft** | Cascading delay caused by the late arrival of the same physical aircraft from its previous segment. | Tight turnaround schedules combined with earlier morning delays cascading into afternoon banks. | `late_aircraft_delay_mins` |

---

## 3. Network & Efficiency KPIs

### 3.1 Turnaround Buffer Time (`Turnaround_Buffer_Mins`)
* **Definition:** The scheduled time interval available between an aircraft's arrival at the gate from its inbound flight (`Inbound_Actual_Arr_Time`) and its scheduled departure for the next outbound leg (`CRS_Dep_Time`).
* **Why it matters:** Tight turnarounds ($<35$ minutes) have zero buffer for unexpected deplaning or cleaning delays. Our machine learning explainability analysis (`src/models/explainability.py`) proves that **Turnaround Buffer Time is the #1 strongest predictor of departure delays**.

### 3.2 Origin Airport Hourly Departure Density (`Origin_Hourly_Traffic`)
* **Definition:** The total number of commercial flights scheduled to depart from a specific origin airport within the same one-hour UTC/Local block.
* **Why it matters:** Captures hub congestion and taxi-way queue length during peak morning (08:00 - 10:00) and evening (16:00 - 19:00) departure banks.

---

## 4. PowerBI & Tableau Data Integration Guide

All KPIs documented above are automatically computed and exported by `src/visualization/dashboard_data.py` into ready-to-load relational CSV/Parquet tables stored in `dashboards/powerbi/`:
1. `exec_summary_kpi.csv`: Single-row system overview for executive cards.
2. `airline_scorecard.csv`: Carrier-level reliability and delay breakdown matrix.
3. `airport_metrics.csv`: Hub airport departure delays, taxi-out tarmac times, and weather incident counts.
4. `route_popularity.csv`: Corridor frequency, distance, and reliability metrics.
