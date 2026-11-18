import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# ---------- Settings ----------
LAT, LON = 31.5204, 74.3587  # Lahore
OPENAQ = "https://api.openaq.org/v3"
DAYS = 30
OUT_FILE = Path("data/history.csv")

load_dotenv()
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


# ---------- 2. Find the PM2.5 sensor at a station ----------
def get_pm25_sensor_id(station_id):
    r = requests.get(f"{OPENAQ}/locations/{station_id}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    for sensor in r.json()["results"][0]["sensors"]:
        if sensor["parameter"]["name"] == "pm25":
            return sensor["id"]
    return None


# ---------- 3. Get hourly PM2.5 for the last 30 days ----------
def get_pm25_history(sensor_id, start, end):
    params = {
        "datetime_from": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "datetime_to": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "limit": 1000,
    }
    r = requests.get(
        f"{OPENAQ}/sensors/{sensor_id}/hours",
        headers=HEADERS, params=params, timeout=60,
    )
    r.raise_for_status()
    rows = [
        {"time_utc": item["period"]["datetimeFrom"]["utc"], "pm25": item["value"]}
        for item in r.json()["results"]
    ]
    df = pd.DataFrame(rows)
    if not df.empty:
        df["time_utc"] = pd.to_datetime(df["time_utc"], utc=True).dt.floor("h")
    return df


# ---------- 4. Get hourly weather for the last 30 days ----------
def get_weather_history():
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "past_days": DAYS,
        "forecast_days": 1,
        "timezone": "UTC",
    }
    r = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=60)
    r.raise_for_status()
    hourly = r.json()["hourly"]
    df = pd.DataFrame({
        "time_utc": pd.to_datetime(hourly["time"], utc=True),
        "temperature_c": hourly["temperature_2m"],
        "humidity_pct": hourly["relative_humidity_2m"],
        "wind_kmh": hourly["wind_speed_10m"],
    })
    return df


# ---------- 5. Put it all together ----------
def main():
    if not API_KEY:
        raise SystemExit("No OPENAQ_KEY found. Add it to your .env file.")

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=DAYS)

    frames = []
    for station_id, name in load_stations():
        try:
            sensor_id = get_pm25_sensor_id(station_id)
            if sensor_id is None:
                print(f"No PM2.5 sensor at {name}")
                continue
            df = get_pm25_history(sensor_id, start, end)
        except Exception as error:
            print(f"Skipping {name}: {error}")
            continue
        if df.empty:
            print(f"No data for {name}")
            continue
        df["station_id"] = station_id
        df["station_name"] = name
        frames.append(df)
        print(f"{name}: {len(df)} hourly readings")
        time.sleep(1)  # be polite to the API

    if not frames:
        raise SystemExit("No PM2.5 data collected.")

    pm25 = pd.concat(frames, ignore_index=True)
    weather = get_weather_history()

    # Match each PM2.5 reading to the weather in the same hour
    merged = pm25.merge(weather, on="time_utc", how="left")
    merged = merged.sort_values(["station_id", "time_utc"])

    OUT_FILE.parent.mkdir(exist_ok=True)
    merged.to_csv(OUT_FILE, index=False)
    print(f"Saved {len(merged)} rows to {OUT_FILE}")


if __name__ == "__main__":
    main()