"""Time and pace formatting utilities."""


def time_in_hhmmss(seconds: float) -> str:
    """
    Format seconds into HH:MM:SS format.

    Args:
        seconds: Time in seconds.

    Returns:
        str: Formatted time as HH:MM:SS with zero-padded hours.
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def pace_in_min_km(pace_per_km: float) -> str:
    """
    Convert pace from minutes per km to min:sec per km format.

    Args:
        pace_per_km: Pace in minutes per kilometer.

    Returns:
        str: Formatted pace as M:SS per km.
    """
    minutes = int(pace_per_km // 1)
    seconds = round((pace_per_km % 1) * 60)

    # Handle seconds rollover (60 seconds = 1 minute)
    if seconds == 60:
        minutes += 1
        seconds = 0

    return f"{minutes}:{seconds:02d}"


def pace_in_min_sec(pace_minutes: float) -> str:
    """
    Format decimal minutes to pace string in M:SS format.
    
    Args:
        pace_minutes: Pace in decimal minutes.
        
    Returns:
        str: Formatted pace as "M:SS".
    """
    minutes = int(pace_minutes)
    seconds = int((pace_minutes - minutes) * 60)
    
    # Handle rounding edge case
    if seconds >= 60:
        minutes += 1
        seconds = 0
        
    return f"{minutes}:{seconds:02d}"
