"""ModelLoader (singleton).

Loads the trained model, the MinMaxScaler, the selected-feature list and the
label map exactly once, when this module is first imported. The chosen model is
selected by the MODEL_TYPE environment variable (default 'random_forest'); the
loaded objects are exposed as module-level constants so the rest of the engine
shares a single in-memory copy.
"""

import json
import os
from pathlib import Path

import joblib

_HERE = Path(__file__).resolve().parent      # core/detection
CORE_DIR = _HERE.parent                       # core
MODELS_DIR = CORE_DIR / "models"

MODEL_TYPE = os.environ.get("MODEL_TYPE", "random_forest").lower()

_MODEL_PATHS = {
    "random_forest": MODELS_DIR / "random_forest_model.pkl",
    "xgboost": MODELS_DIR / "xgboost_model.pkl",
    "lstm": MODELS_DIR / "lstm_model",
}


def _load_model(model_type):
    if model_type not in _MODEL_PATHS:
        raise ValueError(
            f"Unknown MODEL_TYPE '{model_type}'. Expected one of {list(_MODEL_PATHS)}.")
    path = _MODEL_PATHS[model_type]
    if not path.exists():
        raise FileNotFoundError(
            f"Model artifact for '{model_type}' not found at {path}. "
            "Train it first via core/training/.")
    if model_type == "lstm":
        from tensorflow.keras.models import load_model  # lazy: only LSTM pulls in TF
        return load_model(str(path))
    return joblib.load(path)


# --- loaded once at import (the singleton) ---
MODEL = _load_model(MODEL_TYPE)
SCALER = joblib.load(MODELS_DIR / "scaler.pkl")

with open(MODELS_DIR / "selected_features.json", encoding="utf-8") as _fh:
    SELECTED_FEATURES = json.load(_fh)

with open(MODELS_DIR / "label_map.json", encoding="utf-8") as _fh:
    LABEL_MAP = {int(k): v for k, v in json.load(_fh).items()}

NUM_FEATURES = len(SELECTED_FEATURES)
