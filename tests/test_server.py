import pytest
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from running_formulas_mcp.server import mcp

def test_mcp_server_tools():
    """Test that the MCP server lists exactly the expected tools"""
    expected_tools = {"calculate_vdot", "training_paces"}
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

def test_training_paces():
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
        fn = get_actual_function('training_paces')
        result = fn(vdot)
        assert isinstance(result, dict)
        assert result == expected
