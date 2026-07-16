# Power BI Dashboard Setup & Template Guide (`US_Flights_Analytics.pbix`)

The `US_Flights_Analytics.pbix` dashboard model is pre-configured to ingest the clean star-schema relational data exported by our Python pipeline (`src/visualization/dashboard_data.py`).

## 📥 Data Tables Included in Power BI Data Model
When opening `US_Flights_Analytics.pbix` in Power BI Desktop, the data model connects to the following local datasets inside `dashboards/powerbi/`:
1. **Executive Summary (`exec_summary_kpi.csv`)** — Drives the top KPI cards (Total Flights, On-Time %, Cancellation %, Average Delay).
2. **Airline Scorecard (`airline_scorecard.csv`)** — Drives the bar chart comparison (`AA`, `DL`, `UA`, `WN`, `B6`, `AS`, `NK`, `F9`).
3. **Airport Metrics (`airport_metrics.csv`)** — Drives the hub map and average taxi-out tarmac delay charts.
4. **Route Popularity (`route_popularity.csv`)** — Drives the top 10 busiest corridors and highest delay routes table.

## 🔄 How to Refresh Dashboard Data
To refresh the Power BI report after updating or running new pipeline simulations:
1. Run the Python data exporter:
   ```bash
   python src/pipeline.py --mode visualize
   ```
2. Open `US_Flights_Analytics.pbix` in Microsoft Power BI Desktop.
3. Click **Home $\rightarrow$ Refresh**. Power BI will instantly reload the CSVs and update all visual charts!
