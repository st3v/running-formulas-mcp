"""
Unit tests for McMillan Running Calculator implementation.
"""

import pytest
from pytest import approx
from src.running_formulas_mcp.formulas.mcmillan import (
    calculate_cv, calculate_vlt, calculate_vvo2, predict_race_times,
    training_paces, format_pace_ms, format_pace_hms, format_pace,
    format_split, format_pace_and_time, _normalize_time, _assert_inputs,
    heart_rate_zones
)


# ============================================================================
# SHARED FIXTURES AND TEST DATA
# ============================================================================

@pytest.fixture
def boundary_valid_cases():
    """Test cases for boundary valid inputs (just within valid range)."""
    return [
        (1000, 60, "At pace boundary (60 sec/km - just valid)"),
        (1000, 1200, "At pace boundary (1200 sec/km - just valid)"),
        (5000, 300, "At pace boundary (60 sec/km - just valid)"),
        (5000, 6000, "At pace boundary (1200 sec/km - just valid)"),
        (400, 120, "At distance boundary (400m - minimum valid)"),
        (160934, 50000, "At distance boundary (160934m - maximum valid)"),
    ]


@pytest.fixture
def boundary_invalid_cases():
    """Test cases for boundary invalid inputs (just outside valid range)."""
    return [
        (1000, 59, "Pace appears unrealistically fast"),
        (1000, 1201, "Pace appears unrealistically slow"),
        (5000, 299, "Pace appears unrealistically fast"),
        (5000, 6001, "Pace appears unrealistically slow"),
        (399, 120, "Distance too short, must be at least 400m for meaningful calculations"),
        (160935, 50000, "Distance too long, must be less than 100 miles for this calculation method"),
    ]


@pytest.fixture
def basic_invalid_cases():
    """Test cases for basic invalid inputs."""
    return [
        (-1000, 1200, "Distance must be positive"),
        (5000, -120, "Time must be positive"),
        (0, 1200, "Distance must be positive"),
        (5000, 0, "Time must be positive"),
        (100, 60, "Distance too short, must be at least 400m for meaningful calculations"),
        (200000, 36000, "Distance too long, must be less than 100 miles for this calculation method"),
    ]


@pytest.fixture
def interpolated_distance_cases():
    """Test cases for interpolated distances."""
    return [
        (4500, 1080, "Interpolated distance (4500m)"),
        (7500, 1800, "Interpolated distance (7500m)"),
        (12500, 3000, "Interpolated distance (12.5K)"),
        (6000, 1440, "Interpolated distance (6K)"),
        (15000, 3600, "Interpolated distance (15K)"),
        (25000, 6000, "Interpolated distance (25K)"),
    ]


# ============================================================================
# SHARED HELPER METHODS
# ============================================================================

def time_string_to_seconds(time_str):
    """Convert HH:MM:SS time string to total seconds."""
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def pace_string_to_seconds(pace_str):
    """Convert MM:SS pace string to total seconds."""
    parts = pace_str.split(":")
    minutes = int(parts[0])
    seconds = int(parts[1])
    return minutes * 60 + seconds


# ============================================================================
# BASE TEST CLASSES
# ============================================================================

class BaseVelocityMarkerTests:
    """Base class for velocity marker tests (CV, VLT, VVO2) with shared logic."""

    @pytest.fixture
    def velocity_function(self):
        """Override in subclasses to specify which function to test."""
        raise NotImplementedError("Subclasses must implement velocity_function fixture")

    def test_boundary_valid_inputs(self, velocity_function, boundary_valid_cases):
        """Test velocity calculation with boundary valid inputs."""
        for distance, time, description in boundary_valid_cases:
            result = velocity_function(distance, time)
            assert result > 0, f"Result should be positive for {description}"

    def test_boundary_invalid_inputs(self, velocity_function, boundary_invalid_cases):
        """Test velocity calculation with boundary invalid inputs."""
        for distance, time, error_message in boundary_invalid_cases:
            with pytest.raises(ValueError, match=error_message):
                velocity_function(distance, time)

    def test_basic_invalid_inputs(self, velocity_function, basic_invalid_cases):
        """Test velocity calculation with basic invalid inputs."""
        for distance, time, error_message in basic_invalid_cases:
            with pytest.raises(ValueError, match=error_message):
                velocity_function(distance, time)

    def test_interpolated_distances(self, velocity_function, interpolated_distance_cases):
        """Test velocity calculation with interpolated distances."""
        for distance, time, description in interpolated_distance_cases:
            result = velocity_function(distance, time)
            assert result > 0, f"Result should be positive for {description}"


class BaseInputValidationTests:
    """Base class for functions that use input validation."""

    @pytest.fixture
    def function_under_test(self):
        """Override in subclasses to specify which function to test."""
        raise NotImplementedError("Subclasses must implement function_under_test fixture")

    def test_boundary_valid_inputs(self, function_under_test, boundary_valid_cases):
        """Test function with boundary valid inputs."""
        for distance, time, description in boundary_valid_cases:
            # Should not raise any exception
            result = function_under_test(distance, time)
            assert result is not None, f"Should return result for {description}"

    def test_boundary_invalid_inputs(self, function_under_test, boundary_invalid_cases):
        """Test function with boundary invalid inputs."""
        for distance, time, error_message in boundary_invalid_cases:
            with pytest.raises(ValueError, match=error_message):
                function_under_test(distance, time)

    def test_basic_invalid_inputs(self, function_under_test, basic_invalid_cases):
        """Test function with basic invalid inputs."""
        for distance, time, error_message in basic_invalid_cases:
            with pytest.raises(ValueError, match=error_message):
                function_under_test(distance, time)


# ============================================================================
# VELOCITY MARKER TESTS
# ============================================================================

class TestMcMillanCV(BaseVelocityMarkerTests):
    """Test Critical Velocity calculations."""

    @pytest.fixture
    def velocity_function(self):
        return calculate_cv

    @pytest.mark.parametrize("distance,time,expected_cv,description", [
        (400, 50, 176, "400m in 00:00:50"),
        (400, 80, 276, "400m in 00:01:20"),
        (400, 130, 437, "400m in 00:02:10"),
        (800, 115, 184, "800m in 00:01:55"),
        (800, 160, 253, "800m in 00:02:40"),
        (800, 255, 391, "800m in 00:04:15"),
        (1500, 235, 183, "1500m in 00:03:55"),
        (1500, 345, 263, "1500m in 00:05:45"),
        (1500, 570, 424, "1500m in 00:09:30"),
        (5000, 825, 171, "5k in 00:13:45"),
        (5000, 1275, 259, "5k in 00:21:15"),
        (5000, 2250, 445, "5k in 00:37:30"),
        (10000, 1755, 176, "10k in 00:29:15"),
        (10000, 2880, 279, "10k in 00:48:00"),
        (10000, 4680, 446, "10k in 01:18:00"),
        (21097, 4050, 181, "Half-marathon in 01:07:30"),
        (21097, 7050, 307, "Half-marathon in 01:57:30"),
        (21097, 10350, 442, "Half-marathon in 02:52:30"),
        (42195, 8280, 177, "Marathon in 02:18:00"),
        (42195, 15750, 325, "Marathon in 04:22:30"),
        (42195, 22500, 452, "Marathon in 06:15:00"),
    ])
    def test_known_values(self, distance, time, expected_cv, description):
        """Test CV calculation for known race performances with official McMillan values."""
        cv = calculate_cv(distance, time)
        assert cv == approx(expected_cv, rel=0.01), f"Failed for {description}"


class TestMcMillanVLT(BaseVelocityMarkerTests):
    """Test vLT calculations."""

    @pytest.fixture
    def velocity_function(self):
        return calculate_vlt

    @pytest.mark.parametrize("distance,time,expected_vlt,description", [
        (400, 50, 185, "400m in 00:50"),
        (400, 80, 287, "400m in 01:20"),
        (400, 130, 453, "400m in 02:10"),
        (800, 115, 194, "800m in 01:55"),
        (800, 160, 263, "800m in 02:40"),
        (800, 255, 408, "800m in 04:15"),
        (1500, 235, 192, "1500m in 03:55"),
        (1500, 345, 275, "1500m in 05:45"),
        (1500, 570, 441, "1500m in 09:30"),
        (5000, 825, 181, "5000m in 13:45"),
        (5000, 1275, 270, "5000m in 21:15"),
        (5000, 2250, 462, "5000m in 37:30"),
        (10000, 1755, 185, "10000m in 29:15"),
        (10000, 2880, 293, "10000m in 48:00"),
        (10000, 4680, 463, "10000m in 78:00"),
        (21097, 4050, 190, "21097m in 67:30"),
        (21097, 7050, 319, "21097m in 117:30"),
        (21097, 10350, 460, "21097m in 172:30"),
        (42195, 8280, 186, "42195m in 138:00"),
        (42195, 15750, 338, "42195m in 262:30"),
        (42195, 22500, 474, "42195m in 375:00"),
    ])
    def test_known_values(self, distance, time, expected_vlt, description):
        """Test vLT calculation for known race performances with expected values."""
        vlt = calculate_vlt(distance, time)
        assert vlt == approx(expected_vlt, rel=0.01), f"Failed for {description}"


class TestMcMillanVVO2(BaseVelocityMarkerTests):
    """Test vVO2 calculations."""

    @pytest.fixture
    def velocity_function(self):
        return calculate_vvo2

    @pytest.mark.parametrize("distance,time,expected_vvo2,description", [
        (400, 50, 162, "400m in 00:50"),
        (400, 80, 247, "400m in 01:20"),
        (400, 130, 386, "400m in 02:10"),
        (800, 115, 168, "800m in 01:55"),
        (800, 160, 227, "800m in 02:40"),
        (800, 255, 348, "800m in 04:15"),
        (1500, 235, 168, "1500m in 03:55"),
        (1500, 345, 237, "1500m in 05:45"),
        (1500, 570, 375, "1500m in 09:30"),
        (5000, 825, 157, "5000m in 13:45"),
        (5000, 1275, 234, "5000m in 21:15"),
        (5000, 2250, 392, "5000m in 37:30"),
        (10000, 1755, 161, "10000m in 29:15"),
        (10000, 2880, 252, "10000m in 48:00"),
        (10000, 4680, 393, "10000m in 78:00"),
        (21097, 4050, 166, "21097m in 67:30"),
        (21097, 7050, 275, "21097m in 117:30"),
        (21097, 10350, 390, "21097m in 172:30"),
        (42195, 8280, 162, "42195m in 138:00"),
        (42195, 15750, 290, "42195m in 262:30"),
        (42195, 22500, 402, "42195m in 375:00"),
    ])
    def test_known_values(self, distance, time, expected_vvo2, description):
        """Test vVO2 calculation for known race performances with expected values."""
        vvo2 = calculate_vvo2(distance, time)
        assert vvo2 == approx(expected_vvo2, rel=0.01), f"Failed for {description}"


# ============================================================================
# RACE TIME PREDICTION TESTS
# ============================================================================

class TestPredictRaceTimes(BaseInputValidationTests):
    """Test race time predictions."""

    @pytest.fixture
    def function_under_test(self):
        return predict_race_times

    @pytest.mark.parametrize("distance,time,expected_predictions,description", [
        (21097, 5400, {
            "1.5 Miles": "00:08:44",
            "1/2 Marathon": "01:30:00",
            "10 Miles": "01:07:28",
            "100 Miles": "18:13:36",
            "1000m": "00:03:18",
            "100km": "09:13:39",
            "100m": "00:00:16",
            "10km": "00:40:22",
            "12km": "00:49:04",
            "15 Miles": "01:44:08",
            "1500m": "00:05:10",
            "15km": "01:02:32",
            "1600m": "00:05:33",
            "2 Miles": "00:11:53",
            "20 Miles": "02:21:40",
            "2000m": "00:07:06",
            "200m": "00:00:32",
            "20km": "01:25:05",
            "25km": "01:48:07",
            "3 Miles": "00:18:37",
            "3000m": "00:11:03",
            "30km": "02:11:29",
            "3200m": "00:11:49",
            "4 Miles": "00:25:15",
            "4000m": "00:15:13",
            "400m": "00:01:08",
            "5 Miles": "00:32:13",
            "50 Miles": "07:00:13",
            "5000m": "00:19:26",
            "500m": "00:01:29",
            "50km": "03:49:45",
            "600m": "00:01:49",
            "8000m": "00:32:01",
            "800m": "00:02:30",
            "Marathon": "03:09:24",
            "Mile": "00:05:36",
        }, "Half marathon in 1:30:00"),
    ])
    def test_known_values(self, distance, time, expected_predictions, description):
        """Test race time predictions (±1% tolerance)."""
        predictions = predict_race_times(distance, time)

        for race_distance, expected_time in expected_predictions.items():
            assert race_distance in predictions, f"Should predict {race_distance} for {description}"

            expected_seconds = time_string_to_seconds(expected_time)
            actual_seconds = time_string_to_seconds(predictions[race_distance])

            assert actual_seconds == approx(expected_seconds, rel=0.01), \
                f"Failed prediction for {race_distance} in {description}: expected {expected_time}, got {predictions[race_distance]}"


# ============================================================================
# TRAINING PACES TESTS
# ============================================================================

class TestTrainingPaces(BaseInputValidationTests):
    """Test training pace calculations."""

    @pytest.fixture
    def function_under_test(self):
        return training_paces

    @pytest.mark.parametrize("distance,time,expected_paces,description", [
        (5000, 1200, {
            "endurance": {
                "easy_runs": {"pace": {"fast": "04:39", "slow": "05:17"}},
                "long_runs": {"pace": {"fast": "04:42", "slow": "05:28"}},
                "recovery_jogs": {"pace": {"fast": "05:20", "slow": "05:46"}},
            },
            "stamina": {
                "cruise_intervals": {
                    "distances": {
                        "400m": {"pace": {"fast": "04:02", "slow": "04:10"}, "split": {"fast": "01:37", "slow": "01:40"}},
                        "600m": {"pace": {"fast": "04:02", "slow": "04:10"}, "split": {"fast": "02:25", "slow": "02:30"}},
                        "800m": {"pace": {"fast": "04:02", "slow": "04:09"}, "split": {"fast": "03:14", "slow": "03:19"}},
                        "1000m": {"pace": {"fast": "04:02", "slow": "04:10"}, "split": {"fast": "04:02", "slow": "04:10"}},
                        "1200m": {"pace": {"fast": "04:02", "slow": "04:10"}, "split": {"fast": "04:51", "slow": "05:00"}},
                    },
                },
                "steady_state_runs": {"pace": {"fast": "04:20", "slow": "04:31"}},
                "tempo_intervals": {"pace": {"fast": "04:05", "slow": "04:14"}},
                "tempo_runs": {"pace": {"fast": "04:09", "slow": "04:18"}},
            },
            "speed": {
                "endurance_monster": {
                    "distances": {
                        "400m": {"pace": {"fast": "03:35", "slow": "03:47"}, "split": {"fast": "01:26", "slow": "01:30"}},
                        "600m": {"pace": {"fast": "03:40", "slow": "03:51"}, "split": {"fast": "02:12", "slow": "02:18"}},
                        "800m": {"pace": {"fast": "03:45", "slow": "03:55"}, "split": {"fast": "03:00", "slow": "03:08"}},
                        "1000m": {"pace": {"fast": "03:49", "slow": "04:01"}, "split": {"fast": "03:49", "slow": "04:01"}},
                        "1200m": {"pace": {"fast": "03:50", "slow": "04:04"}, "split": {"fast": "04:36", "slow": "04:53"}},
                        "1600m": {"pace": {"fast": "03:59", "slow": "04:06"}, "split": {"fast": "06:23", "slow": "06:34"}},
                    },
                },
                "speedster": {
                    "distances": {
                        "400m": {"pace": {"fast": "03:32", "slow": "03:43"}, "split": {"fast": "01:24", "slow": "01:29"}},
                        "600m": {"pace": {"fast": "03:33", "slow": "03:45"}, "split": {"fast": "02:08", "slow": "02:15"}},
                        "800m": {"pace": {"fast": "03:35", "slow": "03:46"}, "split": {"fast": "02:52", "slow": "03:01"}},
                        "1000m": {"pace": {"fast": "03:45", "slow": "03:54"}, "split": {"fast": "03:45", "slow": "03:54"}},
                        "1200m": {"pace": {"fast": "03:48", "slow": "03:55"}, "split": {"fast": "04:33", "slow": "04:42"}},
                        "1600m": {"pace": {"fast": "03:49", "slow": "04:01"}, "split": {"fast": "06:07", "slow": "06:26"}},
                    },
                },
            },
            "sprint": {
                "endurance_monster": {
                    "distances": {
                        "100m": {"pace": {"fast": "02:59", "slow": "03:17"}, "split": {"fast": "00:17", "slow": "00:19"}},
                        "200m": {"pace": {"fast": "03:03", "slow": "03:24"}, "split": {"fast": "00:36", "slow": "00:40"}},
                        "300m": {"pace": {"fast": "03:07", "slow": "03:34"}, "split": {"fast": "00:56", "slow": "01:04"}},
                        "400m": {"pace": {"fast": "03:10", "slow": "03:35"}, "split": {"fast": "01:16", "slow": "01:26"}},
                        "600m": {"pace": {"fast": "03:24", "slow": "03:40"}, "split": {"fast": "02:02", "slow": "02:12"}},
                    },
                },
                "speedster": {
                    "distances": {
                        "100m": {"pace": {"fast": "02:55", "slow": "03:13"}, "split": {"fast": "00:17", "slow": "00:19"}},
                        "200m": {"pace": {"fast": "02:59", "slow": "03:17"}, "split": {"fast": "00:35", "slow": "00:39"}},
                        "300m": {"pace": {"fast": "02:59", "slow": "03:31"}, "split": {"fast": "00:53", "slow": "01:03"}},
                        "400m": {"pace": {"fast": "03:07", "slow": "03:34"}, "split": {"fast": "01:15", "slow": "01:25"}},
                        "600m": {"pace": {"fast": "03:14", "slow": "03:35"}, "split": {"fast": "01:56", "slow": "02:09"}},
                    },
                },
            },
        }, "5K in 20:00"),
    ])
    def test_known_values(self, distance, time, expected_paces, description):
        """Test training paces for all zones, types, and distances (±1% tolerance)."""
        paces = training_paces(distance, time)

        for zone_name, expected_zone in expected_paces.items():
            assert zone_name in paces, f"Should contain {zone_name} zone for {description}"

            for type_name, expected_type in expected_zone.items():
                assert type_name in paces[zone_name]["types"], f"Should contain {type_name} type in {zone_name} zone for {description}"
                actual_type = paces[zone_name]["types"][type_name]

                # Check pace-only types (endurance and some stamina types)
                if "pace" in expected_type:
                    assert "pace" in actual_type, f"Should have pace for {type_name} in {zone_name} for {description}"

                    expected_fast_seconds = pace_string_to_seconds(expected_type["pace"]["fast"])
                    actual_fast_seconds = pace_string_to_seconds(actual_type["pace"]["fast"])
                    expected_slow_seconds = pace_string_to_seconds(expected_type["pace"]["slow"])
                    actual_slow_seconds = pace_string_to_seconds(actual_type["pace"]["slow"])

                    assert actual_fast_seconds == approx(expected_fast_seconds, rel=0.01), f"Failed fast pace for {type_name} in {zone_name} for {description}: expected {expected_type['pace']['fast']}, got {actual_type['pace']['fast']}"
                    assert actual_slow_seconds == approx(expected_slow_seconds, rel=0.01), f"Failed slow pace for {type_name} in {zone_name} for {description}: expected {expected_type['pace']['slow']}, got {actual_type['pace']['slow']}"

                # Check distance-based types (intervals in stamina, speed, and sprint zones)
                if "distances" in expected_type:
                    assert "distances" in actual_type, f"Should have distances for {type_name} in {zone_name} for {description}"

                    for distance_name, expected_distance in expected_type["distances"].items():
                        assert distance_name in actual_type["distances"], f"Should contain {distance_name} distance for {type_name} in {zone_name} for {description}"
                        actual_distance = actual_type["distances"][distance_name]

                        # Check pace values
                        if "pace" in expected_distance:
                            assert "pace" in actual_distance, f"Should have pace for {distance_name} in {type_name} for {description}"

                            expected_fast_seconds = pace_string_to_seconds(expected_distance["pace"]["fast"])
                            actual_fast_seconds = pace_string_to_seconds(actual_distance["pace"]["fast"])
                            expected_slow_seconds = pace_string_to_seconds(expected_distance["pace"]["slow"])
                            actual_slow_seconds = pace_string_to_seconds(actual_distance["pace"]["slow"])

                            assert actual_fast_seconds == approx(expected_fast_seconds, rel=0.01), f"Failed fast pace for {distance_name} {type_name} in {zone_name} for {description}: expected {expected_distance['pace']['fast']}, got {actual_distance['pace']['fast']}"
                            assert actual_slow_seconds == approx(expected_slow_seconds, rel=0.01), f"Failed slow pace for {distance_name} {type_name} in {zone_name} for {description}: expected {expected_distance['pace']['slow']}, got {actual_distance['pace']['slow']}"

                        # Check split values
                        if "split" in expected_distance:
                            assert "split" in actual_distance, f"Should have split for {distance_name} in {type_name} for {description}"

                            expected_fast_seconds = pace_string_to_seconds(expected_distance["split"]["fast"])
                            actual_fast_seconds = pace_string_to_seconds(actual_distance["split"]["fast"])
                            expected_slow_seconds = pace_string_to_seconds(expected_distance["split"]["slow"])
                            actual_slow_seconds = pace_string_to_seconds(actual_distance["split"]["slow"])

                            assert actual_fast_seconds == approx(expected_fast_seconds, rel=0.01), f"Failed fast split for {distance_name} {type_name} in {zone_name} for {description}: expected {expected_distance['split']['fast']}, got {actual_distance['split']['fast']}"
                            assert actual_slow_seconds == approx(expected_slow_seconds, rel=0.01), f"Failed slow split for {distance_name} {type_name} in {zone_name} for {description}: expected {expected_distance['split']['slow']}, got {actual_distance['split']['slow']}"

    @pytest.mark.parametrize("distance,time,description", [
        (4500, 900, "4500m in 15:00"),
        (444, 50, "444m in 50s"),
        (5001, 1200, "5001m in 20:00"),
    ])
    def test_non_standard_distance_interpolation(self, distance, time, description):
        """Test training paces with non-standard distance to exercise interpolation code paths."""

        # Call the function - this should exercise the interpolation paths
        paces = training_paces(distance, time)

        # Basic validation that we get a valid result structure
        assert isinstance(paces, dict), "Should return a dictionary"
        for zone_name in ["endurance", "stamina", "speed", "sprint"]:
            assert zone_name in paces, f"Should contain {zone_name} zone"
            assert "description" in paces[zone_name], f"Zone {zone_name} should have description"
            assert "types" in paces[zone_name], f"Zone {zone_name} should have types"
            assert isinstance(paces[zone_name]["types"], dict), f"Zone {zone_name} types should be a dict"

        # Check that endurance zone has pace-only types
        endurance_types = paces["endurance"]["types"]
        for type_name in ["easy_runs", "long_runs", "recovery_jogs"]:
            assert type_name in endurance_types, f"Endurance should have {type_name}"
            assert "pace" in endurance_types[type_name], f"{type_name} should have pace"
            assert "fast" in endurance_types[type_name]["pace"], f"{type_name} pace should have fast"
            assert "slow" in endurance_types[type_name]["pace"], f"{type_name} pace should have slow"
            fast_pace_in_sec = pace_string_to_seconds(endurance_types[type_name]["pace"]["fast"])
            assert fast_pace_in_sec > 0, f"Fast pace for {type_name} should be positive, got {fast_pace_in_sec}"
            slow_pace_in_sec = pace_string_to_seconds(endurance_types[type_name]["pace"]["slow"])
            assert slow_pace_in_sec > fast_pace_in_sec, f"Slow pace for {type_name} should be slower than fast pace, want >{fast_pace_in_sec}, got {slow_pace_in_sec}"

        # Check that interval zones have distance-based types
        for zone_name in ["stamina", "speed", "sprint"]:
            zone_types = paces[zone_name]["types"]
            for type_name, type_data in zone_types.items():
                if "distances" in type_data:
                    assert isinstance(type_data["distances"], dict), f"{type_name} distances should be a dict"
                    # Check that each distance has pace and split
                    for dist_name, dist_data in type_data["distances"].items():
                        for key in ["pace", "split"]:
                            assert key in dist_data, f"{dist_name} should have pace"
                            assert "fast" in dist_data[key], f"{dist_name} {key} should have fast"
                            assert "slow" in dist_data[key], f"{dist_name} {key} should have slow"
                            fast_in_sec = pace_string_to_seconds(dist_data[key]["fast"])
                            assert fast_in_sec > 0, f"Fast {key} for {dist_name} {type_name} should be positive, got {fast_in_sec}"
                            slow_in_sec = pace_string_to_seconds(dist_data[key]["slow"])
                            assert slow_in_sec > fast_in_sec, f"Slow {key} for {dist_name} {type_name} should be slower than fast {key}, want >{fast_in_sec}, got {slow_in_sec}"

# ============================================================================
# FORMATTING TESTS
# ============================================================================

class TestFormatting:
    """Test formatting functions."""

    @pytest.mark.parametrize("seconds,expected,description", [
        (300, "05:00", "normal pace (5:00/km)"),
        (3930, "01:05:30", "pace over 1 hour"),
        (210, "03:30", "fast pace"),
    ])
    def test_format_pace_ms(self, seconds, expected, description):
        """Test MM:SS pace formatting."""
        assert format_pace_ms(seconds) == expected, f"Failed for {description}"

    @pytest.mark.parametrize("seconds,expected,description", [
        (300, "00:05:00", "normal pace (5:00/km)"),
        (3930, "01:05:30", "pace over 1 hour"),
        (210, "00:03:30", "fast pace"),
    ])
    def test_format_pace_hms(self, seconds, expected, description):
        """Test HH:MM:SS pace formatting."""
        assert format_pace_hms(seconds) == expected, f"Failed for {description}"

    def test_format_pace(self):
        """Test pace range formatting."""
        result = format_pace(300, 330)  # 5:00 to 5:30 per km

        assert isinstance(result, dict), "Should return a dictionary"
        assert result["fast"] == "05:00"
        assert result["slow"] == "05:30"
        assert result["format"] == "MM:SS/km"

    def test_format_split(self):
        """Test split time formatting."""
        result = format_split(90, 100, 400)  # 1:30 to 1:40 for 400m

        assert isinstance(result, dict), "Should return a dictionary"
        assert result["fast"] == "01:30"
        assert result["slow"] == "01:40"
        assert result["format"] == "MM:SS/400m"

    def test_format_pace_and_time(self):
        """Test combined pace and time formatting."""
        result = format_pace_and_time(4.0, 3.5, 400)  # 4.0 m/s to 3.5 m/s for 400m

        assert isinstance(result, dict), "Should return a dictionary"
        assert "split" in result, "Should have split times"
        assert "pace" in result, "Should have pace"
        assert isinstance(result["split"], dict), "Split should be a dictionary"
        assert isinstance(result["pace"], dict), "Pace should be a dictionary"


# ============================================================================
# UTILITY FUNCTION TESTS
# ============================================================================

class TestUtilityFunctions:
    """Test utility and helper functions."""

    def test_normalize_time_same_distance(self):
        """Test time normalization when distances are the same."""
        normalized = _normalize_time(5000, 1200, 5000)
        assert normalized == 1200, "Should return same time for same distance"

    def test_normalize_time_different_distances(self):
        """Test time normalization between different distances."""
        normalized = _normalize_time(5000, 1200, 10000)  # 5K to 10K

        assert normalized > 1200, "10K time should be longer than 5K time"
        expected = 1200 * ((10000 / 5000) ** 1.06)  # Riegel's formula
        assert normalized == approx(expected, rel=0.001), "Should match Riegel's formula"

    @pytest.mark.parametrize("distance,time,description", [
        (5000, 1200, "normal inputs"),
        (400, 60, "minimum valid distance"),
        (160934, 50000, "maximum valid distance"),
    ])
    def test_assert_inputs_valid(self, distance, time, description):
        """Test input validation with valid inputs."""
        # Should not raise any exception
        _assert_inputs(distance, time)

    @pytest.mark.parametrize("distance,time,error_message,description", [
        (-1000, 1200, "Distance must be positive", "negative distance"),
        (5000, -120, "Time must be positive", "negative time"),
        (399, 60, "Distance too short", "distance too short"),
        (5000, 250, "Pace appears unrealistically fast", "unrealistically fast pace"),
    ])
    def test_assert_inputs_invalid(self, distance, time, error_message, description):
        """Test input validation with invalid inputs."""
        with pytest.raises(ValueError, match=error_message):
            _assert_inputs(distance, time)


# ============================================================================
# HEART RATE ZONES TESTS
# ============================================================================

class TestHeartRateZones:
    """Test heart rate zone calculations."""

    @pytest.mark.parametrize("age,resting_hr,max_hr,expected_estimated_max,expected_zones,description", [
        (30, 60, 190, 187, {
            "endurance": {
                "easy_runs": {"hrmax": (114, 162), "hrreserve": (132, 161)},
                "long_runs": {"hrmax": (114, 162), "hrreserve": (132, 161)}
            },
            "stamina": {
                "steady_state_runs": {"hrmax": (158, 165), "hrreserve": (158, 164)},
                "tempo_runs": {"hrmax": (162, 171), "hrreserve": (164, 170)},
                "tempo_intervals": {"hrmax": (165, 175), "hrreserve": (167, 173)},
                "cruise_intervals": {"hrmax": (165, 175), "hrreserve": (170, 177)}
            },
            "speed": {
                "endurance_monster": {"hrmax": (171, 190), "hrreserve": (177, 190)},
                "speedster": {"hrmax": (171, 190), "hrreserve": (177, 190)}
            },
            "sprint": {
                "endurance_monster": {"hrmax": (171, 190), "hrreserve": (177, 190)},
                "speedster": {"hrmax": (171, 190), "hrreserve": (177, 190)}
            }
        }, "30-year-old with 60 BPM resting HR and 190 BPM max HR"),

        (45, 50, 175, 177, {
            "endurance": {
                "easy_runs": {"hrmax": (105, 149), "hrreserve": (119, 148)},
                "long_runs": {"hrmax": (105, 149), "hrreserve": (119, 148)}
            },
            "stamina": {
                "steady_state_runs": {"hrmax": (145, 152), "hrreserve": (144, 150)},
                "tempo_runs": {"hrmax": (149, 158), "hrreserve": (150, 156)},
                "tempo_intervals": {"hrmax": (152, 161), "hrreserve": (152, 159)},
                "cruise_intervals": {"hrmax": (152, 161), "hrreserve": (156, 162)}
            },
            "speed": {
                "endurance_monster": {"hrmax": (158, 175), "hrreserve": (162, 175)},
                "speedster": {"hrmax": (158, 175), "hrreserve": (162, 175)}
            },
            "sprint": {
                "endurance_monster": {"hrmax": (158, 175), "hrreserve": (162, 175)},
                "speedster": {"hrmax": (158, 175), "hrreserve": (162, 175)}
            }
        }, "45-year-old with 50 BPM resting HR and 175 BPM max HR"),

        (45, 50, None, 177, {
            "endurance": {
                "easy_runs": {"hrmax": (106, 150), "hrreserve": (120, 149)},
                "long_runs": {"hrmax": (106, 150), "hrreserve": (120, 149)}
            },
            "stamina": {
                "steady_state_runs": {"hrmax": (147, 154), "hrreserve": (145, 152)},
                "tempo_runs": {"hrmax": (150, 159), "hrreserve": (152, 158)},
                "tempo_intervals": {"hrmax": (154, 163), "hrreserve": (154, 160)},
                "cruise_intervals": {"hrmax": (154, 163), "hrreserve": (158, 164)}
            },
            "speed": {
                "endurance_monster": {"hrmax": (159, 177), "hrreserve": (164, 177)},
                "speedster": {"hrmax": (159, 177), "hrreserve": (164, 177)}
            },
            "sprint": {
                "endurance_monster": {"hrmax": (159, 177), "hrreserve": (164, 177)},
                "speedster": {"hrmax": (159, 177), "hrreserve": (164, 177)}
            }
        }, "45-year-old with 50 BPM resting HR and no max HR"),
    ])
    def test_known_values(self, age, resting_hr, max_hr, expected_estimated_max, expected_zones, description):
        """Test heart rate zone calculations for known values."""

        zones = heart_rate_zones(age=age, resting_heart_rate=resting_hr, max_heart_rate=max_hr)

        actual_estimated_max = zones["estimated_max_heart_rate"]
        assert actual_estimated_max == expected_estimated_max, f"Effective Max Heart Rate: expected {expected_estimated_max}, got {actual_estimated_max}"

        expected_effective_max = max_hr
        if expected_effective_max is None:
            expected_effective_max = expected_estimated_max
        actual_effective_max = zones["effective_max_heart_rate"]
        assert actual_effective_max == expected_effective_max, f"Estimated Max Heart Rate: expected {expected_effective_max}, got {actual_effective_max}"

        expected_resting = resting_hr
        actual_resting = zones["resting_heart_rate"]
        assert actual_resting == expected_resting, f"Resting Heart Rate: expected {expected_resting}, got {actual_resting}"

        for zone_name, expected_zone in expected_zones.items():
            assert zone_name in zones["zones"], f"Should contain {zone_name} zone for {description}"
            actual_zone = zones["zones"][zone_name]

            for type_name, expected_type in expected_zone.items():
                assert type_name in actual_zone["types"], f"Should contain {type_name} in {zone_name} for {description}"
                actual_type = actual_zone["types"][type_name]

                # Check HRMAX values
                expected_hrmax_min, expected_hrmax_max = expected_type["hrmax"]
                expected_hrmax_range = f"{expected_hrmax_min}-{expected_hrmax_max} BPM"

                actual_hrmax_min = actual_type["hrmax"]["min"]
                actual_hrmax_max = actual_type["hrmax"]["max"]
                actual_hrmax_range = f"{actual_hrmax_min}-{actual_hrmax_max} BPM"

                assert actual_hrmax_min == expected_hrmax_min, \
                    f"HRMAX min for {type_name} in {zone_name} for {description}: expected {expected_hrmax_min}, got {actual_hrmax_min}"
                assert actual_hrmax_max == expected_hrmax_max, \
                    f"HRMAX max for {type_name} in {zone_name} for {description}: expected {expected_hrmax_max}, got {actual_hrmax_max}"
                assert actual_hrmax_range == expected_hrmax_range, \
                    f"HRMAX range for {type_name} in {zone_name} for {description}: expected {expected_hrmax_range}, got {actual_hrmax_range}"

                # Check HRRESERVE values
                expected_hrreserve_min, expected_hrreserve_max = expected_type["hrreserve"]
                expected_hrreserve_range = f"{expected_hrreserve_min}-{expected_hrreserve_max} BPM"

                actual_hrreserve_min = actual_type["hrreserve"]["min"]
                actual_hrreserve_max = actual_type["hrreserve"]["max"]
                actual_hrreserve_range = f"{actual_hrreserve_min}-{actual_hrreserve_max} BPM"

                assert actual_hrreserve_min == expected_hrreserve_min, \
                    f"HRRESERVE min for {type_name} in {zone_name} for {description}: expected {expected_hrreserve_min}, got {actual_hrreserve_min}"
                assert actual_hrreserve_max == expected_hrreserve_max, \
                    f"HRRESERVE max for {type_name} in {zone_name} for {description}: expected {expected_hrreserve_max}, got {actual_hrreserve_max}"
                assert actual_hrreserve_range == expected_hrreserve_range, \
                    f"HRRESERVE range for {type_name} in {zone_name} for {description}: expected {expected_hrreserve_range}, got {actual_hrreserve_range}"

    @pytest.mark.parametrize("age,resting_hr,max_hr,error_message,description", [
        (0, 60, None, "Age must be positive", "zero age"),
        (-30, 60, None, "Age must be positive", "negative age"),
        (30, 0, None, "Resting heart rate must be positive", "zero resting heart rate"),
        (30, -60, None, "Resting heart rate must be positive", "negative resting heart rate"),
        (30, 60, 0, "Max heart rate must be positive", "zero max heart rate"),
        (30, 60, -190, "Max heart rate must be positive", "negative max heart rate"),
    ])
    def test_invalid_inputs(self, age, resting_hr, max_hr, error_message, description):
        """Test heart rate zone calculations with invalid inputs."""
        with pytest.raises(ValueError, match=error_message):
            heart_rate_zones(age=age, resting_heart_rate=resting_hr, max_heart_rate=max_hr)