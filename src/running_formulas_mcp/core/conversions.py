"""Pace and speed conversion utilities."""


def pace_min_km_to_min_mile(pace_min_km: float) -> float:
    """
    Convert pace from minutes per kilometer to minutes per mile.

    Args:
        pace_min_km: Pace in minutes per kilometer.

    Returns:
        float: Pace in minutes per mile.
    """
    # 1 mile = 1.609344 km
    return pace_min_km * 1.609344


def pace_min_mile_to_min_km(pace_min_mile: float) -> float:
    """
    Convert pace from minutes per mile to minutes per kilometer.

    Args:
        pace_min_mile: Pace in minutes per mile.

    Returns:
        float: Pace in minutes per kilometer.
    """
    # 1 mile = 1.609344 km
    return pace_min_mile / 1.609344


def pace_to_speed_kmh(pace_min_km: float) -> float:
    """
    Convert pace (min/km) to speed (km/h).

    Args:
        pace_min_km: Pace in minutes per kilometer.

    Returns:
        float: Speed in kilometers per hour.
    """
    if pace_min_km <= 0:
        raise ValueError("Pace must be a positive value")
    # Speed = 60 / pace (60 minutes per hour)
    return 60.0 / pace_min_km


def speed_kmh_to_pace(speed_kmh: float) -> float:
    """
    Convert speed (km/h) to pace (min/km).

    Args:
        speed_kmh: Speed in kilometers per hour.

    Returns:
        float: Pace in minutes per kilometer.
    """
    if speed_kmh <= 0:
        raise ValueError("Speed must be a positive value")
    # Pace = 60 / speed (60 minutes per hour)
    return 60.0 / speed_kmh


def pace_to_speed_mph(pace_min_mile: float) -> float:
    """
    Convert pace (min/mile) to speed (mph).

    Args:
        pace_min_mile: Pace in minutes per mile.

    Returns:
        float: Speed in miles per hour.
    """
    if pace_min_mile <= 0:
        raise ValueError("Pace must be a positive value")
    # Speed = 60 / pace (60 minutes per hour)
    return 60.0 / pace_min_mile


def speed_mph_to_pace(speed_mph: float) -> float:
    """
    Convert speed (mph) to pace (min/mile).

    Args:
        speed_mph: Speed in miles per hour.

    Returns:
        float: Pace in minutes per mile.
    """
    if speed_mph <= 0:
        raise ValueError("Speed must be a positive value")
    # Pace = 60 / speed (60 minutes per hour)
    return 60.0 / speed_mph


def kmh_to_mph(speed_kmh: float) -> float:
    """
    Convert speed from km/h to mph.

    Args:
        speed_kmh: Speed in kilometers per hour.

    Returns:
        float: Speed in miles per hour.
    """
    # 1 mile = 1.609344 km
    return speed_kmh / 1.609344


def mph_to_kmh(speed_mph: float) -> float:
    """
    Convert speed from mph to km/h.

    Args:
        speed_mph: Speed in miles per hour.

    Returns:
        float: Speed in kilometers per hour.
    """
    # 1 mile = 1.609344 km
    return speed_mph * 1.609344


def parse_pace_string(pace_str: str) -> float:
    """
    Parse a pace string in MM:SS or M:SS format to decimal minutes.

    Args:
        pace_str: Pace string in format "M:SS" or "MM:SS".

    Returns:
        float: Pace in decimal minutes.

    Raises:
        ValueError: If the pace string format is invalid.
    """
    try:
        if ':' not in pace_str:
            raise ValueError("Pace must be in M:SS or MM:SS format")

        parts = pace_str.split(':')
        if len(parts) != 2:
            raise ValueError("Pace must be in M:SS or MM:SS format")

        minutes = int(parts[0])
        seconds = int(parts[1])

        if seconds >= 60:
            raise ValueError("Seconds must be less than 60")

        return minutes + (seconds / 60.0)

    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid pace format '{pace_str}': {e}")


