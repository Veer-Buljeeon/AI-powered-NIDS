"""Classifier (strategy).

A single classify() that behaves identically regardless of which model
MODEL_TYPE selected. It scales the raw feature vector with the persisted
MinMaxScaler (so inference matches training), runs the loaded model, and returns
{class_label, class_index, confidence}. The MODEL_TYPE branch is hidden here, so
swapping models never touches the endpoint or the API.
"""

import numpy as np

from model_loader import LABEL_MAP, MODEL, MODEL_TYPE, SCALER


def _predict_proba(scaled_row):
    """Class-probability vector for one scaled sample, shape (num_classes,)."""
    if MODEL_TYPE == "lstm":
        reshaped = scaled_row.reshape((1, 1, scaled_row.shape[1])).astype("float32")
        return MODEL.predict(reshaped, verbose=0)[0]
    return MODEL.predict_proba(scaled_row)[0]


def classify(feature_vector):
    """Classify one raw feature vector; returns the detection-engine contract dict."""
    row = np.asarray(feature_vector, dtype="float64").reshape(1, -1)
    scaled = SCALER.transform(row)
    proba = np.asarray(_predict_proba(scaled), dtype="float64")
    class_index = int(np.argmax(proba))
    confidence = float(proba[class_index])
    class_label = LABEL_MAP.get(class_index, str(class_index))
    return {
        "class_label": class_label,
        "class_index": class_index,
        "confidence": round(confidence, 6),
    }
