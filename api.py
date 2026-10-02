"""
api.py - Backend API server for the Dashboard.

Serves the pipeline's CSV outputs (final_report.csv, health_scores.csv)
as JSON over HTTP, and handles login + role-based filtering, so the
dashboard (static/dashboard.html) is a real "live" frontend instead of
a static file viewer.

Run: python api.py
Then open http://localhost:8000 in a browser.

Requires main.py to have been run at least once (so final_report.csv,
health_scores.csv exist).
"""

import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

import notifications  # reuses the same USERS list + station-region mapping

app = FastAPI(title="SIH26073 AWS Anomaly Detection API")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple demo credentials - maps to notifications.USERS by role.
# In production this would be a real user database with hashed passwords.
DEMO_LOGINS = {
    "admin": {"password": "admin123", "role": "admin", "name": "DDG Delhi"},
    "operator": {"password": "operator123", "role": "regional_operator", "name": "Met Officer Chennai", "region": "south"},
    "technician": {"password": "tech123", "role": "field_technician", "name": "Field Tech Team"},
    "forecaster": {"password": "forecast123", "role": "forecaster", "name": "Forecaster Delhi"},
    "viewer": {"password": "viewer123", "role": "viewer", "name": "Public Viewer"},
}


class LoginRequest(BaseModel):
    username: str
    password: str


def _load_csv(filename: str) -> pd.DataFrame:
    path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    # Force object dtype before replacing NaN with None - pandas silently
    # reverts None back to NaN on float-typed columns otherwise, which
    # crashes FastAPI's JSON encoder ("Out of range float values...").
    df = df.astype(object).where(pd.notna(df), None)
    return df


def _filter_for_role(df: pd.DataFrame, role: str, region: str = None) -> pd.DataFrame:
    """Same routing logic as notifications.py, reused here so the
    dashboard shows each role exactly what they'd be emailed about."""
    if df.empty or role == "admin":
        return df
    if role == "regional_operator":
        region_stations = [s for s, r in notifications.STATION_REGION.items() if r == region]
        return df[df["station_id"].isin(region_stations)]
    if role == "field_technician":
        return df[df["attribution"].isin(notifications.MAINTENANCE_ATTRIBUTIONS)]
    if role == "forecaster":
        return df[df["attribution"].isin(notifications.WEATHER_ATTRIBUTIONS)]
    return df.iloc[0:0]  # viewer: no anomaly details, dashboard summary only


@app.post("/api/login")
def login(req: LoginRequest):
    user = DEMO_LOGINS.get(req.username)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {
        "username": req.username,
        "name": user["name"],
        "role": user["role"],
        "region": user.get("region"),
    }


@app.get("/api/anomalies")
def get_anomalies(role: str = "admin", region: str = None):
    df = _load_csv("final_report.csv")
    df = _filter_for_role(df, role, region)
    return df.to_dict(orient="records")


@app.get("/api/health-scores")
def get_health_scores():
    df = _load_csv("health_scores.csv")
    return df.to_dict(orient="records")


@app.get("/api/system-status")
def get_system_status():
    """Powers the small green/red 'system health' indicator in the header."""
    checks = {
        "aws_data.csv": os.path.exists(os.path.join(BASE_DIR, "aws_data.csv")),
        "final_report.csv": os.path.exists(os.path.join(BASE_DIR, "final_report.csv")),
        "health_scores.csv": os.path.exists(os.path.join(BASE_DIR, "health_scores.csv")),
    }
    all_ok = all(checks.values())
    return {"status": "ok" if all_ok else "incomplete", "checks": checks}


@app.get("/api/comparison")
def get_comparison():
    """Namma-vs-existing-systems data for the About/Research tab."""
    path = os.path.join(BASE_DIR, "comparison_data.json")
    if not os.path.exists(path):
        return {"error": "comparison_data.json not found"}
    import json
    with open(path) as f:
        return json.load(f)


# Serve the dashboard itself at the root URL
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    print("Starting dashboard server...")
    print("Open this in your browser: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
