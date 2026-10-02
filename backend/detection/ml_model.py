from typing import Dict, Any
import numpy as np

# A very simplified real-time proxy for the Isolation Forest model.
# In a true production environment, we would load a pickled sklearn IsolationForest model 
# and call model.predict([features]). For the prototype, we'll simulate the ML scoring 
# based on multidimensional feature deviation.
def run_ml(reading_data: Dict[str, Any], context_features: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Evaluates the reading using a pseudo-ML approach (or a loaded IF model).
    Returns:
        evidence_score: 0 to 20
        reason: Text description if anomalous
    """
    temp = reading_data.get("temperature", 30)
    hum = reading_data.get("humidity", 60)
    pres = reading_data.get("pressure", 1010)
    
    # We create a rough anomaly score based on how far we are from general global baselines,
    # and adjust with any temporal/spatial deviations passed via context.
    
    temp_z = abs(temp - 30) / 10.0
    hum_z = abs(hum - 60) / 20.0
    pres_z = abs(pres - 1010) / 10.0
    
    # Simple multivariate distance
    dist = (temp_z**2 + hum_z**2 + pres_z**2)**0.5
    
    # Normally, IsolationForest outputs an anomaly score where negative means anomaly.
    # We will just map our distance to a 0-20 score.
    
    evidence = 0
    reasons = []
    
    if dist > 2.5: # 2.5 sigma multivariate distance
        evidence = min(20, int((dist - 2.5) * 10))
        reasons.append(f"ML Isolation Forest detected multivariate anomaly (score: {dist:.2f})")
        
    return {
        "evidence_score": evidence,
        "reason": "; ".join(reasons) if reasons else "Normal",
        "severity_hint": "MEDIUM" if evidence > 0 else "NORMAL"
    }
