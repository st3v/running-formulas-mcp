"""Jack Daniels' formulas for VDOT, training paces, and race predictions."""

import math


def calculate_vdot_from_performance(distance: float, time: float) -> float:
    """
    Calculate VDOT from distance and time using Jack Daniels' formula.
    
    Args:
        distance: Distance in meters.
        time: Time in seconds.
    
    Returns:
        float: The calculated VDOT value.
    """
    t_min = time / 60
    v = distance / t_min
    vo2 = -4.6 + 0.182258 * v + 0.000104 * v * v
    vo2max = 0.8 + 0.1894393 * math.exp(-0.012778 * t_min) + 0.2989558 * math.exp(-0.1932605 * t_min)
    return vo2 / vo2max


def get_pace_velocity(vdot_val: float) -> float:
    """
    Calculate velocity from VDOT using Jack Daniels formula.
    
    Args:
        vdot_val: VDOT value.
        
    Returns:
        float: Velocity in meters per minute.
    """
    return 29.54 + 5.000663 * vdot_val - 0.007546 * (vdot_val ** 2)


def get_custom_effort_pace(vdot_val: float, distance: float, effort_percentage: float) -> float:
    """
    Calculate pace for given effort percentage.
    
    Args:
        vdot_val: VDOT value.
        distance: Distance in meters.
        effort_percentage: Effort as percentage (0.0 to 1.0).
        
    Returns:
        float: Time in minutes for the given distance.
    """
    adjusted_vdot = vdot_val * effort_percentage
    velocity = get_pace_velocity(adjusted_vdot)  # meters per minute
    pace_per_meter = 1 / velocity  # minutes per meter
    return pace_per_meter * distance  # minutes per distance


def predict_time_daniels(current_distance: float, current_time: float, target_distance: float) -> float:
    """
    Predict race time using Jack Daniels' VDOT method.
    
    Args:
        current_distance: Distance of known performance in meters.
        current_time: Time of known performance in seconds.
        target_distance: Distance for race time prediction in meters.
        
    Returns:
        float: Predicted time in seconds.
    """
    # Calculate VDOT from current performance
    vdot = calculate_vdot_from_performance(current_distance, current_time)
    
    # Calculate time for target distance using 100% effort (1.0)
    time_minutes = get_custom_effort_pace(vdot, target_distance, 1.0)
    return time_minutes * 60  # Convert minutes to seconds


def get_marathon_velocity(vdot_val: float) -> float:
    """
    Calculate marathon velocity using iterative method from Jack Daniels.
    
    Args:
        vdot_val: VDOT value.
        
    Returns:
        float: Marathon velocity in meters per minute.
    """
    marathon_distance = 42195  # meters
    time_estimate = marathon_distance / (4 * vdot_val)

    # Iterative refinement (3 iterations as in reference)
    for _ in range(3):
        exp1 = math.exp(-0.193261 * time_estimate)
        correction_factor = 0.298956 * exp1 + math.exp(-0.012778 * time_estimate) * 0.189439 + 0.8
        velocity = (vdot_val * correction_factor) ** 2 * (-0.0075) + vdot_val * correction_factor * 5.000663 + 29.54

        # Calculate derivatives for Newton's method
        d1 = 0.298956 * exp1 * 0.19326
        d2 = d1 - math.exp(-0.012778 * time_estimate) * 0.189439 * (-0.012778)
        d3 = correction_factor * d2 * vdot_val * (-0.007546) * 3
        d4 = d2 * vdot_val * 5.000663 + d3
        d5 = marathon_distance * d4 / (velocity ** 2) + 1

        delta = time_estimate - marathon_distance / velocity
        adjustment = delta / d5
        time_estimate = time_estimate - adjustment

    return marathon_distance / time_estimate


def is_slow_vdot(vdot_val: float, limit: float = 39) -> bool:
    """
    Check if VDOT is considered slow and needs adjustment.
    
    Args:
        vdot_val: VDOT value to check.
        limit: VDOT limit for slow runner adjustments.
        
    Returns:
        bool: True if VDOT is below the slow runner limit.
    """
    return 0 < vdot_val < limit


def get_slow_runner_vdot(vdot_val: float) -> float:
    """
    Get adjusted VDOT for slow runners.
    
    Args:
        vdot_val: Original VDOT value.
        
    Returns:
        float: Adjusted VDOT for slow runners.
    """
    return vdot_val * 2 / 3 + 13


def get_easy_pace(vdot_val: float, distance: float, is_slow_version: bool = False) -> float:
    """
    Calculate easy pace using Jack Daniels' methodology.
    
    Args:
        vdot_val: VDOT value.
        distance: Distance in meters.
        is_slow_version: Whether to use slower easy pace variant.
        
    Returns:
        float: Time in minutes for the given distance.
    """
    if is_slow_vdot(vdot_val):
        vdot_val = get_slow_runner_vdot(vdot_val)

    effort = 0.62 if is_slow_version else 0.7
    return get_custom_effort_pace(vdot_val, distance, effort)


def get_threshold_pace(vdot_val: float, distance: float) -> float:
    """
    Calculate threshold pace using Jack Daniels' methodology.
    
    Args:
        vdot_val: VDOT value.
        distance: Distance in meters.
        
    Returns:
        float: Time in minutes for the given distance.
    """
    if is_slow_vdot(vdot_val):
        sr_vdot = get_slow_runner_vdot(vdot_val)
        vdot_val = (sr_vdot + float(vdot_val)) / 2

    return get_custom_effort_pace(vdot_val, distance, 0.88)


def get_interval_pace(vdot_val: float, distance: float) -> float:
    """
    Calculate interval pace using Jack Daniels' methodology.
    
    Args:
        vdot_val: VDOT value.
        distance: Distance in meters.
        
    Returns:
        float: Time in minutes for the given distance.
    """
    if is_slow_vdot(vdot_val):
        vdot_val = get_slow_runner_vdot(vdot_val)

    return get_custom_effort_pace(vdot_val, distance, 0.975)


def get_repetition_pace(vdot_val: float, distance: float) -> float:
    """
    Calculate repetition pace using Jack Daniels' methodology.
    
    Args:
        vdot_val: VDOT value.
        distance: Distance in meters.
        
    Returns:
        float: Time in minutes for the given distance.
    """
    adjustment = distance / 400 * (6 / 60)  # 6 seconds per 400m
    interval_pace = get_interval_pace(vdot_val, distance)
    return interval_pace - adjustment


def get_marathon_pace(vdot_val: float, distance: float) -> float:
    """
    Calculate marathon pace using Jack Daniels' methodology.
    
    Args:
        vdot_val: VDOT value.
        distance: Distance in meters.
        
    Returns:
        float: Time in minutes for the given distance.
    """
    marathon_velocity = get_marathon_velocity(vdot_val)
    return distance / marathon_velocity
