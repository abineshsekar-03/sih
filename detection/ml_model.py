import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
import pandas as pd
from sklearn.ensemble import IsolationForest
import config
from detection.physics import add_derived_features

MODEL_TRAINED_DATE = '2026-09-03'

def check_retrain_needed(trained_date_str=MODEL_TRAINED_DATE, interval_days=config.RETRAIN_INTERVAL_DAYS):
    trained_date = datetime.strptime(trained_date_str, '%Y-%m-%d')
    days_old = (datetime.now() - trained_date).days
    overdue = days_old > interval_days
    return overdue, f'Model is {days_old} days old ' + ('- RETRAIN RECOMMENDED' if overdue else f'(within {interval_days}-day window)')

def build_features(df):
    df = add_derived_features(df)
    cols = ['temperature','rainfall','humidity','wind_speed','wind_direction','pressure','solar_radiation','cloud_cover','dew_point','temperature_deviation','humidity_deviation','pressure_deviation','wind_speed_deviation','rainfall_rolling_6h','wind_direction_change']
    return df, cols

def run(df, region='default'):
    df, feature_cols = build_features(df)
    model = IsolationForest(n_estimators=200, contamination=config.get_contamination(region), random_state=config.ML_RANDOM_STATE)
    X = df[feature_cols].replace([float('inf'), float('-inf')], pd.NA).fillna(0)
    df['ml_prediction'] = model.fit_predict(X)
    df['ml_anomaly_score'] = model.decision_function(X)
    anomalies = df[df['ml_prediction'] == -1].copy()
    anomalies['flag_type'] = 'ML-detected anomaly (Isolation Forest)'
    anomalies['reason'] = "Unusual combination of weather readings vs the station's recent pattern"
    return anomalies[['station_id','timestamp','flag_type','reason','ml_anomaly_score']]
