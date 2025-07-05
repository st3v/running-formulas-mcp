
# running-formulas-mcp MCP server

An MCP server with tools for running calculations including VDOT, training paces, race time predictions, and pace conversions based on [Jack Daniels](https://www.coacheseducation.com/endur/jack-daniels-nov-00.php) methodology and others.

## Features

- **VDOT Calculation**: Calculate VDOT from a given distance (meters) and time (seconds) using Jack Daniels' formula.
- **Training Paces**: Get recommended training paces (Easy, Marathon, Threshold, Interval, Repetition) for a given VDOT.
- **Race Time Predictions**: Predict race times for different distances using Riegel's formula and Jack Daniels' VDOT method.
- **Pace Conversions**: Convert between different pace and speed formats (min/km, min/mile, km/h, mph).

## Tools

- `calculate_vdot`: Returns VDOT for a given distance and time.
  - **Input:**
    - `distance` (number, meters)
    - `time` (number, seconds)
  - **Output:**
    - `vdot` (float): The calculated VDOT value

- `training_paces`: Returns recommended paces for a given VDOT.
  - **Input:**
    - `vdot` (number)
  - **Output:**
    - Structured pace data with value and format for each training zone:
      - `easy` (object): Lower and upper bounds for easy pace range
      - `marathon` (object): Marathon pace
      - `threshold` (object): Threshold pace
      - `interval` (object): Interval pace
      - `repetition` (object): Repetition pace
    - All paces include both `value` (formatted as "min:sec/km") and `format` fields

- `predict_race_time`: Predicts race times for different distances based on a current performance.
  - **Input:**
    - `current_distance` (number, meters)
    - `current_time` (number, seconds)
    - `target_distance` (number, meters)
  - **Output:**
    - `riegel` (object): Prediction using Riegel's formula with value, format, and time_seconds
    - `daniels` (object): Prediction using Jack Daniels' VDOT method with value, format, and time_seconds
    - `average` (object): Average of both methods with value, format, and time_seconds
    - All times formatted as "HH:MM:SS"

- `convert_pace`: Converts between different pace and speed units.
  - **Input:**
    - `value` (number): The numeric value to convert
    - `from_unit` (string): Source unit ("min_km", "min_mile", "kmh", "mph")
    - `to_unit` (string): Target unit ("min_km", "min_mile", "kmh", "mph")
  - **Output:**
    - `value` (float): Converted numeric value
    - `formatted` (string): Human-readable formatted result
    - `unit` (string): Target unit descriptor

## Usage

This server is designed to be used as an MCP stdio server. It does not expose HTTP endpoints directly.

### Example: Calculate VDOT for a 5k in 25 minutes

Call the `calculate_vdot` tool with:

```
{
  "name": "calculate_vdot",
  "arguments": { "distance": 5000, "time": 1500 }
}
```

### Example: Get training paces for VDOT 38.4

Call the `training_paces` tool with:

```
{
  "name": "training_paces",
  "arguments": { "vdot": 38.4 }
}
```

This returns structured pace data like:
```json
{
  "easy": {
    "lower": {"value": "5:42", "format": "min:sec/km"},
    "upper": {"value": "6:29", "format": "min:sec/km"}
  },
  "marathon": {"value": "5:07", "format": "min:sec/km"},
  "threshold": {"value": "4:50", "format": "min:sec/km"},
  "interval": {"value": "4:32", "format": "min:sec/km"},
  "repetition": {"value": "4:26", "format": "min:sec/km"}
}
```

### Example: Predict 10K time from 5K performance

Call the `predict_race_time` tool with:

```
{
  "name": "predict_race_time",
  "arguments": { "current_distance": 5000, "current_time": 1500, "target_distance": 10000 }
}
```

This returns race time predictions:
```json
{
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
}
```

### Example: Convert pace from min/km to min/mile

Call the `convert_pace` tool with:

```
{
  "name": "convert_pace",
  "arguments": { "value": 5.0, "from_unit": "min_km", "to_unit": "min_mile" }
}
```

This returns the converted pace:
```json
{
  "value": 8.047,
  "formatted": "8:02",
  "unit": "min_mile"
}
```

## Configuration

This server is designed to be used with Claude Desktop or other MCP-compatible clients. See the installation sections below for configuration details.

## Installation

```json
{
  "mcpServers": {
    "running-formulas-mcp": {
      "command": "uvx",
      "args": ["running-formulas-mcp"]
    }
  }
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.