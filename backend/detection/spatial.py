import math
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.database.models import Reading, Station
from datetime import datetime, timedelta

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    return 2 * R * math.asin(math.sqrt(a))

def run_spatial(reading_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Evaluates spatial consistency (vs neighbors) of a single reading.
    Returns:
        evidence_score: 0 to 15
        reason: Text description if anomalous
        expected_value: Estimated value from neighbors
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

    # Get this station's coordinates
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        return {"evidence_score": 0, "reason": "Unknown station", "severity_hint": "NORMAL"}

    # Find 3 nearest neighbors
    all_stations = db.query(Station).filter(Station.id != station_id).all()
    neighbors = []
    for s in all_stations:
        dist = haversine_km(station.lat, station.lon, s.lat, s.lon)
        neighbors.append((dist, s.id))
    neighbors.sort()
    top_neighbors = [n[1] for n in neighbors[:3]]

    if not top_neighbors:
        return {"evidence_score": 0, "reason": "No neighbors", "severity_hint": "NORMAL"}

    # Get recent readings from neighbors (last 1 hour)
    cutoff = ts - timedelta(hours=1)
    neighbor_readings = db.query(Reading).filter(
        Reading.station_id.in_(top_neighbors),
        Reading.timestamp >= cutoff,
        Reading.timestamp <= ts + timedelta(minutes=10) # allow slight future overlap in demo
    ).all()

    nbr_temps = [r.temperature for r in neighbor_readings if r.temperature is not None]
    
    if len(nbr_temps) == 0:
        return {"evidence_score": 0, "reason": "No recent neighbor data", "severity_hint": "NORMAL"}
        
    avg_nbr_temp = sum(nbr_temps) / len(nbr_temps)
    
    # Calculate deviation
    deviation = abs(temp - avg_nbr_temp)
    
    evidence = 0
    reasons = []
    
    if deviation > 4.0: # 4 degrees diff from neighbors is suspicious
        reasons.append(f"Temperature ({temp}°C) deviates from spatial neighbors (avg {avg_nbr_temp:.1f}°C)")
        evidence = min(15, int(deviation * 2))
        
    return {
        "evidence_score": evidence,
        "reason": "; ".join(reasons) if reasons else "Normal",
        "severity_hint": "HIGH" if evidence > 10 else "NORMAL",
        "expected_value": avg_nbr_temp
    }
