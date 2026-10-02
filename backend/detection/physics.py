import math
from typing import Dict, Any

def estimate_dew_point(temp_c: float, humidity_pct: float) -> float:
    if temp_c is None or humidity_pct is None:
        return None
    try:
        rh = max(1.0, min(100.0, float(humidity_pct)))
        t = float(temp_c)
        gamma = math.log(rh / 100.0) + (17.62 * t) / (243.12 + t)
        return (243.12 * gamma) / (17.62 - gamma)
    except Exception:
        return None

def run_physics(reading_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates physical consistency of a single reading.
    Returns:
        evidence_score: 0 to 20
        reason: Text description if anomalous
    """
    temp = reading_data.get("temperature")
    hum = reading_data.get("humidity")
    
    reasons = []
    evidence = 0
    
    dp = estimate_dew_point(temp, hum)
    if dp is not None and temp is not None:
        if dp > temp + 0.5:
            reasons.append(f"Dew point ({dp:.1f}°C) exceeds air temperature ({temp}°C) by >0.5C. Sensor inconsistency.")
            evidence = 20

    # We could add more checks here (e.g., pressure vs altitude if we knew it, or temp/rh rapid changes)

    return {
        "evidence_score": evidence,
        "reason": "; ".join(reasons) if reasons else "Normal",
        "severity_hint": "HIGH" if evidence > 0 else "NORMAL"
    }
