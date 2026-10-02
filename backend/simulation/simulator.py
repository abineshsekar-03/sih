import asyncio
import random
import requests
from datetime import datetime, timedelta

# Default base configurations for simulation
BASE_URL = "http://localhost:8000/api"

STATIONS = ["ST01", "ST02", "ST03", "ST04", "ST05", "ST06", "ST07", "ST08", "ST09", "ST10"]

class Simulator:
    def __init__(self):
        self.running = False
        self.task = None
        self.interval = 2.0  # seconds between ticks
        self.current_time = datetime.utcnow()
        self.scenario = "NORMAL"

    def generate_reading(self, station_id: str):
        # Base realistic values
        base_temp = 30.0 + random.uniform(-2, 2)
        base_hum = 60.0 + random.uniform(-5, 5)
        base_pres = 1010.0 + random.uniform(-1, 1)

        reading = {
            "station_id": station_id,
            "timestamp": self.current_time.isoformat(),
            "temperature": round(base_temp, 1),
            "humidity": round(base_hum, 1),
            "pressure": round(base_pres, 1)
        }

        # Apply active scenario if it matches this tick/station
        if self.scenario == "TEMPERATURE_SPIKE" and station_id == "ST07":
            reading["temperature"] = 61.2
            self.scenario = "NORMAL" # one-time injection
        elif self.scenario == "HUMIDITY_FAULT" and station_id == "ST05":
            reading["humidity"] = -10.0
            self.scenario = "NORMAL"
        elif self.scenario == "PRESSURE_DRIFT" and station_id == "ST09":
            reading["pressure"] = 800.0
            self.scenario = "NORMAL"
        elif self.scenario == "FLATLINE" and station_id == "ST02":
            reading["temperature"] = 29.4
            # doesn't reset, stays flatlined until scenario changes manually
        elif self.scenario == "SPATIAL_OUTLIER" and station_id == "ST04":
            reading["temperature"] = 45.0
            self.scenario = "NORMAL"

        return reading

    async def _run_loop(self):
        while self.running:
            self.current_time += timedelta(minutes=10) # 10 mins simulator time per tick
            for station in STATIONS:
                # If silent scenario, skip ST03
                if self.scenario == "SILENT" and station == "ST03":
                    continue
                reading = self.generate_reading(station)
                try:
                    requests.post(f"{BASE_URL}/readings", json=reading, timeout=1)
                except Exception as e:
                    print(f"Simulation post failed: {e}")
            await asyncio.sleep(self.interval)

    def start(self):
        if not self.running:
            self.running = True
            self.task = asyncio.create_task(self._run_loop())
            return {"status": "started"}
        return {"status": "already running"}

    def pause(self):
        self.running = False
        if self.task:
            self.task.cancel()
            self.task = None
        return {"status": "paused"}

    def reset(self):
        self.pause()
        self.current_time = datetime.utcnow()
        self.scenario = "NORMAL"
        # In a full system, you might want to truncate tables via a dedicated route here
        return {"status": "reset"}

    def inject_scenario(self, scenario: str):
        self.scenario = scenario
        return {"status": f"injected {scenario}"}

simulator_instance = Simulator()
