import os

# Thresholds for Range Checks
TEMP_MIN = -10.0
TEMP_MAX = 55.0
HUMIDITY_MIN = 0.0
HUMIDITY_MAX = 100.0
PRESSURE_MIN = 850.0
PRESSURE_MAX = 1080.0

# Temporal / Flatline config
FLATLINE_COUNT = 5  # number of identical consecutive readings to trigger flatline
SILENT_GAP_MINUTES = 60 # wait time before alerting silent station

# Trust & Alert Config
TRUST_QUARANTINE_CONFIDENCE = 75
TRUST_CAUTION_CONFIDENCE = 50

ALERT_CRITICAL_CONFIDENCE = 80
ALERT_MEDIUM_CONFIDENCE = 60

ML_RANDOM_STATE = 42

def seasonal_rain_threshold(month: int) -> float:
    # Example logic: higher threshold in monsoon months (June-Sept in India)
    if 6 <= month <= 9:
        return 250.0
    return 100.0

def get_contamination(region: str) -> float:
    return 0.05
