"""
McMillan Running Calculator Implementation

Based on Greg McMillan's methodology for predicting race times and training paces.
The McMillan method uses Critical Velocity (CV) as the foundation for predictions,
which represents the theoretical maximum pace that can be sustained indefinitely.

References:
- McMillan Running Calculator: https://www.mcmillanrunning.com/
- McMillan, G. (2013). "YOU (Only Faster): Training plans to help you train smarter and run faster"

Note: This implementation closely approximates McMillan's calculations based on
publicly available information.
"""

import numpy as np
import os
import joblib

# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class McMillanCalculationError(Exception):
    """Base exception for McMillan calculation errors."""
    pass


class ModelNotFoundError(McMillanCalculationError):
    """Raised when a required model is not found."""
    pass


class InvalidInputError(McMillanCalculationError, ValueError):
    """Raised when input parameters are invalid."""
    pass


class ModelLoadingError(McMillanCalculationError):
    """Raised when model loading fails."""
    pass


class PredictionError(McMillanCalculationError):
    """Raised when model prediction fails."""
    pass


# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

# Heart rate estimation formulas
MAX_HR_FORMULAS = {
    'londeree': lambda age: 206.3 - (0.711 * age),
    'miller': lambda age: 217 - (0.85 * age),
    'jackson': lambda age: 206.9 - (0.67 * age),
    'whyte': lambda age: 202 - (0.55 * age),
    'oakland': lambda age: 191.5 - (0.007 * (age * age)),
    'tanaka': lambda age: 208 - (0.7 * age),
    'wisloff': lambda age: 211 - (0.64 * age),
    'robergs': lambda age: 205.8 - (0.685 * age),
}

# Standard race distances for predictions
RACE_DISTANCES = {
    "100m": 100, "200m": 200, "400m": 400, "500m": 500, "600m": 600, "800m": 800,
    "1000m": 1000, "1500m": 1500, "1600m": 1600, "Mile": 1609, "2000m": 2000,
    "1.5 Miles": 2414, "3000m": 3000, "3200m": 3200, "2 Miles": 3219, "4000m": 4000,
    "3 Miles": 4828, "5000m": 5000, "6000m": 6000, "4 Miles": 6437, "8000m": 8000,
    "5 Miles": 8047, "10km": 10000, "12km": 12000, "15km": 15000, "10 Miles": 16093,
    "20km": 20000, "1/2 Marathon": 21097, "15 Miles": 24140, "25km": 25000,
    "30km": 30000, "20 Miles": 32187, "Marathon": 42195, "50km": 50000,
    "50 Miles": 80467, "100km": 100000, "100 Miles": 160934,
}

# Heart rate zone definitions
HR_ZONE_DEFINITIONS = {
    "endurance": {
        "recovery_jogs": {"hrmax": (60, 70), "hrreserve": (55, 65), "description": ""},
        "long_runs": {"hrmax": (60, 85), "hrreserve": (55, 78), "description": "Long aerobic runs to build endurance"},
        "easy_runs": {"hrmax": (60, 85), "hrreserve": (55, 78), "description": "Comfortable aerobic base runs"}
    },
    "stamina": {
        "steady_state_runs": {"hrmax": (83, 87), "hrreserve": (75, 80), "description": "Easy-Moderate continuous runs"},
        "tempo_runs": {"hrmax": (85, 90), "hrreserve": (80, 85), "description": "Moderate pace continuous runs"},
        "tempo_intervals": {"hrmax": (87, 92), "hrreserve": (82, 87), "description": "Moderate pace repetitions with short recovery jogs"},
        "cruise_intervals": {"hrmax": (87, 92), "hrreserve": (85, 90), "description": "Moderate pace repetitions with very short recovery jogs"}
    },
    "speed": {
        "endurance_monster": {"hrmax": (90, 100), "hrreserve": (90, 100), "description": "Speed training for endurance-focused athletes"},
        "speedster": {"hrmax": (90, 100), "hrreserve": (90, 100), "description": "Speed training for speed-focused athletes"}
    },
    "sprint": {
        "endurance_monster": {"hrmax": (90, 100), "hrreserve": (90, 100), "description": "Sprint training for endurance-focused athletes"},
        "speedster": {"hrmax": (90, 100), "hrreserve": (90, 100), "description": "Sprint training for speed-focused athletes"}
    }
}

# Training zone name mappings
ZONE_NAME_MAPPINGS = {
    'endurance': {'recovery': 'recovery_jogs', 'easy': 'easy_runs', 'long': 'long_runs'},
    'stamina': {'steady-state_runs': 'steady_state_runs', 'tempo': 'tempo_runs', 'tempo_interval': 'tempo_intervals'}
}

# Training zone descriptions
ZONE_DESCRIPTIONS = {
    'recovery_jogs': "Very easy recovery runs",
    'easy_runs': "Comfortable aerobic base runs",
    'long_runs': "Long aerobic runs to build endurance",
    'steady_state_runs': "Easy-Moderate continuous runs",
    'tempo_runs': "Moderate pace continuous runs",
    'tempo_intervals': "Moderate pace repetitions with short recovery jogs"
}

# Validation constants
VALIDATION_LIMITS = {
    'min_distance': 400,  # meters
    'max_distance': 160934,  # meters (100 miles)
    'min_pace_per_km': 60,  # seconds (1:00/km)
    'max_pace_per_km': 1200,  # seconds (20:00/km)
}

# Riegel's formula exponent
RIEGEL_EXPONENT = 1.06

def calculate_vlt(distance_meters: float, time_seconds: float) -> int:
    """
    Calculate Velocity at Lactate Threshold (VLT) from a race performance.

    Args:
        distance_meters: Race distance in meters.
        time_seconds: Race time in seconds.

    Returns:
        int: Lactate Threshold Pace (vLT) in seconds per kilometer.

    Raises:
        InvalidInputError: If distance or time is not positive or if inputs are unrealistic.
    """
    return _calculate_velocity_marker(distance_meters, time_seconds, 'vLT')


def calculate_cv(distance_meters: float, time_seconds: float) -> int:
    """
    Calculate Critical Velocity (CV) from a race performance using our functional models.

    Args:
        distance_meters: Race distance in meters.
        time_seconds: Race time in seconds.

    Returns:
        float: Critical Velocity Pace (CV) in seconds per kilometer.

    Raises:
        InvalidInputError: If distance or time is not positive or if inputs are unrealistic.
    """

    return _calculate_velocity_marker(distance_meters, time_seconds, 'CV')


def calculate_vvo2(distance_meters: float, time_seconds: float) -> int:
    """
    Calculate Velocity at V̇O₂max (VVO2) from a race performance.

    Args:
        distance_meters: Race distance in meters.
        time_seconds: Race time in seconds.

    Returns:
        int: VO2Max Pace (vVO2Max) in seconds per kilometer.

    Raises:
        InvalidInputError: If distance or time is not positive or if inputs are unrealistic.
    """
    return _calculate_velocity_marker(distance_meters, time_seconds, 'vVO2')


def predict_race_times(distance_meters: float, time_seconds: float) -> dict:
    """
    Predict race times for all standard distances based on a single race performance
    using our event-specific functional models.

    This version normalizes the input time to match the model's base distance
    using Riegel's formula if the input race distance is not one of the standard distances.

    Args:
        distance_meters: Race distance in meters (input for the model).
        time_seconds: Race time in seconds (input for the model).

    Returns:
        dict: Dictionary with distance names as keys and predicted times as values
              in HH:MM:SS format.

    Raises:
        InvalidInputError: If distance or time is not positive or if inputs are unrealistic.
    """

    _assert_inputs(distance_meters, time_seconds)

    available_input_distances = _available_model_distances("race_times")
    (normalized_distance, normalized_time) = _normalize_inputs(available_input_distances, distance_meters, time_seconds)

    predicted_race_times = {}
    for race_name, output_distance in RACE_DISTANCES.items():
        # If the race to predict is the user's input race, just use the original time
        if output_distance == int(distance_meters):
            predicted_race_times[race_name] = format_pace_hms(time_seconds)
            continue

        model = _get_race_time_model(normalized_distance, race_name)

        try:
            predicted_time = _predict_with_model(normalized_time, model)
            if not np.isnan(predicted_time):
                predicted_race_times[race_name] = format_pace_hms(predicted_time)
        except Exception:
            continue

    return predicted_race_times


def _calculate_velocity_marker(distance_meters: float, time_seconds: float, marker_type: str) -> int:
    _assert_inputs(distance_meters, time_seconds)

    available_input_distances = _available_model_distances("velocity_markers")
    (normalized_distance, normalized_time) = _normalize_inputs(available_input_distances, distance_meters, time_seconds)

    # Load the functional model for the determined base distance and marker type
    model = _get_velocity_marker_model(normalized_distance, marker_type)

    # Predict VLT using the functional model
    marker = _predict_with_model(normalized_time, model)
    if np.isnan(marker):
        raise InvalidInputError(f"Failed to predict {marker_type} using model.")

    return round(marker)


def _assert_inputs(distance_meters: float, time_seconds: float):
    """
    Validate input parameters for distance and time.

    Args:
        distance_meters: Race distance in meters
        time_seconds: Race time in seconds

    Raises:
        InvalidInputError: If inputs are invalid or unrealistic
    """
    if distance_meters <= 0:
        raise InvalidInputError("Distance must be positive")
    if time_seconds <= 0:
        raise InvalidInputError("Time must be positive")

    # Add realistic range checking for distance
    if distance_meters < VALIDATION_LIMITS['min_distance']:
        raise InvalidInputError(f"Distance too short, must be at least {VALIDATION_LIMITS['min_distance']}m for meaningful calculations")
    if distance_meters > VALIDATION_LIMITS['max_distance']:
        raise InvalidInputError(f"Distance too long, must be less than {VALIDATION_LIMITS['max_distance']/1609.344:.0f} miles for this calculation method")

    # Check for unrealistic paces
    pace_per_km = time_seconds / (distance_meters / 1000)
    if pace_per_km < VALIDATION_LIMITS['min_pace_per_km']:
        min_pace_formatted = f"{VALIDATION_LIMITS['min_pace_per_km']//60}:{VALIDATION_LIMITS['min_pace_per_km']%60:02d}"
        raise InvalidInputError(f"Pace appears unrealistically fast (faster than {min_pace_formatted}/km)")
    if pace_per_km > VALIDATION_LIMITS['max_pace_per_km']:
        max_pace_formatted = f"{VALIDATION_LIMITS['max_pace_per_km']//60}:{VALIDATION_LIMITS['max_pace_per_km']%60:02d}"
        raise InvalidInputError(f"Pace appears unrealistically slow (slower than {max_pace_formatted}/km)")


def _available_model_distances(model_type: str) -> list:
    """
    Returns a sorted list of available input distances for which we have functional models.
    This is used to determine the closest model base distance for normalization and prediction.
    """
    return _model_manager.get_available_distances(model_type)


class ModelManager:
    """
    Manages loading, caching, and access to McMillan calculation models.

    This class provides a centralized way to handle model loading with proper
    error handling, validation, and lazy loading capabilities.
    """

    def __init__(self):
        self._models = {}
        self._loaded = False
        self._model_path = os.path.join(os.path.dirname(__file__), "mcmillan.pkl")

    def _ensure_models_loaded(self):
        """Ensure models are loaded, loading them if necessary."""
        if not self._loaded:
            self._load_models()

    def _load_models(self):
        """
        Load all models from the pickle file with comprehensive error handling.

        Raises:
            ModelLoadingError: If model loading fails
        """
        try:
            self._models = joblib.load(self._model_path)
            if not self._models:
                raise ModelLoadingError("Loaded models dictionary is empty")

            # Validate required model categories
            required_categories = ["velocity_markers", "race_times", "training_paces"]
            missing_categories = [cat for cat in required_categories if cat not in self._models]
            if missing_categories:
                raise ModelLoadingError(f"Missing required model categories: {missing_categories}")

            self._loaded = True

        except FileNotFoundError:
            raise ModelLoadingError(f"Models file not found at {self._model_path}")
        except joblib.externals.loky.process_executor.TerminatedWorkerError:
            raise ModelLoadingError(f"Failed to deserialize models file at {self._model_path} - file may be corrupted")
        except Exception as e:
            raise ModelLoadingError(f"Unexpected error loading models: {e}")

    def get_model(self, model_category: str, input_distance: int, model_key: str):
        """
        Retrieve a model from the loaded models with comprehensive error handling.

        Args:
            model_category: Category of model ('velocity_markers', 'race_times', etc.)
            input_distance: Distance in meters for which to retrieve the model
            model_key: Specific model key (marker type, event name, etc.)

        Returns:
            dict: The model parameters for the specified key

        Raises:
            ModelNotFoundError: If the requested model is not found
        """
        self._ensure_models_loaded()

        if model_category not in self._models:
            available_categories = list(self._models.keys())
            raise ModelNotFoundError(f"Model category '{model_category}' not found. Available categories: {available_categories}")

        if input_distance not in self._models[model_category]:
            available_distances = sorted(self._models[model_category].keys())
            raise ModelNotFoundError(f"No models found for distance {input_distance}m in category '{model_category}'. Available distances: {available_distances}")

        if model_key not in self._models[model_category][input_distance]:
            available_keys = list(self._models[model_category][input_distance].keys())
            raise ModelNotFoundError(f"Model key '{model_key}' not found for {input_distance}m in category '{model_category}'. Available keys: {available_keys}")

        return self._models[model_category][input_distance][model_key]

    def get_available_distances(self, model_category: str) -> list:
        """
        Get available distances for a specific model category.

        Args:
            model_category: Category of model to check

        Returns:
            list: Sorted list of available distances

        Raises:
            ModelNotFoundError: If model category is not found
        """
        self._ensure_models_loaded()

        if model_category not in self._models:
            available_categories = list(self._models.keys())
            raise ModelNotFoundError(f"Model category '{model_category}' not found. Available categories: {available_categories}")

        distances = sorted(self._models[model_category].keys())
        if not distances:
            raise ModelNotFoundError(f"No models available for {model_category}.")

        return distances

    def get_training_pace_zones(self) -> list:
        """
        Get all available training pace zone keys.

        Returns:
            list: List of zone keys (tuples) available in the training pace models
        """
        self._ensure_models_loaded()

        if "training_paces" not in self._models:
            return []

        return list(self._models["training_paces"].keys())

    def get_training_pace_models(self, zone_key):
        """
        Get training pace models for a specific zone key.

        Args:
            zone_key: Tuple of (zone_group, zone_type, zone_distance)

        Returns:
            dict: Distance models for the zone key, or None if not found
        """
        self._ensure_models_loaded()

        try:
            return self.get_model("training_paces", zone_key, "models")
        except ModelNotFoundError:
            # Handle the case where training_paces are stored directly by zone_key
            if "training_paces" in self._models and zone_key in self._models["training_paces"]:
                return self._models["training_paces"][zone_key]
            return None

    @property
    def is_loaded(self) -> bool:
        """Check if models are loaded."""
        return self._loaded

    def reload_models(self):
        """Force reload of models from file."""
        self._loaded = False
        self._models = {}
        self._ensure_models_loaded()


# Global model manager instance
_model_manager = ModelManager()

def _normalize_inputs(available_distances: dict, distance_meters: int, time_seconds: int) -> tuple[int, int]:
    """
    Normalizes the inputs for the model prediction.

    Args:
        distance_meters: Distance in meters for which to retrieve the model.

    Returns:
        dict: A dictionary containing the normalized time in seconds
    """

    # Find the closest input distance for which we have a model set. This will be our base model.
    normalized_distance = min(available_distances, key=lambda x: abs(x - distance_meters))

    if distance_meters == normalized_distance:
        return (normalized_distance, time_seconds)

    normalized_time = _normalize_time(distance_meters, time_seconds, normalized_distance)
    return (normalized_distance, normalized_time)


def _get_model(model_category: str, input_distance: int, model_key: str):
    """
    Generic function to retrieve a model from the loaded models.

    Args:
        model_category: Category of model ('velocity_markers', 'race_times', etc.)
        input_distance: Distance in meters for which to retrieve the model
        model_key: Specific model key (marker type, event name, etc.)

    Returns:
        dict: The model parameters for the specified key

    Raises:
        ModelNotFoundError: If the requested model is not found
    """
    return _model_manager.get_model(model_category, input_distance, model_key)


def _get_velocity_marker_model(input_distance: int, marker_type: str):
    """
    Retrieves a model to predict velocity markers for a specific input distance and marker type.

    Args:
        input_distance: Distance in meters for which to retrieve the model.
        marker_type: Type of velocity marker (e.g., 'vLT', 'CV', 'vVO2').

    Returns:
        dict: The model parameters for the specified marker type.
    """
    return _get_model("velocity_markers", input_distance, marker_type)


def _get_race_time_model(input_distance: int, event_name: str):
    """
    Retrieves a model to predict race times for a specific input distance and event name.

    Args:
        input_distance: Distance in meters for which to retrieve the model.
        event_name: Name of the event (e.g., 'marathon', '5000m').

    Returns:
        dict: The model parameters for the specified event name.
    """
    return _get_model("race_times", input_distance, event_name)


def _predict_with_model(input_time: float, model_params: dict) -> float:
    """
    Predict a value using the specified model parameters.

    Args:
        input_time: Input time in seconds
        model_params: Model parameters dictionary

    Returns:
        float: Predicted value

    Raises:
        PredictionError: If prediction fails or produces invalid results
    """
    if not isinstance(model_params, dict):
        raise PredictionError(f"Model parameters must be a dictionary, got {type(model_params)}")

    if 'type' not in model_params:
        raise PredictionError("Model parameters missing 'type' field")

    if model_params['type'] == 'polynomial':
        if 'coefficients' not in model_params:
            raise PredictionError("Polynomial model missing 'coefficients' field")

        try:
            poly_func = np.poly1d(model_params['coefficients'])
            result = float(poly_func(input_time))

            if np.isnan(result) or np.isinf(result):
                raise PredictionError(f"Model prediction resulted in invalid value: {result}")

            return result
        except Exception as e:
            raise PredictionError(f"Failed to predict using polynomial model: {e}")
    else:
        raise PredictionError(f"Unsupported model type: {model_params['type']}")


def _normalize_time(distance_meters: float, time_seconds: float, target_distance: float) -> float:
    """
    Normalizes a race time from one distance to an equivalent time at a target distance
    using Riegel's formula.

    Riegel's formula: T2 = T1 * (D2 / D1)^1.06

    Args:
        distance_meters: Original race distance in meters.
        time_seconds: Original race time in seconds.
        target_distance: The distance in meters to which the time should be normalized.

    Returns:
        float: The equivalent time in seconds for the target distance.
    """
    # Avoid division by zero if distances are the same, though this case should be handled by caller
    if distance_meters == target_distance:
        return time_seconds

    # Apply Riegel's formula
    normalized_time = time_seconds * ((target_distance / distance_meters) ** RIEGEL_EXPONENT)
    return normalized_time


def _get_training_pace_models(zone_key):
    """
    Get training pace models for a specific zone key using the unified model system.

    Args:
        zone_key: Tuple of (zone_group, zone_type, zone_distance)

    Returns:
        dict: Distance models for the zone key, or None if not found
    """
    return _model_manager.get_training_pace_models(zone_key)


def _interpolate_training_pace(zone_key, input_distance: float, input_time: float):
    """
    Interpolate training pace for a specific zone using polynomial models.

    Args:
        zone_key: Tuple of (zone_group, zone_type, zone_distance)
        input_distance: Race distance in meters
        input_time: Race time in seconds

    Returns:
        Tuple of (fast_pace_seconds, slow_pace_seconds) or None if not available
    """
    distance_models = _get_training_pace_models(zone_key)
    if distance_models is None:
        return None

    available_distances = sorted(distance_models.keys())
    if not available_distances:
        return None

    # If exact distance is available, use it directly
    if input_distance in distance_models:
        return _predict_pace_from_models(input_time, distance_models[input_distance])

    # Check if distance is within the available range
    if input_distance < available_distances[0] or input_distance > available_distances[-1]:
        # Use nearest distance
        nearest_dist = min(available_distances, key=lambda x: abs(x - input_distance))
        return _predict_pace_from_models(input_time, distance_models[nearest_dist])

    # Interpolate between two distances
    lower_dist, upper_dist = _find_interpolation_bounds(available_distances, input_distance)

    if lower_dist is None or upper_dist is None:
        # Fallback to nearest distance
        nearest_dist = min(available_distances, key=lambda x: abs(x - input_distance))
        return _predict_pace_from_models(input_time, distance_models[nearest_dist])

    # Perform interpolation
    return _interpolate_between_distances(
        input_time, input_distance, lower_dist, upper_dist,
        distance_models[lower_dist], distance_models[upper_dist]
    )


def _predict_pace_from_models(input_time: float, models: dict):
    """Predict fast and slow paces from model dictionary."""
    fast_pace = _predict_with_model(input_time, models['fast'])
    slow_pace = _predict_with_model(input_time, models['slow'])
    return (fast_pace, slow_pace)


def _find_interpolation_bounds(available_distances: list, input_distance: float):
    """Find the lower and upper bounds for interpolation."""
    lower_dist = None
    upper_dist = None

    for dist in available_distances:
        if dist < input_distance:
            lower_dist = dist
        elif dist > input_distance:
            upper_dist = dist
            break

    return lower_dist, upper_dist


def _interpolate_between_distances(input_time: float, input_distance: float,
                                 lower_dist: float, upper_dist: float,
                                 models_lower: dict, models_upper: dict):
    """Interpolate training paces between two distances."""
    fast_pace_lower, slow_pace_lower = _predict_pace_from_models(input_time, models_lower)
    fast_pace_upper, slow_pace_upper = _predict_pace_from_models(input_time, models_upper)

    weight = (input_distance - lower_dist) / (upper_dist - lower_dist)
    fast_pace = fast_pace_lower + weight * (fast_pace_upper - fast_pace_lower)
    slow_pace = slow_pace_lower + weight * (slow_pace_upper - slow_pace_lower)

    return (fast_pace, slow_pace)


def training_paces(distance_meters: float, time_seconds: float) -> dict:
    """
    Calculate training paces based on a race performance using McMillan methodology.

    Args:
        distance_meters: Race distance in meters
        time_seconds: Race time in seconds

    Returns:
        dict: Dictionary containing training pace zones with official McMillan accuracy

    Raises:
        InvalidInputError: If distance or time is not positive or if inputs are unrealistic.
    """
    _assert_inputs(distance_meters, time_seconds)

    # Initialize training pace structure
    training_paces = _initialize_training_pace_structure()

    # Get all training pace zone keys from the unified model system
    training_pace_zones = _get_all_training_pace_zones()

    # Process each zone type
    for zone_key in training_pace_zones:
        zone_group, zone_type, zone_distance = zone_key

        pace_result = _interpolate_training_pace(zone_key, distance_meters, time_seconds)
        if pace_result is None:
            continue

        fast_pace_seconds, slow_pace_seconds = pace_result

        # Process zone based on type
        if zone_group == 'endurance':
            _process_endurance_zone(training_paces, zone_type, fast_pace_seconds, slow_pace_seconds)
        elif zone_group == 'stamina':
            _process_stamina_zone(training_paces, zone_type, zone_distance, fast_pace_seconds, slow_pace_seconds)
        elif zone_group in ['speed', 'sprint']:
            _process_interval_zone(training_paces, zone_group, zone_type, zone_distance, fast_pace_seconds, slow_pace_seconds)

    return training_paces


def _get_all_training_pace_zones():
    """
    Get all available training pace zone keys from the unified model system.

    Returns:
        list: List of zone keys (tuples) available in the training pace models
    """
    return _model_manager.get_training_pace_zones()


def _initialize_training_pace_structure() -> dict:
    """Initialize the basic training pace structure."""
    return {
        "endurance": {
            "description": "Endurance Zone: Running at an easy effort for extended periods of time",
            "types": {}
        },
        "stamina": {
            "description": "Stamina Zone: Medium-effort, medium duration running",
            "types": {}
        },
        "speed": {
            "description": "Speed Zone: Running at a high effort for a short duration",
            "types": {
                "endurance_monster": {
                    "description": "Speed training for endurance-focused athletes",
                    "distances": {}
                },
                "speedster": {
                    "description": "Speed training for speed-focused athletes",
                    "distances": {}
                }
            }
        },
        "sprint": {
            "description": "Sprint Zone: Running at a very high speed for a very short distance",
            "types": {
                "endurance_monster": {
                    "description": "Sprint training for endurance-focused athletes",
                    "distances": {}
                },
                "speedster": {
                    "description": "Sprint training for speed-focused athletes",
                    "distances": {}
                }
            }
        }
    }


def _process_endurance_zone(training_paces: dict, zone_type: str, fast_pace_seconds: float, slow_pace_seconds: float):
    """Process endurance zone training paces."""
    display_name = ZONE_NAME_MAPPINGS['endurance'].get(zone_type, zone_type)
    description = ZONE_DESCRIPTIONS.get(display_name, f"{display_name.replace('_', ' ').title()} pace")

    training_paces['endurance']['types'][display_name] = {
        'pace': format_pace(fast_pace_seconds, slow_pace_seconds),
        'description': description
    }


def _process_stamina_zone(training_paces: dict, zone_type: str, zone_distance: int, fast_pace_seconds: float, slow_pace_seconds: float):
    """Process stamina zone training paces."""
    if zone_type == 'cruise':
        # Handle cruise intervals with distances
        if 'cruise_intervals' not in training_paces['stamina']['types']:
            training_paces['stamina']['types']['cruise_intervals'] = {
                'description': "Moderate pace repetitions with very short recovery jogs",
                'distances': {}
            }

        fast_velocity = 1000 / fast_pace_seconds
        slow_velocity = 1000 / slow_pace_seconds
        distance_key = f"{zone_distance}m"

        training_paces['stamina']['types']['cruise_intervals']['distances'][distance_key] = format_pace_and_time(
            fast_velocity, slow_velocity, zone_distance
        )
    else:
        # Handle other stamina types with pace ranges
        display_name = ZONE_NAME_MAPPINGS['stamina'].get(zone_type, zone_type)
        description = ZONE_DESCRIPTIONS.get(display_name, f"{display_name.replace('_', ' ').title()} pace")

        training_paces['stamina']['types'][display_name] = {
            'pace': format_pace(fast_pace_seconds, slow_pace_seconds),
            'description': description
        }


def _process_interval_zone(training_paces: dict, zone_group: str, zone_type: str, zone_distance: int, fast_pace_seconds: float, slow_pace_seconds: float):
    """Process speed and sprint zone training paces."""
    fast_velocity = 1000 / fast_pace_seconds  # velocity in m/s
    slow_velocity = 1000 / slow_pace_seconds  # velocity in m/s
    distance_key = f"{zone_distance}m"

    # Ensure zone type exists
    if zone_type not in training_paces[zone_group]['types']:
        training_paces[zone_group]['types'][zone_type] = {
            'description': f"{zone_group.title()} training for {zone_type.replace('_', ' ')} athletes",
            'distances': {}
        }

    training_paces[zone_group]['types'][zone_type]['distances'][distance_key] = format_pace_and_time(
        fast_velocity, slow_velocity, zone_distance
    )


def format_pace_ms(seconds_per_km: float) -> str:
    """
    Format pace in seconds per kilometer to MM:SS format.

    Args:
        seconds_per_km: Pace in seconds per kilometer

    Returns:
        str: Formatted pace as "MM:SS" or "HH:MM:SS" if over 1 hour
    """
    hours = int(seconds_per_km // 3600)
    minutes = int((seconds_per_km % 3600) // 60)
    seconds = int(seconds_per_km % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


def format_pace_hms(seconds_per_km: float) -> str:
    """
    Format pace in seconds per kilometer to HH:MM:SS format.

    Args:
        seconds_per_km: Pace in seconds per kilometer

    Returns:
        str: Formatted pace as "HH:MM:SS"
    """
    hours = int(seconds_per_km // 3600)
    minutes = int((seconds_per_km % 3600) // 60)
    seconds = int(seconds_per_km % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_pace_and_time(fast_velocity: float, slow_velocity: float, distance: float) -> dict:
    """
    Format fast and slow velocities into a dictionary with formatted strings.

    Args:
        fast_velocity: Fast velocity in meters per second
        slow_velocity: Slow velocity in meters per second
        distance: Distance in meters

    Returns:
        dict: Dictionary with formatted fast and slow velocities
    """

    return {
        "split": format_split(distance / fast_velocity, distance / slow_velocity, distance),
        "pace": format_pace(1000 / fast_velocity, 1000 / slow_velocity)
    }


def format_pace(fast_pace: float, slow_pace: float) -> dict:
    """
    Format fast and slow paces.

    Args:
        fast_pace: Fast pace in seconds per kilometer
        slow_pace: Slow pace in seconds per kilometer

    Returns:
        dict: Dictionary with formatted fast and slow paces
    """

    return {
        "fast": format_pace_ms(fast_pace),
        "slow": format_pace_ms(slow_pace),
        "format": "MM:SS/km"
    }


def format_split(fast_time: float, slow_time: float, distance: int) -> dict:
    """
    Format fast and slow splits.

    Args:
        fast_time: Fast time in seconds for the given distance
        slow_time: Slow time in seconds for the given distance
        distance: Distance in meters

    Returns:
        dict: Dictionary with formatted fast and slow split times
    """

    return {
        "fast": format_pace_ms(fast_time),
        "slow": format_pace_ms(slow_time),
        "format": f"MM:SS/{distance}m"
    }


def heart_rate_zones(age: int, resting_heart_rate: int, max_heart_rate: int = None) -> dict:
    """
    Calculate heart rate zones based on age, resting heart rate, and optional max heart rate.

    Uses multiple formulas to estimate max heart rate if not provided, then calculates
    training zones using both HRMAX and HRRESERVE methods.

    Args:
        age: Runner's age in years
        resting_heart_rate: Resting heart rate in BPM
        max_heart_rate: Optional maximum heart rate in BPM (if None, will be estimated)

    Returns:
        dict: Dictionary containing estimated max HR and training zones

    Raises:
        InvalidInputError: If age, resting_heart_rate, or max_heart_rate are not positive
    """
    # Input validation
    if age <= 0:
        raise InvalidInputError("Age must be positive")
    if resting_heart_rate <= 0:
        raise InvalidInputError("Resting heart rate must be positive")
    if max_heart_rate is not None and max_heart_rate <= 0:
        raise InvalidInputError("Max heart rate must be positive")

    # Calculate estimated max heart rate using multiple formulas
    formula_results = [formula(age) for formula in MAX_HR_FORMULAS.values()]
    estimated_max_hr = round(sum(formula_results) / len(formula_results))

    # Use provided max heart rate if available, otherwise use estimated
    effective_max_hr = max_heart_rate if max_heart_rate is not None else estimated_max_hr

    # Use predefined training zone definitions
    zone_definitions = HR_ZONE_DEFINITIONS

    # Calculate heart rate zones
    result = {
        "estimated_max_heart_rate": estimated_max_hr,
        "effective_max_heart_rate": effective_max_hr,
        "resting_heart_rate": resting_heart_rate,
        "zones": {}
    }

    for zone_group, zones in zone_definitions.items():
        result["zones"][zone_group] = {
            "description": f"{zone_group.title()} Zone training",
            "types": {}
        }

        for zone_name, zone_data in zones.items():
            hrmax_min, hrmax_max = zone_data["hrmax"]
            hrreserve_min, hrreserve_max = zone_data["hrreserve"]

            # Calculate HRMAX method (percentage of max heart rate)
            hrmax_min_bpm = round((hrmax_min / 100) * effective_max_hr)
            hrmax_max_bpm = round((hrmax_max / 100) * effective_max_hr)

            # Calculate HRRESERVE method (percentage of heart rate reserve + resting)
            hr_reserve = effective_max_hr - resting_heart_rate
            hrreserve_min_bpm = round((hrreserve_min / 100) * hr_reserve + resting_heart_rate)
            hrreserve_max_bpm = round((hrreserve_max / 100) * hr_reserve + resting_heart_rate)

            result["zones"][zone_group]["types"][zone_name] = {
                "description": zone_data["description"],
                "hrmax": {
                    "min": hrmax_min_bpm,
                    "max": hrmax_max_bpm,
                    "range": f"{hrmax_min_bpm}-{hrmax_max_bpm} BPM"
                },
                "hrreserve": {
                    "min": hrreserve_min_bpm,
                    "max": hrreserve_max_bpm,
                    "range": f"{hrreserve_min_bpm}-{hrreserve_max_bpm} BPM"
                }
            }

    return result