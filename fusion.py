"""
fusion.py - Combines all detection layers into one final verdict.
This is the "reasoning core" of the system: takes independent outputs
from rules, physics, neighbor-comparison, and ML layers, and produces:
  - attribution   : the most useful single label for what went wrong
  - confidence     : % of layers that agree (simple, explainable - not
                      a black-box number)
  - trust_state    : ACCEPT / CAUTION / QUARANTINE / REJECT
"""

import pandas as pd
import config


def _match_key(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["match_key"] = df["station_id"] + "_" + df["timestamp"].dt.floor(f"{config.DATA_INTERVAL_MINUTES}min").astype(str)
    return df


def _trust_state(confidence: float, attribution: str) -> str:
    if attribution == "Silent station":
        return "REJECT"
    if confidence >= config.TRUST_QUARANTINE_CONFIDENCE:
        return "QUARANTINE"
    if confidence >= config.TRUST_CAUTION_CONFIDENCE:
        return "CAUTION"
    return "ACCEPT"


def _alert_priority(confidence: float) -> str:
    if confidence >= config.ALERT_CRITICAL_CONFIDENCE:
        return "CRITICAL - send immediately"
    if confidence >= config.ALERT_MEDIUM_CONFIDENCE:
        return "MEDIUM - daily digest"
    return "LOW - log only"


def combine(rule_df, physics_df, neighbor_df, ml_df) -> pd.DataFrame:
    rule_df = _match_key(rule_df)
    physics_df = _match_key(physics_df)
    neighbor_df = _match_key(neighbor_df)
    ml_df = _match_key(ml_df)

    layer_frames = {"rule": rule_df, "physics": physics_df, "neighbor": neighbor_df, "ml": ml_df}
    all_keys = set()
    for df in layer_frames.values():
        if "match_key" in df.columns:
            all_keys.update(df["match_key"].tolist())

    results = []
    for key in all_keys:
        station_id, ts_str = key.split("_", 1)

        hit = {name: ("match_key" in df.columns and key in df["match_key"].values)
               for name, df in layer_frames.items()}
        layers_agreeing = sum(hit.values())
        confidence = round((layers_agreeing / len(layer_frames)) * 100)

        if hit["rule"]:
            rule_row = rule_df[rule_df["match_key"] == key].iloc[0]
            attribution = "Silent station" if "Silent" in str(rule_row.get("flag_type", "")) else "Sensor fault"
        elif hit["physics"]:
            attribution = "Physics violation (sensor inconsistency)"
        elif hit["neighbor"]:
            attribution = "Possible tampering"
        elif hit["ml"]:
            attribution = "ML-detected anomaly (needs review)"
        else:
            attribution = "Unknown"

        corrected_value = None
        if hit["neighbor"]:
            nrow = neighbor_df[neighbor_df["match_key"] == key].iloc[0]
            corrected_value = nrow.get("corrected_value")

        results.append({
            "station_id": station_id, "timestamp": ts_str, "attribution": attribution,
            "flagged_by_rule": hit["rule"], "flagged_by_physics": hit["physics"],
            "flagged_by_neighbor": hit["neighbor"], "flagged_by_ml": hit["ml"],
            "confidence_%": confidence, "trust_state": _trust_state(confidence, attribution),
            "alert_priority": _alert_priority(confidence),
            "corrected_value": corrected_value,
        })

    if not results:
        return pd.DataFrame(columns=["station_id", "timestamp", "attribution", "confidence_%",
                                      "trust_state", "alert_priority", "corrected_value"])
    return pd.DataFrame(results).sort_values(["confidence_%", "station_id"], ascending=[False, True])


def compute_recall(final_df: pd.DataFrame, known_anomaly_stations: set) -> dict:
    """Honest accuracy on our synthetic test set - no fake precision claims."""
    detected_stations = set(final_df["station_id"].unique())
    true_positives = len(known_anomaly_stations & detected_stations)
    recall = true_positives / len(known_anomaly_stations) if known_anomaly_stations else 0
    return {
        "known_injected_anomaly_stations": sorted(known_anomaly_stations),
        "detected_stations": sorted(detected_stations),
        "recall_on_synthetic_test_%": round(recall * 100, 1),
        "note": "Precision requires real IMD ground-truth fault records to compute honestly; "
                "this recall figure is measured only against our own injected synthetic faults.",
    }
