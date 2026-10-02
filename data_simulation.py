"""
SIH26073 - Part 1: Synthetic AWS Data Generator
--------------------------------------------------
Generates fake Automatic Weather Station (AWS) data for 10 stations,
then intentionally injects errors (silent station, stuck sensor,
sudden spike, tampering-like pattern) so we can test our detection
engine later.

Run: python 1_generate_data.py
Output: aws_data.csv
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)  # so results are repeatable for demo

# ---- 1. Define 10 virtual stations with rough lat/lon (India-ish spread) ----
STATIONS = {
    "ST01": (28.61, 77.20),  # Delhi
    "ST02": (19.07, 72.87),  # Mumbai
    "ST03": (13.08, 80.27),  # Chennai
    "ST04": (12.97, 77.59),  # Bengaluru
    "ST05": (22.57, 88.36),  # Kolkata
    "ST06": (23.03, 72.58),  # Ahmedabad
    "ST07": (26.85, 80.95),  # Lucknow
    "ST08": (17.38, 78.49),  # Hyderabad
    "ST09": (15.30, 74.12),  # Belagavi
    "ST10": (30.74, 76.78),  # Chandigarh
}

READINGS_PER_STATION = 200          # ~ every 10 min over ~33 hours
START_TIME = datetime(2026, 8, 28, 0, 0, 0)
INTERVAL_MIN = 10


def generate_clean_reading(base_temp=30):
    """One normal, physically-realistic reading."""
    temperature = np.random.normal(base_temp, 2.5)
    rainfall = max(0, np.random.exponential(1.2) - 0.8)  # mostly 0, occasional rain
    humidity = np.clip(np.random.normal(60, 8), 10, 100)
    wind_speed = max(0, np.random.normal(12, 4))
    wind_direction = np.random.uniform(0, 360)  # degrees
    pressure = np.random.normal(1010, 3)
    cloud_cover = np.clip(np.random.normal(40, 25), 0, 100)  # %
    # more cloud cover -> less solar radiation, roughly (keeps synthetic data physically plausible)
    solar_radiation = max(0, np.random.normal(500, 150) * (1 - cloud_cover / 150))
    return (round(temperature, 1), round(rainfall, 1), round(humidity, 1),
            round(wind_speed, 1), round(wind_direction, 1), round(pressure, 1),
            round(solar_radiation, 1), round(cloud_cover, 1))


def build_dataset():
    rows = []
    for station_id, (lat, lon) in STATIONS.items():
        base_temp = np.random.uniform(24, 34)  # each station has its own climate baseline
        timestamp = START_TIME
        for i in range(READINGS_PER_STATION):
            temp, rain, hum, wind, wind_dir, pres, solar, cloud = generate_clean_reading(base_temp)
            rows.append([station_id, lat, lon, timestamp, temp, rain, hum, wind, wind_dir,
                         pres, solar, cloud])
            timestamp += timedelta(minutes=INTERVAL_MIN)

    df = pd.DataFrame(rows, columns=[
        "station_id", "lat", "lon", "timestamp",
        "temperature", "rainfall", "humidity", "wind_speed", "wind_direction", "pressure",
        "solar_radiation", "cloud_cover",
    ])
    return df


def inject_anomalies(df, scenario="default"):
    """Deliberately break some readings so our detector has something to catch.

    scenario="gurugram" replicates the real 2018 Gurugram incident: the
    station goes silent for an extended period, and while it's dead, a
    major rain event (128mm) happens that never gets recorded - exactly
    what triggered the real-world failure this project is built around.
    """
    df = df.copy()

    if scenario == "gurugram":
        # Silent for a LONG stretch (simulating 20-25 real days, compressed
        # into our shorter demo timeframe) - and importantly, a big rain
        # event happens at nearby stations DURING the silence, which is
        # exactly what went undetected in the real incident.
        st04_idx = df[df.station_id == "ST04"].index
        silent_block = st04_idx[40:160]  # a much longer silence than default
        df = df.drop(silent_block)

        # Big rain event at neighboring stations during the silent window -
        # this is the "128mm we would have missed" moment
        for other in ["ST03", "ST08", "ST09"]:
            other_idx = df[df.station_id == other].index
            block = other_idx[60:80]
            df.loc[block, "rainfall"] = np.random.uniform(15, 25, size=len(block)).round(1)

        return df.sort_values(["station_id", "timestamp"]).reset_index(drop=True)

    # ---- default scenario (original 5 mixed fault types) ----
    # 1. SILENT STATION -> remove 25 consecutive readings for ST04 (simulates Gurugram-style outage)
    st04_idx = df[df.station_id == "ST04"].index
    silent_block = st04_idx[80:105]
    df = df.drop(silent_block)

    # 2. STUCK SENSOR (flatline) -> ST02 temperature frozen at one value for 3 hours (18 readings)
    st02_idx = df[df.station_id == "ST02"].index
    stuck_block = st02_idx[50:68]
    df.loc[stuck_block, "temperature"] = 29.4

    # 3. SUDDEN IMPOSSIBLE SPIKE -> ST07 temperature jumps to 61C for one reading (sensor fault)
    st07_idx = df[df.station_id == "ST07"].index
    df.loc[st07_idx[120], "temperature"] = 61.0

    # 4. NEGATIVE RAINFALL -> ST09, impossible value (fault)
    st09_idx = df[df.station_id == "ST09"].index
    df.loc[st09_idx[30], "rainfall"] = -4.0

    # 5. POSSIBLE TAMPERING -> ST03 reports 0mm rain consistently while ALL its
    #    neighbors show real rain at the same timestamps (classic insurance-fraud pattern)
    st03_idx = df[df.station_id == "ST03"].index
    tamper_block = st03_idx[140:160]
    df.loc[tamper_block, "rainfall"] = 0.0
    # give same-timestamp neighbors real rain so the mismatch is detectable later
    for other in ["ST04", "ST08", "ST09"]:
        other_idx = df[df.station_id == other].index
        block = other_idx[140:160]
        df.loc[block, "rainfall"] = np.random.uniform(8, 20, size=len(block)).round(1)

    return df.sort_values(["station_id", "timestamp"]).reset_index(drop=True)


if __name__ == "__main__":
    clean_df = build_dataset()
    final_df = inject_anomalies(clean_df)
    final_df.to_csv("aws_data.csv", index=False)

    print(f"Generated {len(final_df)} readings across {len(STATIONS)} stations.")
    print("Injected anomalies:")
    print("  - ST04: silent for 25 readings (~4 hours)")
    print("  - ST02: stuck sensor, temperature frozen for 18 readings")
    print("  - ST07: one impossible spike (61C)")
    print("  - ST09: one negative rainfall value (-4mm)")
    print("  - ST03: suspicious 0mm rainfall while neighbors report real rain (possible tampering)")
    print("\nSaved to aws_data.csv")
