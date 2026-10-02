from typing import Dict, Any, Optional
import backend.config as config
from sqlalchemy.orm import Session
from backend.database.models import Reading

def run_rules(reading_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Evaluates rule-based limits on a single reading.
    Returns:
        evidence_score: 0 to 25
        reason: Text description if anomalous
    """
    reasons = []
    
    # Range checks
    temp = reading_data.get("temperature")
    if temp is not None and not (config.TEMP_MIN <= temp <= config.TEMP_MAX):
        reasons.append(f"Temperature {temp}°C out of realistic range")
        
    hum = reading_data.get("humidity")
    if hum is not None and not (config.HUMIDITY_MIN <= hum <= config.HUMIDITY_MAX):
        reasons.append(f"Humidity {hum}% out of realistic range")
        
    pres = reading_data.get("pressure")
    if pres is not None and not (config.PRESSURE_MIN <= pres <= config.PRESSURE_MAX):
        reasons.append(f"Pressure {pres} hPa out of realistic range")

    # Check for flatline (compare with last N readings)
    station_id = reading_data.get("station_id")
    if temp is not None:
        last_readings = db.query(Reading).filter(Reading.station_id == station_id).order_by(Reading.timestamp.desc()).limit(config.FLATLINE_COUNT).all()
        if len(last_readings) == config.FLATLINE_COUNT:
            if all(r.temperature == temp for r in last_readings):
                reasons.append(f"Temperature stuck at {temp}°C for {config.FLATLINE_COUNT} consecutive readings")

    evidence = 0
    if reasons:
        evidence = 25 # Maximum evidence for rule violation (it's deterministic)

    return {
        "evidence_score": evidence,
        "reason": "; ".join(reasons) if reasons else "Normal",
        "severity_hint": "CRITICAL" if len(reasons) > 0 else "NORMAL"
    }
