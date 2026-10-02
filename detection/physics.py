import numpy as np
import pandas as pd

def estimate_dew_point(temp_c, humidity_pct):
    if pd.isna(temp_c) or pd.isna(humidity_pct):
        return np.nan
    rh = float(np.clip(humidity_pct, 1, 100))
    t = float(temp_c)
    gamma = np.log(rh / 100.0) + (17.62 * t) / (243.12 + t)
    return (243.12 * gamma) / (17.62 - gamma)

def add_derived_features(df):
    df = df.copy()
    df['dew_point'] = [estimate_dew_point(t, h) for t, h in zip(df['temperature'], df['humidity'])]
    df = df.sort_values(['station_id', 'timestamp']).copy()
    for col in ['temperature', 'humidity', 'pressure', 'wind_speed']:
        rolling = df.groupby('station_id')[col].transform(lambda x: x.rolling(24, min_periods=1).mean())
        df[f'{col}_deviation'] = df[col] - rolling
    df['rainfall_rolling_6h'] = df.groupby('station_id')['rainfall'].transform(lambda x: x.rolling(6, min_periods=1).mean())
    df['wind_direction_change'] = df.groupby('station_id')['wind_direction'].transform(lambda x: x.diff().abs().fillna(0))
    return df

def run(df):
    flags = []
    work = add_derived_features(df)
    for _, row in work.iterrows():
        dp = row['dew_point']
        if pd.notna(dp) and dp > row['temperature'] + 0.5:
            flags.append({'station_id': row['station_id'], 'timestamp': row['timestamp'], 'flag_type': 'Physics violation', 'reason': f'Calculated dew point ({dp:.1f}C) exceeds air temperature ({row["temperature"]}C) - temp or humidity sensor is faulty'})
    return pd.DataFrame(flags)
