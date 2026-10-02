from typing import Dict, Any

def get_severity(evidence_score: int) -> str:
    if evidence_score >= 80:
        return "CRITICAL"
    elif evidence_score >= 60:
        return "HIGH"
    elif evidence_score >= 40:
        return "MEDIUM"
    elif evidence_score >= 20:
        return "LOW"
    return "NORMAL"

def get_trust_state(severity: str) -> str:
    if severity == "CRITICAL":
        return "REJECT"
    elif severity == "HIGH":
        return "QUARANTINE"
    elif severity in ["MEDIUM", "LOW"]:
        return "CAUTION"
    return "ACCEPT"

def fuse_evidence(
    rule_res: Dict[str, Any],
    physics_res: Dict[str, Any],
    temporal_res: Dict[str, Any],
    spatial_res: Dict[str, Any],
    ml_res: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Fuses the evidence from 5 detection layers into a single score and verdict.
    """
    
    # Calculate Evidence Score (0-100)
    rule_score = rule_res.get("evidence_score", 0) # Max 25
    physics_score = physics_res.get("evidence_score", 0) # Max 20
    temporal_score = temporal_res.get("evidence_score", 0) # Max 20
    spatial_score = spatial_res.get("evidence_score", 0) # Max 15
    ml_score = ml_res.get("evidence_score", 0) # Max 20
    
    total_score = rule_score + physics_score + temporal_score + spatial_score + ml_score
    
    severity = get_severity(total_score)
    trust = get_trust_state(severity)
    
    # Build explanation
    explanations = []
    if rule_score > 0:
        explanations.append(f"• Rule engine: {rule_res.get('reason')}")
    if physics_score > 0:
        explanations.append(f"• Physics engine: {physics_res.get('reason')}")
    if temporal_score > 0:
        explanations.append(f"• Temporal engine: {temporal_res.get('reason')}")
    if spatial_score > 0:
        explanations.append(f"• Spatial engine: {spatial_res.get('reason')}")
    if ml_score > 0:
        explanations.append(f"• ML engine: {ml_res.get('reason')}")
        
    explanation = "\n".join(explanations)
    if not explanation:
        explanation = "Reading is within normal operational parameters."
        
    # Determine attribution and expected value
    attribution = "Normal"
    if severity != "NORMAL":
        if rule_score > 0 or physics_score > 0:
            attribution = "Sensor Fault / Implausible Value"
        elif spatial_score > 10:
            attribution = "Spatial Outlier / Tampering"
        elif temporal_score > 10:
            attribution = "Sudden Drift"
        else:
            attribution = "Multivariate Anomaly"
            
    expected_value = spatial_res.get("expected_value")
    
    return {
        "evidence_score": total_score,
        "severity": severity,
        "trust_state": trust,
        "explanation": explanation,
        "attribution": attribution,
        "expected_value": expected_value,
        "is_anomaly": total_score >= 20
    }
