from fastmcp import FastMCP

from .core.formatting import time_in_hhmmss, pace_in_min_km
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


def main():
    """Main entry point for the console script."""
    mcp.run()

if __name__ == "__main__":
    main()
