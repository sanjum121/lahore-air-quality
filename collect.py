import csv
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

# ---------- Settings ----------
LAT, LON = 31.5204, 74.3587  # Lahore
OPENAQ = "https://api.openaq.org/v3"
OUT_FILE = Path("data/live.csv")

load_dotenv()  # reads the .env file if there is one
API_KEY = os.getenv("OPENAQ_KEY")
HEADERS = {"X-API-Key": API_KEY}


# ---------- 1. Read the station list ----------
def load_stations():
    stations = []
    for line in Path("stations.txt").read_text().splitlines():
        if line.strip():
            station_id, name = line.split(" ", 1)
            stations.append((int(station_id), name))
    return stations


# ---------- 2. Get the latest PM2.5 for one station ----------
def get_pm25(station_id):
    # Ask which sensors this station has, and find the PM2.5 one
    info = requests.get(f"{OPENAQ}/locations/{station_id}", headers=HEADERS, timeout=30)
    info.raise_for_status()
    sensors = info.json()["results"][0]["sensors"]
    pm25_ids = [s["id"] for s in sensors if s["parameter"]["name"] == "pm25"]
    if not pm25_ids:
        return None

    # Ask for the latest readings, and pick the PM2.5 one
    latest = requests.get(f"{OPENAQ}/locations/{station_id}/latest", headers=HEADERS, timeout=30)
    latest.raise_for_status()
    for item in latest.json()["results"]:
        if item["sensorsId"] == pm25_ids[0]:
            return item["value"], item["datetime"]["utc"]
    return None


# ---------- 3. Get current weather for Lahore ----------
def get_weather():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()["current"]


# ---------- 4. Put it all together ----------
def main():
    if not API_KEY:
        raise SystemExit("No OPENAQ_KEY found. Add it to your .env file.")

    weather = get_weather()
    collected_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []

    for station_id, name in load_stations():
        try:
            result = get_pm25(station_id)
        except Exception as error:  # one broken station should not stop the rest
            print(f"Skipping {name}: {error}")
            continue
        if result is None:
            print(f"No PM2.5 reading for {name}")
            continue
        pm25, measured_at = result
        rows.append([
            collected_at, station_id, name, pm25, measured_at,
            weather["temperature_2m"], weather["relative_humidity_2m"],
            weather["wind_speed_10m"],
        ])

    # ---------- 5. Save to the CSV file ----------
    OUT_FILE.parent.mkdir(exist_ok=True)
    is_new_file = not OUT_FILE.exists()
    with open(OUT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new_file:
            writer.writerow([
                "collected_at_utc", "station_id", "station_name", "pm25",
                "pm25_measured_at_utc", "temperature_c", "humidity_pct", "wind_kmh",
            ])
        writer.writerows(rows)

    print(f"Saved {len(rows)} rows to {OUT_FILE}")


if __name__ == "__main__":
    main()