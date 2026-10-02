# SIH26073 - ATMOS-X
## AI-Powered Automated Quality Control & Anomaly Detection for AWS

ATMOS-X is a Level-3+ Hackathon Prototype that acts as an intelligence command center for Automatic Weather Stations (AWS). It ingests real-time weather streams (Temperature, Pressure, Relative Humidity) and performs real-time multi-layered quality control to detect sensor faults, plausible spatial deviations, and data integrity problems.

### Architecture

The system replaces traditional batch-pipeline architectures with an event-driven realtime stream:
- **FastAPI / SQLite Backend:** Ingests live data via `POST /api/readings` and computes detection scores immediately.
- **5-Layer Detection Engine:** 
  1. Rules (Range and basic constraints)
  2. Physics (Dew point verification between Temperature and Humidity)
  3. Temporal (Deviation from recent hourly baselines)
  4. Spatial (Deviation from nearest geographic neighbors)
  5. ML (Isolation Forest multivariate detection)
- **Fusion Engine:** Translates the outputs of the 5 layers into a single 0-100 `Evidence Agreement Score`, calculates a severity level, and issues a Trust State (ACCEPT, CAUTION, QUARANTINE, REJECT).
- **Vite/React Dashboard:** A premium, live-updating mission control UI using Server-Sent Events (SSE).

### Demo Instructions

A live demo mode is built directly into the UI!
1. Start the stack (see below).
2. Open the frontend at `http://localhost:5173`.
3. In the left sidebar under "Demo Simulator", click **Play**.
4. The dashboard will populate with stations and live graphs.
5. In the simulator dropdown, select "Temperature Spike (ST07)" and click **Inject Anomaly**.
6. Switch to the **Live Monitor** or watch the **Overview** page to see the anomaly detected in real-time.
7. Click the anomaly in the list to open the detailed **Anomaly Drawer** which explains why it was flagged and what action to take.

### Installation & Running

1. **Install Python dependencies:**
   `pip install -r requirements.txt`
2. **Install Node dependencies:**
   `cd frontend && npm install`

**Quick Start:**
On Windows, you can simply run:
`start.bat`
This will automatically launch the FastAPI backend and the Vite frontend.

### Testing & Verification
You can run the built-in system verification:
`python system_check.py`

### Explainability and Honesty
- We explicitly distinguish between controlled synthetic benchmarks and real-world precision.
- The UI surfaces exactly *why* a reading was quarantined through an Evidence Chain (Rule, Physics, Temporal, Spatial, ML), ensuring that meteorologists understand the AI's reasoning.
