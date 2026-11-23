# Lahore Air Quality

**Question:** How much do wind and humidity explain PM2.5 pollution levels in Lahore?

This project collects air quality readings from sensors around Lahore and matches them with hourly weather, to build a dataset and study that question.

## What's in this repo

| File | What it does |
|---|---|
| `collect.py` | Gets the latest PM2.5 reading from each station, plus current weather, and appends it to `data/live.csv` |
| `collect_history.py` | Pulls the last 30 days of hourly PM2.5 and weather into `data/history.csv` |
| `stations.txt` | The OpenAQ station IDs and names the scripts use |
| `requirements.txt` | Python packages needed |

## Data sources

- **PM2.5:** [OpenAQ](https://openaq.org) (readings from real sensors)
- **Weather:** [Open-Meteo](https://open-meteo.com) (temperature, humidity and wind from a weather model, not a local station)

## Stations

Five stations across Lahore: 
4618814 Gulberg III
4698865 Cantonment
4555745 Ravi Road
4568423 Model Town
4527035 Civil Secretariat
Shalimar and Thokar Niaz Biag stations were dropped after first audit due to larger gaps.

## Data files

`data/history.csv` has these columns: `time_utc`, `pm25`, `station_id`, `station_name`, `temperature_c`, `humidity_pct`, `wind_kmh`. All times are in UTC (Pakistan time is UTC+5).

`data/live.csv` has: `collected_at_utc`, `station_id`, `station_name`, `pm25`, `pm25_measured_at_utc`, `temperature_c`, `humidity_pct`, `wind_kmh`.

## How to run it

1. Clone the repo and install the packages:
   ```
   pip install -r requirements.txt
   ```
2. Get a free API key at [explore.openaq.org](https://explore.openaq.org).
3. Create a file named `.env` in the project folder containing one line:
   ```
   OPENAQ_KEY=your-key-here
   ```
   The `.env` file is listed in `.gitignore`, so your key is never uploaded.
4. Run:
   ```
   python collect_history.py
   python collect.py
   ```

## Data quality notes so far

Stations don't report equally. Over the first 30-day pull (a full month is about 720 hourly readings):

| Station | Readings | Note |
|---|---|---|
| Gulberg III | 719 | nearly complete |
| Cantonment | 694 | good |
| Ravi Road | 661 | good |
| Thokar Niaz Baig | 367 | gaps, and stopped reporting on Nov 16 |
| Shalimar Town | 256 | scattered gaps |

Stale or missing readings will need handling before any analysis.

## Status

- [x] Latest-reading collector
- [x] 30-day historical pull
- [ ] Daily automatic collection with GitHub Actions
- [ ] Data audit (gaps, stuck values, spikes)
- [ ] Analysis report
