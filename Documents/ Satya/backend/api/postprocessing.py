# Formatting results for frontend
def format_confidence(score: float) -> str:
    return f"{score * 100:.1f}%"

def get_risk_level(score: float) -> str:
    if score > 0.8:
        return "HIGH"
    elif score > 0.5:
        return "MEDIUM"
    else:
        return "LOW"
