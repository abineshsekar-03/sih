"""
detection/rules.py - Layer 1: Rule-based checks.
Physically impossible values, flatline (stuck) sensors, and silent
stations. Thresholds pulled from config.py so they're tunable in one place.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import config


def check_value_ranges(df):
    flags = []
    for idx, row in df.iterrows():
        reasons = []
        month = pd.Timestamp(row["timestamp"]).month
        rain_threshold = config.seasonal_rain_threshold(month)

        if not (config.TEMP_MIN <= row["temperature"] <= config.TEMP_MAX):
            reasons.append(f"Temperature {row['temperature']}C out of range")
        if row["rainfall"] < 0:
            reasons.append(f"Negative rainfall {row['rainfall']}mm - impossible")
        if row["rainfall"] > rain_threshold:
            reasons.append(f"Rainfall {row['rainfall']}mm exceeds seasonal threshold ({rain_threshold}mm)")
        if not (config.HUMIDITY_MIN <= row["humidity"] <= config.HUMIDITY_MAX):
            reasons.append(f"Humidity {row['humidity']}% out of range")
        if not (config.WIND_MIN <= row["wind_speed"] <= config.WIND_MAX):
            reasons.append(f"Wind speed {row['wind_speed']}km/h out of range")
        if not (config.PRESSURE_MIN <= row["pressure"] <= config.PRESSURE_MAX):
            reasons.append(f"Pressure {row['pressure']}hPa out of range")

        if reasons:
            flags.append({
                "station_id": row["station_id"], "timestamp": row["timestamp"],
                "flag_type": "Sensor fault (range check)",
                "reason": "; ".join(reasons), "num_issues": len(reasons),
            })
    return flags


def check_flatline(df):
    flags = []
    for station_id, group in df.groupby("station_id"):
        group = group.sort_values("timestamp").reset_index(drop=True)
        temps = group["temperature"].values
        run_start = 0
        for i in range(1, len(temps) + 1):
            if i == len(temps) or temps[i] != temps[run_start]:
                run_len = i - run_start
                if run_len >= config.FLATLINE_COUNT:
                    flags.append({
                        "station_id": station_id, "timestamp": group.loc[run_start, "timestamp"],
                        "flag_type": "Sensor fault (flatline)",
                        "reason": f"Temperature stuck at {temps[run_start]}C for {run_len} readings",
                        "num_issues": 1,
                    })
                run_start = i
    return flags


def check_silent_stations(df):
    flags = []
    for station_id, group in df.groupby("station_id"):
        group = group.sort_values("timestamp").reset_index(drop=True)
        gaps = group["timestamp"].diff().dt.total_seconds() / 60
        for i, gap in enumerate(gaps):
            if pd.notna(gap) and gap > config.SILENT_GAP_MINUTES:
                flags.append({
                    "station_id": station_id, "timestamp": group.loc[i, "timestamp"],
                    "flag_type": "Silent station",
                    "reason": f"No data received for {int(gap)} minutes (expected every 60 min)",
                    "num_issues": 1,
                })
    return flags


def run(df) -> pd.DataFrame:
    flags = check_value_ranges(df) + check_flatline(df) + check_silent_stations(df)
    return pd.DataFrame(flags)
