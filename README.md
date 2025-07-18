
# running-formulas-mcp MCP server

An MCP server with comprehensive tools for running calculations including VDOT, training paces, race time predictions, velocity markers, heart rate zones, and pace conversions. Supports multiple methodologies including [Jack Daniels](https://www.coacheseducation.com/endur/jack-daniels-nov-00.php), [Greg McMillan](https://www.mcmillanrunning.com/), and Riegel's formula.

## Features

### Jack Daniels Methodology
- **VDOT Calculation**: Calculate VDOT from race performance using Jack Daniels' formula
- **Training Paces**: Get recommended training paces (Easy, Marathon, Threshold, Interval, Repetition) for a given VDOT
- **Race Time Predictions**: Predict race times using Jack Daniels' equivalent performance methodology

### McMillan Methodology
- **Velocity Markers**: Calculate vLT (Lactate Threshold), CV (Critical Velocity), and vVO2 (VO2max velocity)
- **Training Paces**: Comprehensive training pace zones (Endurance, Stamina, Speed, Sprint) with sub-categories
- **Race Time Predictions**: Predict race times for all standard distances using McMillan's methodology
- **Heart Rate Zones**: Calculate training heart rate zones using multiple estimation formulas

### Additional Tools
- **Riegel's Formula**: Race time predictions using Riegel's power law
- **Pace Conversions**: Convert between different pace and speed formats (min/km, min/mile, km/h, mph)

## Tools

### Jack Daniels Tools

- `daniels_calculate_vdot`: Calculate VDOT from race performance using Jack Daniels' formula.
  - **Input:**
    - `distance` (float): Distance in meters
    - `time` (float): Time in seconds
  - **Output:**
    - `vdot` (float): The calculated VDOT value

- `daniels_calculate_training_paces`: Get recommended training paces for a given VDOT.
  - **Input:**
    - `vdot` (float): VDOT value
  - **Output:**
    - `easy` (object): Easy pace range with lower and upper bounds
    - `marathon` (object): Marathon pace
    - `threshold` (object): Threshold pace
    - `interval` (object): Interval pace
    - `repetition` (object): Repetition pace
    - All paces formatted as "MM:SS/km"

- `daniels_predict_race_time`: Predict race time using Jack Daniels' equivalent performance methodology.
  - **Input:**
    - `current_distance` (float): Distance of known performance in meters
    - `current_time` (float): Time of known performance in seconds
    - `target_distance` (float): Distance for race time prediction in meters
  - **Output:**
    - `value` (string): Predicted time in "HH:MM:SS" format
    - `format` (string): "HH:MM:SS"
    - `time_seconds` (float): Time in seconds

### McMillan Tools

- `mcmillan_calculate_velocity_markers`: Calculate velocity markers (vLT, CV, vVO2) from race performance.
  - **Input:**
    - `distance` (float): Race distance in meters
    - `time` (float): Race time in seconds
  - **Output:**
    - `velocity_markers` (object): Contains vLT, CV, and vVO2 with pace and description

- `mcmillan_predict_race_times`: Predict race times for standard distances using McMillan methodology.
  - **Input:**
    - `distance` (float): Race distance in meters
    - `time` (float): Race time in seconds
  - **Output:**
    - Dictionary with predicted times for all standard race distances

- `mcmillan_calculate_training_paces`: Calculate comprehensive training paces using McMillan methodology.
  - **Input:**
    - `distance` (float): Race distance in meters
    - `time` (float): Race time in seconds
  - **Output:**
    - Training paces organized by zones (endurance, stamina, speed, sprint)

- `mcmillan_heart_rate_zones`: Calculate heart rate training zones.
  - **Input:**
    - `age` (int): Runner's age in years
    - `resting_heart_rate` (int): Resting heart rate in BPM
    - `max_heart_rate` (int, optional): Maximum heart rate in BPM
  - **Output:**
    - Heart rate zones with both HRMAX and HRRESERVE calculations

### Additional Tools

- `riegel_predict_race_time`: Predict race time using Riegel's formula.
  - **Input:**
    - `current_distance` (float): Distance of known performance in meters
    - `current_time` (float): Time of known performance in seconds
    - `target_distance` (float): Distance for race time prediction in meters
  - **Output:**
    - `value` (string): Predicted time in "HH:MM:SS" format
    - `format` (string): "HH:MM:SS"
    - `time_seconds` (float): Time in seconds

- `convert_pace`: Convert between different pace and speed units.
  - **Input:**
    - `value` (float): The numeric value to convert
    - `from_unit` (string): Source unit ("min_km", "min_mile", "kmh", "mph")
    - `to_unit` (string): Target unit ("min_km", "min_mile", "kmh", "mph")
  - **Output:**
    - `value` (float): Converted numeric value
    - `formatted` (string): Human-readable formatted result
    - `unit` (string): Target unit descriptor

## Usage

This server is designed to be used as an MCP stdio server. It does not expose HTTP endpoints directly.

### Example: Calculate VDOT for a 5k in 25 minutes

Call the `daniels_calculate_vdot` tool with:

```json
{
  "name": "daniels_calculate_vdot",
  "arguments": { "distance": 5000, "time": 1500 }
}
```

Returns:
```json
{
  "vdot": 38.4
}
```

### Example: Get training paces for VDOT 38.4

Call the `daniels_calculate_training_paces` tool with:

```json
{
  "name": "daniels_calculate_training_paces",
  "arguments": { "vdot": 38.4 }
}
```

Returns structured pace data like:
```json
{
  "easy": {
    "lower": {"value": "5:42", "format": "MM:SS/km"},
    "upper": {"value": "6:29", "format": "MM:SS/km"}
  },
  "marathon": {"value": "5:07", "format": "MM:SS/km"},
  "threshold": {"value": "4:50", "format": "MM:SS/km"},
  "interval": {"value": "4:32", "format": "MM:SS/km"},
  "repetition": {"value": "4:26", "format": "MM:SS/km"}
}
```

### Example: Calculate McMillan velocity markers from 5K performance

Call the `mcmillan_calculate_velocity_markers` tool with:

```json
{
  "name": "mcmillan_calculate_velocity_markers",
  "arguments": { "distance": 5000, "time": 1500 }
}
```

Returns velocity markers:
```json
{
  "velocity_markers": {
    "vLT": {
      "pace": "4:50",
      "description": "Velocity at Lactate Threshold (vLT) - sustainable pace for ~1 hour"
    },
    "CV": {
      "pace": "4:32",
      "description": "Critical Velocity (CV) - theoretical maximum sustainable pace"
    },
    "vVO2": {
      "pace": "4:15",
      "description": "Velocity at VO2max (vVO2) - pace at maximum oxygen uptake"
    }
  }
}
```

### Example: Predict 10K time using Daniels methodology

Call the `daniels_predict_race_time` tool with:

```json
{
  "name": "daniels_predict_race_time",
  "arguments": { "current_distance": 5000, "current_time": 1500, "target_distance": 10000 }
}
```

Returns:
```json
{
  "value": "00:52:07",
  "format": "HH:MM:SS",
  "time_seconds": 3127.4
}
```

### Example: Calculate heart rate zones for a 30-year-old

Call the `mcmillan_heart_rate_zones` tool with:

```json
{
  "name": "mcmillan_heart_rate_zones",
  "arguments": { "age": 30, "resting_heart_rate": 60, "max_heart_rate": 190 }
}
```

### Example: Convert pace from min/km to min/mile

Call the `convert_pace` tool with:

```json
{
  "name": "convert_pace",
  "arguments": { "value": 5.0, "from_unit": "min_km", "to_unit": "min_mile" }
}
```

Returns:
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