"""Riegel's formula for race time prediction."""


def predict_time_riegel(current_distance: float, current_time: float, target_distance: float) -> float:
    """
    Predict race time using Riegel's formula.
    
    Riegel's formula: T2 = T1 * (D2/D1)^1.06
    
    Args:
        current_distance: Distance of known performance in meters.
        current_time: Time of known performance in seconds.
        target_distance: Distance for race time prediction in meters.
        
    Returns:
        float: Predicted time in seconds.
    """
    riegel_exponent = 1.06
    return current_time * ((target_distance / current_distance) ** riegel_exponent)
