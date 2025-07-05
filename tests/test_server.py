
import sys
import os
from pytest import raises

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from running_formulas_mcp.server import mcp

def test_mcp_server_tools():
    """Test that the MCP server lists exactly the expected tools"""
    expected_tools = {"calculate_vdot", "training_paces", "predict_race_time", "convert_pace"}
    actual_tools = set(mcp._tool_manager._tools.keys())

    # Check that we have exactly the expected tools
    assert actual_tools == expected_tools, f"Expected tools {expected_tools}, but got {actual_tools}"

    # Check that each tool is properly registered
    for tool_name in expected_tools:
        assert tool_name in mcp._tool_manager._tools
        tool = mcp._tool_manager._tools[tool_name]
        assert tool.fn is not None
        assert tool.description is not None

def get_actual_function(tool_name):
    """Get the actual function from the FastMCP tool manager"""
    return mcp._tool_manager._tools[tool_name].fn

def test_calculate_vdot():
    fn = get_actual_function('calculate_vdot')

    test_cases = [
        (5000, 1500, 38.3),  # 5k in 25 minutes
        (10000, 3600, 32.3),  # 10k in 60 minutes
        (1500, 240, 70.1),  # 1500m in 4 minutes
        (42195, 7200, 86.0),  # Marathon in 2 hours
        (1235, 201, 67.4),
    ]

    for distance, time, expected_vdot in test_cases:
        result = fn(distance, time)
        assert "vdot" in result
        assert isinstance(result["vdot"], float)
        assert result["vdot"] == expected_vdot

    # Negative test cases: invalid distance and time values
    negative_test_cases = [
        (0, 1500),      # Zero distance
        (-5000, 1500),  # Negative distance
        (5000, 0),      # Zero time
        (5000, -1500),  # Negative time
    ]

    for distance, time in negative_test_cases:
        with raises(ValueError):
            fn(distance, time)

def test_training_paces():
    fn = get_actual_function('training_paces')

    test_cases = [
        (38.3, {
            "easy": {
                "lower": {"value": "6:18", "format": "min:sec/km"},
                "upper": {"value": "6:55", "format": "min:sec/km"}
            },
            "marathon": {"value": "5:38", "format": "min:sec/km"},
            "threshold": {"value": "5:16", "format": "min:sec/km"},
            "interval": {"value": "4:50", "format": "min:sec/km"},
            "repetition": {"value": "4:35", "format": "min:sec/km"}
        }),
        (69.6, {
            "easy": {
                "lower": {"value": "3:55", "format": "min:sec/km"},
                "upper": {"value": "4:19", "format": "min:sec/km"}
            },
            "marathon": {"value": "3:24", "format": "min:sec/km"},
            "threshold": {"value": "3:15", "format": "min:sec/km"},
            "interval": {"value": "3:00", "format": "min:sec/km"},
            "repetition": {"value": "2:45", "format": "min:sec/km"}
        })
    ]

    for vdot, expected in test_cases:
        result = fn(vdot)
        assert isinstance(result, dict)
        assert result == expected

    # Negative test cases: invalid VDOT values
    negative_test_cases = [
        0,      # Zero VDOT
        -10,    # Negative VDOT
        -38.3,  # Negative valid VDOT
    ]

    for vdot in negative_test_cases:
        with raises(ValueError):
            fn(vdot)

    # Edge cases: very high/low but valid VDOT values
    edge_case_vdots = [
        10.0,   # Very low VDOT
        100.0,  # Very high VDOT
    ]

    for vdot in edge_case_vdots:
        result = fn(vdot)
        assert isinstance(result, dict)
        assert "easy" in result
        assert "marathon" in result
        assert "threshold" in result
        assert "interval" in result
        assert "repetition" in result

def test_predict_race_time():
    """Test race time prediction functionality"""
    fn = get_actual_function('predict_race_time')

    # Positive test cases
    test_cases = [
        # (current_distance, current_time, target_distance, expected_result)
        (5000, 1500, 10000, {
            "riegel": {
                "value": "00:52:07",
                "format": "HH:MM:SS",
                "time_seconds": 3127.4
            },
            "daniels": {
                "value": "00:47:36",
                "format": "HH:MM:SS",
                "time_seconds": 2856.6
            },
            "average": {
                "value": "00:49:52",
                "format": "HH:MM:SS",
                "time_seconds": 2992.0
            }
        })
    ]

    for current_distance, current_time, target_distance, expected in test_cases:
        result = fn(current_distance, current_time, target_distance)
        assert result == expected

    # Negative test cases: invalid distance and time values
    negative_test_cases = [
        (0, 1500, 10000),      # Zero current distance
        (-5000, 1500, 10000),  # Negative current distance
        (5000, 0, 10000),      # Zero current time
        (5000, -1500, 10000),  # Negative current time
        (5000, 1500, 0),       # Zero target distance
        (5000, 1500, -10000),  # Negative target distance
    ]

    for current_distance, current_time, target_distance in negative_test_cases:
        with raises(ValueError):
            fn(current_distance, current_time, target_distance)

def test_convert_pace():
    """Test pace conversion functionality"""
    fn = get_actual_function('convert_pace')

    test_cases = [
        # (value, from_unit, to_unit, expected_result)
        (5.0, "min_km", "min_mile", {
            "value": 8.047,  # 5.0 * 1.609344 = 8.046720
            "formatted": "8:02",
            "unit": "min_mile"
        }),
        (12.0, "kmh", "mph", {
            "value": 7.456,  # 12.0 / 1.609344 = 7.456454
            "formatted": "7.5",
            "unit": "mph"
        }),
        (6.5, "min_km", "min_km", {
            "value": 6.5,
            "formatted": "6:30",
            "unit": "min_km"
        }),
        (4.0, "min_km", "kmh", {
            "value": 15.0,  # 60 / 4.0
            "formatted": "15.0",
            "unit": "kmh"
        }),
        # Cross conversion: min_km -> kmh -> mph
        (5.0, "min_km", "mph", {
            "value": 7.456,  # 5.0 -> 12.0 kmh -> 7.456 mph
            "formatted": "7.5",
            "unit": "mph"
        }),
        # Cross conversion: min_mile -> mph -> kmh
        (8.0, "min_mile", "kmh", {
            "value": 12.07,  # 8.0 -> 7.5 mph -> 12.07 kmh
            "formatted": "12.1",
            "unit": "kmh"
        })
    ]

    for value, from_unit, to_unit, expected in test_cases:
        result = fn(value, from_unit, to_unit)
        assert result == expected

    # Negative test cases: invalid units and values
    negative_test_cases = [
        (5.0, "invalid_unit", "min_km"),  # Invalid from_unit
        (5.0, "min_km", "invalid_unit"),  # Invalid to_unit
        (5.0, "foo", "bar"),              # Both units invalid
        (0, "min_km", "kmh"),             # Zero value for pace
        (-5, "min_km", "kmh"),            # Negative value for pace
    ]

    for value, from_unit, to_unit in negative_test_cases:
        with raises(ValueError):
            fn(value, from_unit, to_unit)
