# LandslideGuard NE
**Early Warning and Landslide Risk Monitoring System for the North Eastern Region of India**

Responsive college mini-project prototype with interactive map, rainfall indicators, transparent rule-based risk screening, SQLite history, prototype alert center, and CSV export.

> **Safety disclaimer:** This is an educational prototype. Its score thresholds are illustrative and not scientifically validated. It does not predict landslides reliably and does not issue official warnings. Always follow official advisories and local authorities.

## Features
- One reference location in each of the eight North Eastern states.
- Interactive Leaflet map with state, risk and rainfall filters.
- Offline demo data and optional Open-Meteo weather mode.
- Explanations for scores, missing inputs, and suggested precautions.
- SQLite assessment and alert storage; alert status management.
- Risk distribution and rainfall charts.
- CSV export, mobile-friendly layout, safety guidance.

## Run on Windows
Open PowerShell in this folder:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
If activation is blocked:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```
Open `http://127.0.0.1:5000`. Stop with Ctrl+C.

## Run on macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Use
1. Choose Demo data for offline sample rainfall values.
2. Filter the map, then click a marker or location row.
3. Inspect score reasons, missing data and precautionary advice.
4. Change alert status in Alert Center.
5. Try live weather mode. If the API is unreachable, sample values are used and the source label will show this.
6. Export reference locations using the CSV link.

## Data and scoring limitations
- Demo rainfall values are simulated, not actual observations.
- Live mode uses Open-Meteo weather data, not landslide occurrence data.
- The score adds illustrative points for rainfall bands only. It is not a calibrated probability and does not include verified slope, soil, geology, or historical landslide features.
- City coordinates are reference points, not necessarily landslide monitoring stations.
- Categories: 0–24 Low, 25–49 Moderate, 50–74 High, 75–100 Very High. These are demo thresholds, not official warning thresholds.
- Alerts are prototype-generated, not official government warnings.
- Map tiles, fonts and charts use external CDNs and need internet to display.

## Architecture
```text
Browser UI (HTML/CSS/JavaScript)
  ├─ Leaflet map + OpenStreetMap
  ├─ Chart.js analytics
  └─ Flask JSON endpoints
       ├─ Open-Meteo optional weather API
       ├─ transparent rule-based score
       └─ SQLite assessments and alerts
```

## Tests
```bash
python -m unittest discover -s tests -v
```

## Demo presentation flow
1. Introduce the problem and explain prototype limitations.
2. Show dashboard summary and map filters.
3. Select a location and explain its score and missing inputs.
4. Update an alert status.
5. Switch to live weather and identify data sources.
6. Explain future work: verified landslide inventory, terrain susceptibility, validated thresholds, model evaluation, official-agency integration.

## Official information
- NDMA: https://ndma.gov.in/
- India Meteorological Department: https://mausam.imd.gov.in/
- Sachet disaster alerts: https://sachet.ndma.gov.in/
