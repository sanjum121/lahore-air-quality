import sys
from datetime import datetime, timedelta, timezone

import pandas as pd

EXPECTED = [
    "collected_at_utc", "station_id", "station_name", "pm25",
    "pm25_measured_at_utc", "temperature_c", "humidity_pct", "wind_kmh",
]


def main():
    try:
        df = pd.read_csv("data/live.csv")
    except Exception as error:
        sys.exit(f"Cannot read data/live.csv: {error}")

    # Structure checks (these FAIL the run)
    missing = [c for c in EXPECTED if c not in df.columns]
    if missing:
        sys.exit(f"Missing columns: {missing}")
    if df.empty:
        sys.exit("live.csv has no rows")

    latest_time = pd.to_datetime(df["collected_at_utc"], utc=True).max()
    if datetime.now(timezone.utc) - latest_time > timedelta(hours=2):
        sys.exit("No new rows were added in this run")

    latest = df[pd.to_datetime(df["collected_at_utc"], utc=True) == latest_time]
    for col in ["pm25", "temperature_c", "humidity_pct", "wind_kmh"]:
        if pd.to_numeric(latest[col], errors="coerce").isna().any():
            sys.exit(f"Non-numeric or empty values in {col}")

    # Suspicious values (these only WARN)
    pm25 = pd.to_numeric(latest["pm25"], errors="coerce")
    if (pm25 < 0).any() or (pm25 > 1500).any():
        print("WARNING: PM2.5 value out of the normal range")

    print(f"OK: {len(latest)} rows in the latest run")


if __name__ == "__main__":
    main()