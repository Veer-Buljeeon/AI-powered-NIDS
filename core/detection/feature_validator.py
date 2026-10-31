"""FeatureValidator.

Checks that an incoming feature vector matches the persisted feature list
exactly (length and numeric type). Raises FeatureValidationError on any
mismatch so the endpoint can fail fast with a 400.
"""

from model_loader import NUM_FEATURES


class FeatureValidationError(ValueError):
    """Raised when an incoming feature vector is the wrong shape or type."""


def validate(features):
    """Return the vector as a list of floats, or raise FeatureValidationError."""
    if not isinstance(features, (list, tuple)):
        raise FeatureValidationError("'features' must be a JSON array of numbers.")
    if len(features) != NUM_FEATURES:
        raise FeatureValidationError(
            f"Expected {NUM_FEATURES} features, got {len(features)}.")
    try:
        return [float(x) for x in features]
    except (TypeError, ValueError):
        raise FeatureValidationError("All features must be numeric.")
