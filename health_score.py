"""
health_score.py - Industrial-grade station health scoring.

UPGRADED VERSION (was: simple anomaly-count penalty).
Now combines 4 independent signals (multi-factor scoring, like real
industrial IoT systems use for wind turbines / factory equipment):

  1. Anomaly frequency      - how often this station gets flagged
  2. Data completeness      - how much data is missing/silent
  3. Sensor variance        - how "noisy"/erratic readings are
                              (rising noise = early sign of a sensor
                              wearing out, even before it fully fails)
  4. Communication reliability - gaps in reporting = connector/network wear

...then adds a simple trend line to ESTIMATE REMAINING USEFUL LIFE
(RUL) - i.e. "at this rate of decline, maintenance will be needed in
~X days" - instead of just a static snapshot score.
"""

from datetime import timedelta
import numpy as np
import pandas as pd
import config

# How much each factor contributes to the final score (must sum to 1.0)
FACTOR_WEIGHTS = {
    "anomaly_frequency": 0.40,
    "data_completeness": 0.20,
    "sensor_variance": 0.20,
    "communication_reliability": 0.20,
}


def _score_anomaly_frequency(station_id, raw_df, all_flags_df, window_start):
    """Fewer flags relative to this station's own reading count = healthier."""
    station_readings = raw_df[raw_df["station_id"] == station_id]
    n_readings = max(len(station_readings), 1)
    n_flags = len(all_flags_df[
        (all_flags_df["station_id"] == station_id)
        & (pd.to_datetime(all_flags_df["timestamp"]) >= window_start)
    ]) if len(all_flags_df) else 0
    flag_rate = n_flags / n_readings
    return max(0, 100 - flag_rate * 500)  # scaled so a 20% flag rate -> 0


def _score_data_completeness(station_id, raw_df, window_start):
    """Compares actual reading count to the EXPECTED count (every 10 min)
    in the same window - missing readings = silent-station gaps."""
    station_df = raw_df[(raw_df["station_id"] == station_id) & (raw_df["timestamp"] >= window_start)]
    if station_df.empty:
        return 0
    actual_span_minutes = (station_df["timestamp"].max() - station_df["timestamp"].min()).total_seconds() / 60
    expected_readings = max(actual_span_minutes / config.DATA_INTERVAL_MINUTES, 1)
    completeness_ratio = min(len(station_df) / expected_readings, 1.0)
    return completeness_ratio * 100


def _score_sensor_variance(station_id, raw_df, window_start):
    """Sudden increase in reading-to-reading noise (temperature jitter)
    is an early warning sign of a degrading sensor, even if every
    individual value is still technically 'in range'."""
    station_df = raw_df[(raw_df["station_id"] == station_id) & (raw_df["timestamp"] >= window_start)]
    if len(station_df) < 3:
        return 100  # not enough data to judge - assume healthy rather than penalize
    jitter = station_df["temperature"].diff().abs().mean()
    # typical healthy jitter is small (~0.5-1.5C between consecutive readings);
    # scale so jitter of 5C+ trends toward 0
    return max(0, 100 - (jitter / 5) * 100)


def _score_communication_reliability(station_id, raw_df, window_start):
    """Same idea as completeness but framed as 'reliability of the link',
    penalized more sharply for LONG individual gaps (a dead radio/modem)
    rather than just total missing count."""
    station_df = raw_df[(raw_df["station_id"] == station_id) & (raw_df["timestamp"] >= window_start)]
    station_df = station_df.sort_values("timestamp")
    if len(station_df) < 2:
        return 100
    gaps_minutes = station_df["timestamp"].diff().dt.total_seconds().dropna() / 60
    longest_gap = gaps_minutes.max() if len(gaps_minutes) else 0
    if longest_gap <= config.DATA_INTERVAL_MINUTES * 1.25:
        return 100
    return max(0, 100 - (max(0, longest_gap - config.DATA_INTERVAL_MINUTES) / 60) * 20)  # every hour of longest gap costs 20 points


def compute_health_scores(raw_df: pd.DataFrame, all_flags_df: pd.DataFrame,
                           window_days: int = 30) -> pd.DataFrame:
    """Multi-factor health score (0-100) + status label per station."""
    raw_df = raw_df.copy()
    raw_df["timestamp"] = pd.to_datetime(raw_df["timestamp"])
    latest_time = raw_df["timestamp"].max()
    window_start = latest_time - timedelta(days=window_days)

    results = []
    for station_id in raw_df["station_id"].unique():
        factors = {
            "anomaly_frequency": _score_anomaly_frequency(station_id, raw_df, all_flags_df, window_start),
            "data_completeness": _score_data_completeness(station_id, raw_df, window_start),
            "sensor_variance": _score_sensor_variance(station_id, raw_df, window_start),
            "communication_reliability": _score_communication_reliability(station_id, raw_df, window_start),
        }
        final_score = round(sum(factors[k] * FACTOR_WEIGHTS[k] for k in factors), 1)

        if final_score >= 80:
            status = "Healthy"
        elif final_score >= 50:
            status = "Monitor"
        else:
            status = "Needs maintenance"

        results.append({
            "station_id": station_id,
            "health_score": final_score,
            "status": status,
            "anomaly_frequency_score": round(factors["anomaly_frequency"], 1),
            "data_completeness_score": round(factors["data_completeness"], 1),
            "sensor_variance_score": round(factors["sensor_variance"], 1),
            "communication_score": round(factors["communication_reliability"], 1),
        })

    return pd.DataFrame(results).sort_values("health_score")


def predict_remaining_life(health_history, critical_threshold: float = 50) -> str:
    """Fits a simple straight-line trend through past health scores to
    estimate when a station will cross the 'needs maintenance' line.
    Needs at least 3 historical data points to give a meaningful answer -
    with less than that, it honestly says so instead of guessing."""
    if len(health_history) < 3:
        return "Not enough history yet to predict (need 3+ past health readings)"

    days = np.arange(len(health_history))
    scores = np.array(health_history)

    slope = np.polyfit(days, scores, 1)[0]  # points change per "day" in history
    current_score = scores[-1]

    if slope >= 0:
        return "Stable or improving - no maintenance predicted based on current trend"

    days_until_critical = (current_score - critical_threshold) / (-slope)
    if days_until_critical < 0:
        return "Already at/below the maintenance threshold - inspect now"
    return f"At current decline rate, estimated {int(days_until_critical)} day(s) until maintenance needed"


# ============================================================
# HISTORY TRACKING - makes predict_remaining_life() actually usable
# ============================================================
HISTORY_FILE = "health_score_history.csv"


def save_to_history(health_df: pd.DataFrame, history_file: str = HISTORY_FILE):
    """Appends today's health scores to a running history file, so that
    over multiple runs (days/weeks) we build up enough data points for
    predict_remaining_life() to work with. Safe to call every run -
    creates the file on first use, appends after that."""
    import os
    from datetime import datetime

    snapshot = health_df[["station_id", "health_score"]].copy()
    snapshot["run_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if os.path.exists(history_file):
        existing = pd.read_csv(history_file)
        combined = pd.concat([existing, snapshot], ignore_index=True)
    else:
        combined = snapshot

    combined.to_csv(history_file, index=False)
    return combined


def load_history_for_station(station_id: str, history_file: str = HISTORY_FILE) -> list:
    """Returns this station's past health scores in chronological order,
    ready to feed into predict_remaining_life()."""
    import os

    if not os.path.exists(history_file):
        return []
    history = pd.read_csv(history_file)
    station_history = history[history["station_id"] == station_id].sort_values("run_date")
    return station_history["health_score"].tolist()


def add_life_predictions(health_df: pd.DataFrame, history_file: str = HISTORY_FILE) -> pd.DataFrame:
    """Adds a 'remaining_life_prediction' column to the health score
    table, using each station's saved history (built up over multiple
    runs of main.py)."""
    predictions = []
    for station_id in health_df["station_id"]:
        past_scores = load_history_for_station(station_id, history_file)
        predictions.append(predict_remaining_life(past_scores))
    health_df = health_df.copy()
    health_df["remaining_life_prediction"] = predictions
    return health_df
