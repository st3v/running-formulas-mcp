from fastmcp import FastMCP
import math

mcp = FastMCP(name="RunningFormulasMCP")

def _calculate_vdot_from_performance(distance: float, time: float) -> float:
    """
    Helper function to calculate VDOT from distance and time.

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

def _get_pace_velocity(vdot_val: float) -> float:
    """Calculate velocity from VDOT using Jack Daniels formula.
    
    Args:
        vdot_val: VDOT value.
        
    Returns:
        float: Velocity in meters per minute.
    """
    return 29.54 + 5.000663 * vdot_val - 0.007546 * (vdot_val ** 2)

def _get_custom_effort_pace(vdot_val: float, distance: float, effort_percentage: float) -> float:
    """Calculate pace for given effort percentage.
    
    Args:
        vdot_val: VDOT value.
        distance: Distance in meters.
        effort_percentage: Effort as percentage (0.0 to 1.0).
        
    Returns:
        float: Time in minutes for the given distance.
    """
    adjusted_vdot = vdot_val * effort_percentage
    velocity = _get_pace_velocity(adjusted_vdot)  # meters per minute
    pace_per_meter = 1 / velocity  # minutes per meter
    return pace_per_meter * distance  # minutes per distance

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
    vdot = _calculate_vdot_from_performance(distance, time)
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
    SLOW_VDOT_LIMIT = 39
    DISTANCE_KM = 1000  # Calculate for 1 km (1000 meters)

    def _is_slow_vdot(vdot_val):
        """Check if VDOT is considered slow and needs adjustment."""
        return 0 < vdot_val < SLOW_VDOT_LIMIT

    def _get_sr_vdot(vdot_val):
        """Get adjusted VDOT for slow runners."""
        return vdot_val * 2 / 3 + 13


    def _get_marathon_velocity(vdot_val):
        """Calculate marathon velocity using iterative method."""
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

    def get_easy_pace(vdot_val, distance, is_slow_version=False):
        """Calculate easy pace."""
        if _is_slow_vdot(vdot_val):
            vdot_val = _get_sr_vdot(vdot_val)

        effort = 0.62 if is_slow_version else 0.7
        return _get_custom_effort_pace(vdot_val, distance, effort)

    def get_threshold_pace(vdot_val, distance):
        """Calculate threshold pace."""
        if _is_slow_vdot(vdot_val):
            sr_vdot = _get_sr_vdot(vdot_val)
            vdot_val = (sr_vdot + float(vdot_val)) / 2

        return _get_custom_effort_pace(vdot_val, distance, 0.88)

    def get_interval_pace(vdot_val, distance):
        """Calculate interval pace."""
        if _is_slow_vdot(vdot_val):
            vdot_val = _get_sr_vdot(vdot_val)

        return _get_custom_effort_pace(vdot_val, distance, 0.975)

    def get_repetition_pace(vdot_val, distance):
        """Calculate repetition pace."""
        adjustment = distance / 400 * (6 / 60)  # 6 seconds per 400m
        interval_pace = get_interval_pace(vdot_val, distance)
        return interval_pace - adjustment

    def get_marathon_pace(vdot_val, distance):
        """Calculate marathon pace."""
        marathon_velocity = _get_marathon_velocity(vdot_val)
        return distance / marathon_velocity

    def pace_to_min_km(pace_per_km):
        """Convert pace from minutes per km to min:sec per km format."""
        minutes = int(pace_per_km // 1)
        seconds = round((pace_per_km % 1) * 60)

        # Handle seconds rollover (60 seconds = 1 minute)
        if seconds == 60:
            minutes += 1
            seconds = 0

        return f"{minutes}:{seconds:02d}"

    def pace_range_str(slow_pace, fast_pace):
        """Format pace range."""
        return f"{pace_to_min_km(slow_pace)} - {pace_to_min_km(fast_pace)}"

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
                "value": pace_to_min_km(easy_fast),
                "format": "min:sec/km"
            },
            "upper": {
                "value": pace_to_min_km(easy_slow),
                "format": "min:sec/km"
            }
        },
        "marathon": {
            "value": pace_to_min_km(marathon),
            "format": "min:sec/km"
        },
        "threshold": {
            "value": pace_to_min_km(threshold),
            "format": "min:sec/km"
        },
        "interval": {
            "value": pace_to_min_km(interval),
            "format": "min:sec/km"
        },
        "repetition": {
            "value": pace_to_min_km(repetition),
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
    def format_time(seconds):
        """Format seconds into HH:MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    # Riegel's formula: T2 = T1 * (D2/D1)^1.06
    riegel_exponent = 1.06
    riegel_time = current_time * ((target_distance / current_distance) ** riegel_exponent)

    # Daniels' method using VDOT
    # Get VDOT from current performance
    vdot = _calculate_vdot_from_performance(current_distance, current_time)
    
    # Calculate time for target distance using 100% effort (1.0)
    daniels_time_minutes = _get_custom_effort_pace(vdot, target_distance, 1.0)
    daniels_time = daniels_time_minutes * 60  # Convert minutes to seconds

    # Calculate average time of both methods
    average_time = (riegel_time + daniels_time) / 2

    return {
        "riegel": {
            "value": format_time(riegel_time),
            "format": "HH:MM:SS",
            "time_seconds": round(riegel_time, 1)
        },
        "daniels": {
            "value": format_time(daniels_time),
            "format": "HH:MM:SS",
            "time_seconds": round(daniels_time, 1)
        },
        "average": {
            "value": format_time(average_time),
            "format": "HH:MM:SS",
            "time_seconds": round(average_time, 1)
        }
    }


def main():
    """Main entry point for the console script."""
    mcp.run()

if __name__ == "__main__":
    main()
