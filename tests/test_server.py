
import sys
import os
import pytest
from pytest import raises

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.running_formulas_mcp.server import mcp

def test_mcp_server_tools():
    """Test that the MCP server lists exactly the expected tools"""
    expected_tools = {
        "daniels_calculate_vdot",
        "daniels_calculate_training_paces",
        "daniels_predict_race_time",
        "riegel_predict_race_time",
        "mcmillan_calculate_velocity_markers",
        "mcmillan_predict_race_times",
        "mcmillan_calculate_training_paces",
        "mcmillan_heart_rate_zones",
        "convert_pace",
    }
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

def test_daniels_calculate_vdot():
    fn = get_actual_function('daniels_calculate_vdot')

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

def test_daniels_calculate_training_paces():
    fn = get_actual_function('daniels_calculate_training_paces')

    test_cases = [
        (38.3, {
            "easy": {
                "lower": {"value": "6:18", "format": "MM:SS/km"},
                "upper": {"value": "6:55", "format": "MM:SS/km"}
            },
            "marathon": {"value": "5:38", "format": "MM:SS/km"},
            "threshold": {"value": "5:16", "format": "MM:SS/km"},
            "interval": {"value": "4:50", "format": "MM:SS/km"},
            "repetition": {"value": "4:35", "format": "MM:SS/km"}
        }),
        (69.6, {
            "easy": {
                "lower": {"value": "3:55", "format": "MM:SS/km"},
                "upper": {"value": "4:19", "format": "MM:SS/km"}
            },
            "marathon": {"value": "3:24", "format": "MM:SS/km"},
            "threshold": {"value": "3:15", "format": "MM:SS/km"},
            "interval": {"value": "3:00", "format": "MM:SS/km"},
            "repetition": {"value": "2:45", "format": "MM:SS/km"}
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
        for zone in ["easy", "marathon", "threshold", "interval", "repetition"]:
            assert zone in result

def test_daniels_predict_race_time():
    """Test Daniels race time prediction functionality"""
    fn = get_actual_function('daniels_predict_race_time')

    # Test a basic prediction
    result = fn(5000, 1500, 10000)
    assert "value" in result
    assert "format" in result
    assert "time_seconds" in result
    assert result["format"] == "HH:MM:SS"
    assert isinstance(result["time_seconds"], float)

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

def test_riegel_predict_race_time():
    """Test Riegel race time prediction functionality"""
    fn = get_actual_function('riegel_predict_race_time')

    # Test a basic prediction
    result = fn(5000, 1500, 10000)
    assert "value" in result
    assert "format" in result
    assert "time_seconds" in result
    assert result["format"] == "HH:MM:SS"
    assert isinstance(result["time_seconds"], float)

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
        }),

        # pace_min_mile_to_min_km tests
        (8.0, "min_mile", "min_km", {
            "value": 4.971,  # 8.0 / 1.609344 = 4.970969
            "formatted": "4:58",
            "unit": "min_km"
        }),
        (6.0, "min_mile", "min_km", {
            "value": 3.728,  # 6.0 / 1.609344 = 3.728227
            "formatted": "3:43",
            "unit": "min_km"
        }),

        # speed_kmh_to_pace tests
        (10.0, "kmh", "min_km", {
            "value": 6.0,  # 60 / 10.0 = 6.0
            "formatted": "6:00",
            "unit": "min_km"
        }),
        (15.0, "kmh", "min_km", {
            "value": 4.0,  # 60 / 15.0 = 4.0
            "formatted": "4:00",
            "unit": "min_km"
        }),

        # pace_to_speed_mph tests
        (7.5, "min_mile", "mph", {
            "value": 8.0,  # 60 / 7.5 = 8.0
            "formatted": "8.0",
            "unit": "mph"
        }),
        (6.0, "min_mile", "mph", {
            "value": 10.0,  # 60 / 6.0 = 10.0
            "formatted": "10.0",
            "unit": "mph"
        }),

        # speed_mph_to_pace tests
        (8.0, "mph", "min_mile", {
            "value": 7.5,  # 60 / 8.0 = 7.5
            "formatted": "7:30",
            "unit": "min_mile"
        }),
        (10.0, "mph", "min_mile", {
            "value": 6.0,  # 60 / 10.0 = 6.0
            "formatted": "6:00",
            "unit": "min_mile"
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
        (0, "min_km", "kmh"),             # Zero pace for pace_to_speed_kmh
        (-5, "min_km", "kmh"),            # Negative pace for pace_to_speed_kmh
        (0, "kmh", "min_km"),             # Zero speed for speed_kmh_to_pace
        (-10, "kmh", "min_km"),           # Negative speed for speed_kmh_to_pace
        (0, "min_mile", "mph"),           # Zero pace for pace_to_speed_mph
        (-7.5, "min_mile", "mph"),        # Negative pace for pace_to_speed_mph
        (0, "mph", "min_mile"),           # Zero speed for speed_mph_to_pace
        (-8, "mph", "min_mile"),          # Negative speed for speed_mph_to_pace
    ]

    for value, from_unit, to_unit in negative_test_cases:
        with raises(ValueError):
            fn(value, from_unit, to_unit)

def test_mcmillan_calculate_velocity_markers():
    """Test McMillan velocity markers calculation"""
    fn = get_actual_function('mcmillan_calculate_velocity_markers')

    # Test with a 5k race performance
    result = fn(5000, 1500)  # 5k in 25 minutes
    assert "velocity_markers" in result
    assert "vLT" in result["velocity_markers"]
    assert "CV" in result["velocity_markers"]
    assert "vVO2" in result["velocity_markers"]

    # Check structure of each marker
    for marker in ["vLT", "CV", "vVO2"]:
        assert "pace" in result["velocity_markers"][marker]
        assert "description" in result["velocity_markers"][marker]
        assert isinstance(result["velocity_markers"][marker]["pace"], str)
        assert isinstance(result["velocity_markers"][marker]["description"], str)

    # Negative test cases: invalid distance and time values
    negative_test_cases = [
        (0, 1500),      # Zero distance
        (-5000, 1500),  # Negative distance
        (5000, 0),      # Zero time
        (5000, -1500),  # Negative time
    ]

    for distance, time in negative_test_cases:
        result = fn(distance, time)
        assert "error" in result

def test_mcmillan_predict_race_times():
    """Test McMillan race time predictions"""
    fn = get_actual_function('mcmillan_predict_race_times')

    # Test with a 5k race performance
    result = fn(5000, 1500)  # 5k in 25 minutes
    assert isinstance(result, dict)

    # Should contain predictions for standard distances
    # The exact structure depends on the implementation, but should be a dict
    assert len(result) > 0

    # Negative test cases: invalid distance and time values
    negative_test_cases = [
        (0, 1500),      # Zero distance
        (-5000, 1500),  # Negative distance
        (5000, 0),      # Zero time
        (5000, -1500),  # Negative time
    ]

    for distance, time in negative_test_cases:
        result = fn(distance, time)
        assert "error" in result

def test_mcmillan_calculate_training_paces():
    """Test McMillan training paces calculation"""
    fn = get_actual_function('mcmillan_calculate_training_paces')

    # Test with a 5k race performance
    result = fn(5000, 1500)  # 5k in 25 minutes
    assert isinstance(result, dict)

    # Should contain training zones
    # The exact structure depends on the implementation, but should be a dict
    assert len(result) > 0

    # Negative test cases: invalid distance and time values
    negative_test_cases = [
        (0, 1500),      # Zero distance
        (-5000, 1500),  # Negative distance
        (5000, 0),      # Zero time
        (5000, -1500),  # Negative time
    ]

    for distance, time in negative_test_cases:
        result = fn(distance, time)
        assert "error" in result

def test_mcmillan_heart_rate_zones():
    """Test McMillan heart rate zones calculation"""
    fn = get_actual_function('mcmillan_heart_rate_zones')

    # Test with basic parameters
    result = fn(30, 60)  # 30 years old, 60 bpm resting HR
    assert isinstance(result, dict)
    assert len(result) > 0

    # Test with custom max heart rate
    result = fn(30, 60, 190)  # 30 years old, 60 bpm resting HR, 190 max HR
    assert isinstance(result, dict)
    assert len(result) > 0

    # Negative test cases: invalid age and heart rate values
    negative_test_cases = [
        (0, 60),        # Zero age
        (-30, 60),      # Negative age
        (30, 0),        # Zero resting HR
        (30, -60),      # Negative resting HR
        (30, 60, 0),    # Zero max HR
        (30, 60, -190), # Negative max HR
    ]

    for args in negative_test_cases:
        result = fn(*args)
        assert "error" in result
