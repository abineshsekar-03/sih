from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import json
import asyncio
from pydantic import BaseModel

from backend.database.session import get_db
from backend.database.models import Reading, Anomaly, Station, Alert, HealthHistory
from backend.api.schemas import ReadingCreate, LoginRequest, AlertActionRequest
from backend.detection import rules, physics, temporal, spatial, ml_model
from backend.fusion import fuse_evidence
from backend.simulation.simulator import simulator_instance

router = APIRouter()

# Global list of queues for SSE clients
sse_queues = []

# Simulator endpoints
@router.post("/simulation/start")
def sim_start():
    return simulator_instance.start()

@router.get("/simulation/status")
def sim_status():
    return {
        "running": simulator_instance.running,
        "scenario": simulator_instance.scenario
    }

@router.post("/simulation/pause")
def sim_pause():
    return simulator_instance.pause()

@router.post("/simulation/reset")
def sim_reset(db: Session = Depends(get_db)):
    res = simulator_instance.reset()
    # Clear history for clean demo
    db.query(Alert).delete()
    db.query(Anomaly).delete()
    db.query(Reading).delete()
    db.commit()
    return res

class InjectRequest(BaseModel):
    scenario: str

@router.post("/simulation/inject")
def sim_inject(req: InjectRequest):
    return simulator_instance.inject_scenario(req.scenario)


async def notify_clients(event_type: str, data: dict):
    message = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    for q in sse_queues:
        await q.put(message)

def process_reading_background(reading_data: dict, db: Session):
    # Detection Layers
    rule_res = rules.run_rules(reading_data, db)
    physics_res = physics.run_physics(reading_data)
    temporal_res = temporal.run_temporal(reading_data, db)
    spatial_res = spatial.run_spatial(reading_data, db)
    ml_res = ml_model.run_ml(reading_data)

    # Fusion
    fusion_res = fuse_evidence(rule_res, physics_res, temporal_res, spatial_res, ml_res)
    
    # Store reading
    ts = reading_data.get("timestamp")
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)
    elif not ts:
        ts = datetime.utcnow()
        reading_data["timestamp"] = ts
        
    new_reading = Reading(
        station_id=reading_data["station_id"],
        timestamp=ts,
        temperature=reading_data.get("temperature"),
        pressure=reading_data.get("pressure"),
        humidity=reading_data.get("humidity"),
        rainfall=reading_data.get("rainfall"),
        wind_speed=reading_data.get("wind_speed"),
        wind_direction=reading_data.get("wind_direction"),
        solar_radiation=reading_data.get("solar_radiation"),
        cloud_cover=reading_data.get("cloud_cover")
    )
    db.add(new_reading)
    db.commit()

    # Update Station status based on fusion
    station = db.query(Station).filter(Station.id == reading_data["station_id"]).first()
    if station:
        if fusion_res["severity"] == "CRITICAL":
            station.status = "critical"
            station.health_score = max(0, station.health_score - 10)
        elif fusion_res["severity"] == "HIGH":
            station.status = "warning"
            station.health_score = max(0, station.health_score - 5)
        elif fusion_res["severity"] == "NORMAL":
            station.status = "healthy"
            station.health_score = min(100, station.health_score + 1)
        db.commit()

    # If anomaly, create Anomaly and Alert
    anomaly = None
    if fusion_res["is_anomaly"]:
        anomaly = Anomaly(
            station_id=reading_data["station_id"],
            timestamp=ts,
            parameter="multivariate" if fusion_res["attribution"] == "Multivariate Anomaly" else "temperature", # simplified for demo
            observed_value=reading_data.get("temperature"),
            expected_value=fusion_res.get("expected_value"),
            deviation=None,
            severity=fusion_res["severity"],
            evidence_score=fusion_res["evidence_score"],
            trust_state=fusion_res["trust_state"],
            attribution=fusion_res["attribution"],
            explanation=fusion_res["explanation"],
            corrected_value=fusion_res.get("expected_value")
        )
        db.add(anomaly)
        db.commit()
        db.refresh(anomaly)
        
        # Create Alert if high enough
        if fusion_res["severity"] in ["CRITICAL", "HIGH", "MEDIUM"]:
            alert = Alert(
                anomaly_id=anomaly.id,
                station_id=reading_data["station_id"],
                timestamp=ts,
                severity=fusion_res["severity"],
                message=f"{fusion_res['attribution']} detected at {reading_data['station_id']}"
            )
            db.add(alert)
            db.commit()

    # Notify frontend via SSE
    payload = {
        "reading": {
            "station_id": reading_data["station_id"],
            "timestamp": ts.isoformat(),
            "temperature": reading_data.get("temperature"),
            "pressure": reading_data.get("pressure"),
            "humidity": reading_data.get("humidity")
        },
        "anomaly": None,
        "station_status": station.status if station else "healthy",
        "station_health": station.health_score if station else 100
    }
    
    if anomaly:
        payload["anomaly"] = {
            "id": anomaly.id,
            "severity": anomaly.severity,
            "trust_state": anomaly.trust_state,
            "evidence_score": anomaly.evidence_score,
            "explanation": anomaly.explanation
        }
        
    asyncio.run(notify_clients("reading", payload))


@router.post("/readings")
def receive_reading(reading: ReadingCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    reading_dict = reading.dict()
    if not reading_dict.get("timestamp"):
        reading_dict["timestamp"] = datetime.utcnow()
    background_tasks.add_task(process_reading_background, reading_dict, db)
    return {"status": "accepted"}

@router.get("/readings")
def get_readings(limit: int = 100, db: Session = Depends(get_db)):
    # Group by timestamp (or just get latest readings)
    # We want to return a time series of average or ST07 specifically, or all.
    # To keep it simple, return latest 100 readings across stations, ordered by time.
    readings = db.query(Reading).order_by(Reading.timestamp.desc()).limit(limit).all()
    # Reverse so they are chronological
    return [
        {
            "station_id": r.station_id,
            "timestamp": r.timestamp.isoformat(),
            "temperature": r.temperature,
            "pressure": r.pressure,
            "humidity": r.humidity
        }
        for r in reversed(readings)
    ]

@router.get("/stations")
def get_stations(db: Session = Depends(get_db)):
    stations = db.query(Station).all()
    return [{"id": s.id, "lat": s.lat, "lon": s.lon, "name": s.name, "status": s.status, "health_score": s.health_score} for s in stations]

@router.get("/anomalies")
def get_anomalies(db: Session = Depends(get_db)):
    anomalies = db.query(Anomaly).order_by(Anomaly.timestamp.desc()).limit(100).all()
    res = []
    for a in anomalies:
        res.append({
            "id": a.id, "station_id": a.station_id, "timestamp": a.timestamp.isoformat(),
            "parameter": a.parameter, "observed_value": a.observed_value,
            "expected_value": a.expected_value, "severity": a.severity,
            "evidence_score": a.evidence_score, "trust_state": a.trust_state,
            "attribution": a.attribution, "explanation": a.explanation,
            "status": a.status
        })
    return res

@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db)):
    alerts = db.query(Alert).order_by(Alert.timestamp.desc()).limit(50).all()
    return [{"id": a.id, "station_id": a.station_id, "timestamp": a.timestamp.isoformat(), "severity": a.severity, "message": a.message, "status": a.status} for a in alerts]

@router.post("/login")
def login(req: LoginRequest):
    # Dummy login for hackathon
    if req.password.endswith("123"):
        return {"username": req.username, "role": "admin" if req.username == "admin" else "viewer", "token": "demo-token"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.get("/system-status")
def system_status():
    return {
        "API": "ONLINE",
        "Database": "ONLINE",
        "Detection Engine": "ONLINE",
        "ML Model": "READY",
        "Data Stream": "LIVE"
    }
