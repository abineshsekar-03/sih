import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import asyncio

from backend.database.session import engine, Base, SessionLocal
from backend.database.models import Station
from backend.api.routes import router as api_router, sse_queues

# Initialize DB
Base.metadata.create_all(bind=engine)

# Seed stations if empty
def seed_stations():
    db = SessionLocal()
    if db.query(Station).count() == 0:
        stations = [
            {"id": "ST01", "lat": 28.61, "lon": 77.20, "name": "Delhi"},
            {"id": "ST02", "lat": 19.07, "lon": 72.87, "name": "Mumbai"},
            {"id": "ST03", "lat": 13.08, "lon": 80.27, "name": "Chennai"},
            {"id": "ST04", "lat": 12.97, "lon": 77.59, "name": "Bengaluru"},
            {"id": "ST05", "lat": 22.57, "lon": 88.36, "name": "Kolkata"},
            {"id": "ST06", "lat": 23.03, "lon": 72.58, "name": "Ahmedabad"},
            {"id": "ST07", "lat": 26.85, "lon": 80.95, "name": "Lucknow"},
            {"id": "ST08", "lat": 17.38, "lon": 78.49, "name": "Hyderabad"},
            {"id": "ST09", "lat": 15.30, "lon": 74.12, "name": "Belagavi"},
            {"id": "ST10", "lat": 30.74, "lon": 76.78, "name": "Chandigarh"}
        ]
        for s in stations:
            db.add(Station(**s))
        db.commit()
    db.close()

seed_stations()

app = FastAPI(title="SIH26073 - Atmos-X API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

from fastapi.staticfiles import StaticFiles
import os

@app.get("/api/live-feed")
async def live_feed(request: Request):
    q = asyncio.Queue()
    sse_queues.append(q)
    
    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                message = await q.get()
                yield message
        except asyncio.CancelledError:
            pass
        finally:
            if q in sse_queues:
                sse_queues.remove(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Mount frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    print(f"Warning: Frontend build directory not found at {frontend_dir}")

if __name__ == "__main__":
    print("Starting backend API on port 8000...")
    uvicorn.run("backend.main_api:app", host="0.0.0.0", port=8000, reload=True)
