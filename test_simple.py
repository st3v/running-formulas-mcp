#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the raw functions before they're wrapped by FastMCP
import math

def calculate_vdot(distance: float, time: float) -> dict:
    """
    Calculate VDOT according to Jack Daniels.

    Args:
        distance: Distance in meters.
        time: Time in seconds.

    Returns:
        dict:
            vdot (float): The calculated VDOT value, representing the runner's aerobic capacity based on the input distance and time.
    """
    v = distance / (time / 60)
    vo2 = -4.60 + 0.182258 * v + 0.000104 * v * v
    t_min = time / 60
    vo2max = vo2 / (
        0.8 + 0.1894393 * math.exp(-0.012778 * t_min) + 0.2989558 * math.exp(-0.1932605 * t_min)
    )
    vdot = vo2max
    return {
        "vdot": vdot
    }

def training_intensities(vdot: float) -> dict:
    """
    Get recommended training intensities (paces) for a given VDOT, based on Jack Daniels' formulas.
    """
    # Constants for VDOT calculations (from Jack Daniels formula)
    _SlowVdotLimit = 39

    def get_sr_vdot(vdot_val):
        """Get slowrunner-adjusted VDOT"""
        return vdot_val * 2 / 3 + 13

    def get_pace_velocity(vdot_val):
        """Calculate velocity from VDOT using Jack Daniels formula"""
        return 29.54 + 5.000663 * vdot_val - 0.007546 * (vdot_val ** 2)

    def get_custom_effort_pace(vdot_val, distance, effort_percentage):
        """Calculate pace for given effort percentage"""
        adjusted_vdot = vdot_val * effort_percentage
        velocity = get_pace_velocity(adjusted_vdot)
        return distance / velocity

    def get_marathon_velocity(vdot_val):
        """Calculate marathon velocity using Jack Daniels iterative method"""
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

    def pace_to_min_km(pace_per_meter):
        """Convert pace from seconds per meter to min:sec per km format"""
        pace_per_km = pace_per_meter * 1000  # Convert to seconds per km
        minutes = int(pace_per_km // 60)
        seconds = int(pace_per_km % 60)
        return f"{minutes}:{seconds:02d}"

    def pace_range_str(slow_pace, fast_pace):
        """Format pace range"""
        return f"{pace_to_min_km(slow_pace)} - {pace_to_min_km(fast_pace)}"

    # Calculate training paces based on VDOT
    distance_km = 1.0  # 1 km

    # Easy pace: 62-70% of VDOT
    # For slow runners (VDOT < 39), use adjusted VDOT
    if vdot < _SlowVdotLimit:
        sr_vdot = get_sr_vdot(vdot)
        easy_slow = get_custom_effort_pace(sr_vdot, distance_km, 0.62)
        easy_fast = get_custom_effort_pace(sr_vdot, distance_km, 0.70)
    else:
        easy_slow = get_custom_effort_pace(vdot, distance_km, 0.62)
        easy_fast = get_custom_effort_pace(vdot, distance_km, 0.70)

    # Marathon pace
    marathon_velocity = get_marathon_velocity(vdot)
    marathon_pace = distance_km / marathon_velocity

    # Threshold pace: 88% of VDOT
    # For slow runners, use average of original and adjusted VDOT
    if vdot < _SlowVdotLimit:
        sr_vdot = get_sr_vdot(vdot)
        threshold_vdot = (sr_vdot + vdot) / 2
        threshold_pace = get_custom_effort_pace(threshold_vdot, distance_km, 0.88)
    else:
        threshold_pace = get_custom_effort_pace(vdot, distance_km, 0.88)

    # Interval pace: 97.5% of VDOT
    # For slow runners, use adjusted VDOT
    if vdot < _SlowVdotLimit:
        sr_vdot = get_sr_vdot(vdot)
        interval_pace = get_custom_effort_pace(sr_vdot, distance_km, 0.975)
    else:
        interval_pace = get_custom_effort_pace(vdot, distance_km, 0.975)

    # Repetition pace: Interval pace minus 6 seconds per 400m
    adjustment = distance_km / 400 * (6 / 60)  # 6 seconds per 400m in minutes
    repetition_pace = interval_pace - adjustment

    return {
        "easy": pace_range_str(easy_slow, easy_fast),
        "marathon": pace_to_min_km(marathon_pace),
        "threshold": pace_to_min_km(threshold_pace),
        "interval": pace_to_min_km(interval_pace),
        "repetition": pace_to_min_km(repetition_pace)
    }

if __name__ == "__main__":
    print("Testing calculate_vdot...")
    result1 = calculate_vdot(5000, 1500)
    print("VDOT result:", result1)

    print("\nTesting training_intensities...")
    result2 = training_intensities(38.31)
    print("Training intensities result:", result2)
