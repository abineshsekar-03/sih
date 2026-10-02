from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.database.models import Reading
from datetime import datetime, timedelta

def run_temporal(reading_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Evaluates temporal consistency (short-term deviation from baseline) of a single reading.
    Returns:
        evidence_score: 0 to 20
        reason: Text description if anomalous
    """
    station_id = reading_data.get("station_id")
    temp = reading_data.get("temperature")
    ts_str = reading_data.get("timestamp")
    
    if not station_id or temp is None or not ts_str:
        return {"evidence_score": 0, "reason": "Normal", "severity_hint": "NORMAL"}
        
    try:
        if isinstance(ts_str, str):
            ts = datetime.fromisoformat(ts_str)
        else:
            ts = ts_str
    except Exception:
        ts = datetime.utcnow()

    # Get readings from the last 6 hours
    cutoff = ts - timedelta(hours=6)
    history = db.query(Reading).filter(
        Reading.station_id == station_id,
        Reading.timestamp >= cutoff,
        Reading.timestamp < ts
    ).all()
    
    if len(history) < 3:
        return {"evidence_score": 0, "reason": "Insufficient history", "severity_hint": "NORMAL"}
        
    # Calculate baseline
    temps = [r.temperature for r in history if r.temperature is not None]
    if not temps:
        return {"evidence_score": 0, "reason": "Normal", "severity_hint": "NORMAL"}
        
    mean_temp = sum(temps) / len(temps)
    variance = sum((x - mean_temp) ** 2 for x in temps) / len(temps)
    std_temp = variance ** 0.5
    
    # If the standard deviation is very low, we still need some margin
    margin = max(std_temp * 3, 2.0)
    
    deviation = abs(temp - mean_temp)
    
    evidence = 0
    reasons = []
    if deviation > margin:
        reasons.append(f"Temperature deviation of {deviation:.1f}°C from 6h baseline (mean: {mean_temp:.1f}°C)")
        evidence = min(20, int((deviation / margin) * 10))
        
    return {
        "evidence_score": evidence,
        "reason": "; ".join(reasons) if reasons else "Normal",
        "severity_hint": "MEDIUM" if evidence > 0 else "NORMAL"
    }
