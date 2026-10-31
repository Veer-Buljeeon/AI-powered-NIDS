"""Flask detection engine (Phase 3).

Exposes POST /classify (validate -> classify -> JSON) and a lightweight
GET /health for container healthchecks. The model/scaler/features/label map are
loaded once at startup by model_loader (selected via the MODEL_TYPE env var).
"""

import logging

from flask import Flask, jsonify, request

from classifier import classify
from feature_validator import FeatureValidationError, validate
from model_loader import MODEL_TYPE, NUM_FEATURES

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("detection")

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "model_type": MODEL_TYPE, "num_features": NUM_FEATURES})


@app.post("/classify")
def classify_endpoint():
    payload = request.get_json(silent=True)
    if not payload or "features" not in payload:
        return jsonify({"error": "Request body must be JSON with a 'features' array."}), 400
    try:
        features = validate(payload["features"])
    except FeatureValidationError as exc:
        return jsonify({"error": str(exc)}), 400
    result = classify(features)
    log.info("classified as %s (confidence %.4f)", result["class_label"], result["confidence"])
    return jsonify(result)


if __name__ == "__main__":
    log.info("Detection engine starting: MODEL_TYPE=%s, expecting %d features",
             MODEL_TYPE, NUM_FEATURES)
    app.run(host="0.0.0.0", port=5000)
