"""
detection/neighbor.py - Layer 2: Spatial cross-checking.
Compares each station against its nearest neighbors to catch tampering
(a value that looks individually valid but doesn't match what's
happening nearby). Falls back to the station's own history if no
neighbors are available (e.g. a remote station). Also outputs a
"corrected value" estimate with an honest uncertainty range - never a
falsely precise number - and a subtle-tampering z-score that catches
patterns too small for a hard cutoff to notice.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import pandas as pd
import config


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def find_neighbors(station_coords, n=config.NUM_NEIGHBORS):
    neighbors = {}
    for station, (lat, lon) in station_coords.items():
        distances = [(other, haversine_km(lat, lon, olat, olon))
                     for other, (olat, olon) in station_coords.items() if other != station]
        distances.sort(key=lambda x: x[1])
        neighbors[station] = [s for s, d in distances[:n]]
    return neighbors


def estimate_corrected_value(neighbor_avg, neighbor_std):
    low, high = round(neighbor_avg - neighbor_std, 1), round(neighbor_avg + neighbor_std, 1)
    return f"{low}mm to {high}mm (estimated, not confirmed)"


def subtle_tampering_score(diffs: np.ndarray) -> float:
    """% of readings that look 'suspiciously low' vs neighbors, even if
    each individual reading isn't extreme enough to trip a hard cutoff."""
    if diffs.std() == 0:
        return 0.0
    z = (diffs - diffs.mean()) / diffs.std()
    return round(float(np.mean(z < -1.0) * 100), 1)


def run(df) -> pd.DataFrame:
    station_coords = df.drop_duplicates("station_id").set_index("station_id")[["lat", "lon"]]
    station_coords = {k: (v["lat"], v["lon"]) for k, v in station_coords.to_dict("index").items()}
    neighbors = find_neighbors(station_coords)

    pivot = df.pivot_table(index="timestamp", columns="station_id", values="rainfall").sort_index()
    flags = []

    for station, nbr_list in neighbors.items():
        if station not in pivot.columns:
            continue
        nbr_cols = [n for n in nbr_list if n in pivot.columns]

        if nbr_cols:
            compare_series = pivot[nbr_cols].mean(axis=1)
            source = "neighbor-based"
        else:
            # fallback: no neighbors available, use this station's own expanding average
            compare_series = pivot[station].expanding().mean()
            source = "self-history-based (no neighbors available)"

        station_series = pivot[station]
        is_suspicious = (station_series < 1.0) & (compare_series > config.MISMATCH_THRESHOLD_MM)

        timestamps = pivot.index.to_list()
        run_start = None
        for i, ts in enumerate(timestamps):
            val = is_suspicious.get(ts, False)
            if val and run_start is None:
                run_start = i
            if (not val or i == len(timestamps) - 1) and run_start is not None:
                run_end = i if not val else i + 1
                run_len = run_end - run_start
                if run_len >= config.REPEAT_COUNT:
                    seg_own = station_series.iloc[run_start:run_end]
                    seg_cmp = compare_series.iloc[run_start:run_end]
                    diffs = (seg_cmp - seg_own).values
                    flags.append({
                        "station_id": station, "timestamp": timestamps[run_start],
                        "flag_type": "Possible tampering",
                        "reason": f"Reported ~{seg_own.mean():.1f}mm while {source} average was "
                                  f"{seg_cmp.mean():.1f}mm, for {run_len} consecutive readings ({source})",
                        "corrected_value": estimate_corrected_value(seg_cmp.mean(), seg_cmp.std() or 1.0),
                        "subtle_tampering_score_%": subtle_tampering_score(diffs),
                    })
                run_start = None

    return pd.DataFrame(flags)
