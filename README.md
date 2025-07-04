
# running-formulas-mcp MCP server

An MCP server with tools to calculate VDOT and recommended training paces based on [Jack Daniels](https://www.coacheseducation.com/endur/jack-daniels-nov-00.php).

## Features

- **VDOT Calculation**: Calculate VDOT from a given distance (meters) and time (seconds) using Jack Daniels' formula.
- **Training Paces**: Get recommended training paces (Easy, Marathon, Threshold, Interval, Repetition) for a given VDOT.

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