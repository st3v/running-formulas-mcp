from fastmcp import FastMCP

from .core.formatting import time_in_hhmmss, pace_in_min_km, pace_in_min_sec
from .core.conversions import (
    pace_min_km_to_min_mile,
    pace_min_mile_to_min_km,
    pace_to_speed_kmh,
    speed_kmh_to_pace,
    pace_to_speed_mph,
    speed_mph_to_pace,
    kmh_to_mph,
    mph_to_kmh
)
from .formulas.riegel import predict_time_riegel
from .formulas.daniels import (
    calculate_vdot_from_performance,
    predict_time_daniels,
    get_easy_pace,
    get_threshold_pace,
    get_interval_pace,
    get_repetition_pace,
    get_marathon_pace
)

mcp = FastMCP(name="RunningFormulasMCP")

@mcp.tool
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
    if distance <= 0:
        raise ValueError("Distance must be positive")
    if time <= 0:
        raise ValueError("Time must be positive")
    
    vdot = calculate_vdot_from_performance(distance, time)
    return {
        "vdot": round(vdot, 1)
    }

@mcp.tool
def training_paces(vdot: float) -> dict:
    """
    Get recommended training paces for a given VDOT, based on Jack Daniels' formulas.

    Args:
        vdot: VDOT value.

    Returns:
        dict:
            easy (dict): Recommended easy pace range with lower and upper bounds.
            marathon (dict): Recommended marathon pace with value and format.
            threshold (dict): Recommended threshold pace with value and format.
            interval (dict): Recommended interval pace with value and format.
            repetition (dict): Recommended repetition pace with value and format.
    """
    if vdot <= 0:
        raise ValueError("VDOT must be positive")
    
    # Constants
    DISTANCE_KM = 1000  # Calculate for 1 km (1000 meters)

    # Calculate all training paces for 1km
    easy_slow = get_easy_pace(vdot, DISTANCE_KM, True)
    easy_fast = get_easy_pace(vdot, DISTANCE_KM, False)
    marathon = get_marathon_pace(vdot, DISTANCE_KM)
    threshold = get_threshold_pace(vdot, DISTANCE_KM)
    interval = get_interval_pace(vdot, DISTANCE_KM)
    repetition = get_repetition_pace(vdot, DISTANCE_KM)

    return {
        "easy": {
            "lower": {
                "value": pace_in_min_km(easy_fast),
                "format": "min:sec/km"
            },
            "upper": {
                "value": pace_in_min_km(easy_slow),
                "format": "min:sec/km"
            }
        },
        "marathon": {
            "value": pace_in_min_km(marathon),
            "format": "min:sec/km"
        },
        "threshold": {
            "value": pace_in_min_km(threshold),
            "format": "min:sec/km"
        },
        "interval": {
            "value": pace_in_min_km(interval),
            "format": "min:sec/km"
        },
        "repetition": {
            "value": pace_in_min_km(repetition),
            "format": "min:sec/km"
        }
    }

@mcp.tool
def predict_race_time(current_distance: float, current_time: float, target_distance: float) -> dict:
    """
    Predict race time for a target distance based on a current race performance.
    Uses Riegel's formula and Jack Daniels' equivalent performance methodology.

    Args:
        current_distance: Distance of known performance in meters.
        current_time: Time of known performance in seconds.
        target_distance: Distance for race time prediction in meters.

    Returns:
        dict:
            riegel (dict): Riegel's formula prediction with value, format, and time_seconds.
            daniels (dict): Daniels' VDOT method prediction with value, format, and time_seconds.
            average (dict): Average of both methods with value, format, and time_seconds.
    """
    if current_distance <= 0:
        raise ValueError("Current distance must be positive")
    if current_time <= 0:
        raise ValueError("Current time must be positive")
    if target_distance <= 0:
        raise ValueError("Target distance must be positive")
    
    # Use Riegel's formula
    riegel_time = predict_time_riegel(current_distance, current_time, target_distance)

    # Use Daniels' VDOT method
    daniels_time = predict_time_daniels(current_distance, current_time, target_distance)

    # Calculate average time of both methods
    average_time = (riegel_time + daniels_time) / 2

    return {
        "riegel": {
            "value": time_in_hhmmss(riegel_time),
            "format": "HH:MM:SS",
            "time_seconds": round(riegel_time, 1)
        },
        "daniels": {
            "value": time_in_hhmmss(daniels_time),
            "format": "HH:MM:SS",
            "time_seconds": round(daniels_time, 1)
        },
        "average": {
            "value": time_in_hhmmss(average_time),
            "format": "HH:MM:SS",
            "time_seconds": round(average_time, 1)
        }
    }

@mcp.tool
def convert_pace(value: float, from_unit: str, to_unit: str) -> dict:
    """
    Convert between different pace and speed units.

    Args:
        value: The numeric value to convert.
        from_unit: Source unit ("min_km", "min_mile", "kmh", "mph").
        to_unit: Target unit ("min_km", "min_mile", "kmh", "mph").

    Returns:
        dict:
            value (float): Converted numeric value.
            formatted (str): Human-readable formatted result.
            unit (str): Target unit descriptor.

    Raises:
        ValueError: If from_unit or to_unit are not valid, or if conversion is not supported.
    """
    # Validate units
    valid_units = {"min_km", "min_mile", "kmh", "mph"}
    if from_unit not in valid_units:
        raise ValueError(f"Invalid from_unit '{from_unit}'. Must be one of: {valid_units}")
    if to_unit not in valid_units:
        raise ValueError(f"Invalid to_unit '{to_unit}'. Must be one of: {valid_units}")

    # Conversion function mapping - single functions, chains, or empty chains
    conversion_map = {
        # Same unit conversions (empty chains)
        ("min_km", "min_km"): [],
        ("min_mile", "min_mile"): [],
        ("kmh", "kmh"): [],
        ("mph", "mph"): [],

        # Direct conversions
        ("min_km", "min_mile"): [pace_min_km_to_min_mile],
        ("min_mile", "min_km"): [pace_min_mile_to_min_km],
        ("min_km", "kmh"): [pace_to_speed_kmh],
        ("kmh", "min_km"): [speed_kmh_to_pace],
        ("min_mile", "mph"): [pace_to_speed_mph],
        ("mph", "min_mile"): [speed_mph_to_pace],
        ("kmh", "mph"): [kmh_to_mph],
        ("mph", "kmh"): [mph_to_kmh],

        # Cross conversions via function chains
        ("min_km", "mph"): [pace_to_speed_kmh, kmh_to_mph],
        ("mph", "min_km"): [mph_to_kmh, speed_kmh_to_pace],
        ("min_mile", "kmh"): [pace_to_speed_mph, mph_to_kmh],
        ("kmh", "min_mile"): [kmh_to_mph, speed_mph_to_pace],
    }

    # Look up conversion functions
    conversion_key = (from_unit, to_unit)
    if conversion_key not in conversion_map:
        raise ValueError(f"Conversion from '{from_unit}' to '{to_unit}' not supported")

    # Apply function chain
    result_value = value
    for func in conversion_map[conversion_key]:
        result_value = func(result_value)

    # Format the result
    if to_unit in ["min_km", "min_mile"]:
        formatted = pace_in_min_sec(result_value)
    else:
        formatted = f"{result_value:.1f}"

    return {
        "value": round(result_value, 3),
        "formatted": formatted,
        "unit": to_unit
    }


def main():
    """Main entry point for the console script."""
    mcp.run()

if __name__ == "__main__":
    main()
