from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from .session import Base

class Station(Base):
    __tablename__ = "stations"
    id = Column(String, primary_key=True, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    name = Column(String, nullable=True)
    status = Column(String, default="healthy") # healthy, warning, critical, offline
    health_score = Column(Integer, default=100)

class Reading(Base):
    __tablename__ = "readings"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    station_id = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    
    # Core
    temperature = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    
    # Optional
    rainfall = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)
    wind_direction = Column(Float, nullable=True)
    solar_radiation = Column(Float, nullable=True)
    cloud_cover = Column(Float, nullable=True)

class Anomaly(Base):
    __tablename__ = "anomalies"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    station_id = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    parameter = Column(String, index=True) # temperature, pressure, humidity, multivariate
    observed_value = Column(Float, nullable=True)
    expected_value = Column(Float, nullable=True)
    deviation = Column(Float, nullable=True)
    severity = Column(String, index=True) # NORMAL, LOW, MEDIUM, HIGH, CRITICAL
    evidence_score = Column(Integer, default=0) # 0-100
    trust_state = Column(String) # ACCEPT, CAUTION, QUARANTINE, REJECT
    attribution = Column(String) # Sensor fault, etc.
    explanation = Column(String)
    corrected_value = Column(Float, nullable=True)
    status = Column(String, default="active") # active, resolved, acknowledged

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    anomaly_id = Column(Integer, index=True)
    station_id = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    severity = Column(String)
    message = Column(String)
    status = Column(String, default="unresolved") # unresolved, acknowledged, resolved

class HealthHistory(Base):
    __tablename__ = "health_history"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    station_id = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    health_score = Column(Integer)
    anomaly_frequency = Column(Float)
    data_completeness = Column(Float)
    sensor_variance = Column(Float)
    communication_reliability = Column(Float)
