"""
CICIDS2017 data-preprocessing pipeline (Phase 1).

Exposes ``load_and_preprocess()``, which turns the raw CICIDS2017 CSVs into
model-ready train/test arrays following the project brief's 11-step pipeline:

  1.  Load + concatenate all CSVs; strip whitespace from column names.
  2.  Replace infinite values with NaN and drop rows containing NaN.
  3.  Separate features (X) from the ``Label`` column (y).
  4.  Drop near-constant features (VarianceThreshold, threshold=0.01).
  5.  Drop one of each feature pair with Pearson correlation > 0.95.
  6.  Stratified train/test split (test_size=0.25, random_state=42).
  7.  Rank features with a preliminary Random Forest; keep the top N (default 30).
  8.  Fit MinMaxScaler on the training set only; transform both sets.
  9.  Encode labels with LabelEncoder.
  10. Persist scaler.pkl, selected_features.json and label_map.json to core/models/.
  11. Apply SMOTE (k_neighbors=5) to the TRAINING set only.

The artifacts written to core/models/ are consumed later by the detection
engine, so the feature order and the label mapping are persisted exactly as
used here.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, MinMaxScaler

logger = logging.getLogger(__name__)

# Resolve project paths relative to this file so the pipeline runs from anywhere.
_HERE = Path(__file__).resolve().parent          # core/preprocessing
_CORE_DIR = _HERE.parent                          # core
DEFAULT_RAW_DIR = _CORE_DIR / "data" / "raw"
DEFAULT_MODELS_DIR = _CORE_DIR / "models"

LABEL_COLUMN = "Label"


def load_and_preprocess(
    raw_dir: str | Path = DEFAULT_RAW_DIR,
    models_dir: str | Path = DEFAULT_MODELS_DIR,
    top_n: int = 30,
    test_size: float = 0.25,
    random_state: int = 42,
    variance_threshold: float = 0.01,
    correlation_threshold: float = 0.95,
    smote_k_neighbors: int = 5,
):
    """Run the full preprocessing pipeline and return model-ready arrays.

    Parameters mirror the project brief; defaults are the documented values.

    Returns
    -------
    X_train_balanced : np.ndarray   scaled, top-N features, SMOTE-balanced
    y_train_balanced : np.ndarray   integer-encoded labels (balanced)
    X_test           : np.ndarray   scaled, top-N features (NO SMOTE applied)
    y_test           : np.ndarray   integer-encoded labels
    """
    raw_dir = Path(raw_dir)
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Step 1 - Load and concatenate all CSVs; strip column-name whitespace
    # ------------------------------------------------------------------ #
    csv_paths = sorted(raw_dir.glob("*.csv"))
    if not csv_paths:
        raise FileNotFoundError(
            f"No CSV files found in {raw_dir}. "
            "Place the CICIDS2017 MachineLearningCVE CSVs there first."
        )

    frames = []
    for path in csv_paths:
        # latin-1 never fails to decode; the CICIDS2017 web-attack labels
        # contain a non-UTF-8 byte (0x96) that would otherwise raise
        # UnicodeDecodeError under the default utf-8 codec.
        part = pd.read_csv(path, encoding="latin-1", low_memory=False)
        part.columns = part.columns.str.strip()
        logger.info("Loaded %-55s rows=%8d cols=%d", path.name, len(part), part.shape[1])
        frames.append(part)

    df = pd.concat(frames, ignore_index=True)
    del frames
    logger.info("Combined dataset: %d rows x %d columns", len(df), df.shape[1])

    if LABEL_COLUMN not in df.columns:
        raise KeyError(
            f"Expected label column '{LABEL_COLUMN}' not found after stripping "
            f"whitespace. First columns seen: {list(df.columns)[:5]}"
        )

    # ------------------------------------------------------------------ #
    # Step 2 - Infinite values -> NaN, then drop rows containing NaN
    # ------------------------------------------------------------------ #
    feature_cols = [c for c in df.columns if c != LABEL_COLUMN]

    # Some CICIDS2017 rows store the literal strings "Infinity"/"NaN" in the
    # 'Flow Bytes/s' and 'Flow Packets/s' columns, which leaves those columns
    # typed as text. Coercing to numeric turns those (and any stray non-numeric
    # value) into NaN so they are dropped together with true infinities -
    # faithful to the brief's "infinite values -> NaN -> drop" intent.
    df[feature_cols] = df[feature_cols].apply(pd.to_numeric, errors="coerce")
    df[feature_cols] = df[feature_cols].replace([np.inf, -np.inf], np.nan)
    # Downcast to float32 to roughly halve the in-memory footprint (~2.8M rows).
    df[feature_cols] = df[feature_cols].astype(np.float32)

    rows_before = len(df)
    df = df.dropna().reset_index(drop=True)
    rows_dropped = rows_before - len(df)
    logger.info(
        "Dropped %d rows with NaN/inf (%.4f%% of %d); %d rows remain",
        rows_dropped, 100 * rows_dropped / max(rows_before, 1), rows_before, len(df),
    )

    # ------------------------------------------------------------------ #
    # Step 3 - Separate features (X) and label (y)
    # ------------------------------------------------------------------ #
    y = df[LABEL_COLUMN].astype(str).str.strip()
    X = df[feature_cols]
    logger.info("Class distribution (full dataset):\n%s", y.value_counts().to_string())

    # ------------------------------------------------------------------ #
    # Step 4 - Drop near-constant features (VarianceThreshold)
    # ------------------------------------------------------------------ #
    selector = VarianceThreshold(threshold=variance_threshold)
    selector.fit(X)
    kept_mask = selector.get_support()
    dropped_variance = list(X.columns[~kept_mask])
    X = X.loc[:, kept_mask]
    logger.info(
        "VarianceThreshold(%.3f) removed %d feature(s): %s",
        variance_threshold, len(dropped_variance), dropped_variance,
    )

    # ------------------------------------------------------------------ #
    # Step 5 - Drop highly correlated features (Pearson > threshold)
    # ------------------------------------------------------------------ #
    corr = X.corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape, dtype=bool), k=1))
    to_drop = [col for col in upper.columns if (upper[col] > correlation_threshold).any()]
    X = X.drop(columns=to_drop)
    logger.info(
        "Correlation filter (>%.2f) removed %d feature(s): %s",
        correlation_threshold, len(to_drop), to_drop,
    )
    logger.info("Features remaining after filtering: %d", X.shape[1])

    # ------------------------------------------------------------------ #
    # Step 6 - Stratified train/test split
    # ------------------------------------------------------------------ #
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y,
    )
    logger.info("Split: train=%d rows, test=%d rows", len(X_train), len(X_test))

    # ------------------------------------------------------------------ #
    # Step 7 - Preliminary Random Forest -> top-N feature selection
    # ------------------------------------------------------------------ #
    n_select = min(top_n, X_train.shape[1])
    logger.info("Fitting preliminary RandomForest for feature ranking "
                "(this is the slow step)...")
    prelim_rf = RandomForestClassifier(
        n_estimators=100, random_state=random_state, n_jobs=-1,
    )
    prelim_rf.fit(X_train, y_train)
    importances = pd.Series(prelim_rf.feature_importances_, index=X_train.columns)
    importances = importances.sort_values(ascending=False)
    selected_features = list(importances.head(n_select).index)
    logger.info("Selected top %d features by importance:\n%s",
                n_select, importances.head(n_select).to_string())

    X_train = X_train[selected_features]
    X_test = X_test[selected_features]

    # Persist the selected features. Order matters: the detection engine feeds
    # feature vectors to the model in exactly this order.
    features_path = models_dir / "selected_features.json"
    with open(features_path, "w", encoding="utf-8") as fh:
        json.dump(selected_features, fh, indent=2)
    logger.info("Wrote %s", features_path)

    # ------------------------------------------------------------------ #
    # Step 8 - MinMaxScaler fit on TRAIN only, transform both
    # ------------------------------------------------------------------ #
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    scaler_path = models_dir / "scaler.pkl"
    joblib.dump(scaler, scaler_path)
    logger.info("Wrote %s", scaler_path)

    # ------------------------------------------------------------------ #
    # Step 9 - Encode labels
    # ------------------------------------------------------------------ #
    # Fit on the full label set so every class gets a stable index and the
    # persisted map is complete, then apply the encoding to each split.
    label_encoder = LabelEncoder()
    label_encoder.fit(y)
    y_train_enc = label_encoder.transform(y_train)
    y_test_enc = label_encoder.transform(y_test)

    # ------------------------------------------------------------------ #
    # Step 10 - Persist the label map (index -> class name)
    # ------------------------------------------------------------------ #
    label_map = {int(i): cls for i, cls in enumerate(label_encoder.classes_)}
    label_map_path = models_dir / "label_map.json"
    with open(label_map_path, "w", encoding="utf-8") as fh:
        json.dump(label_map, fh, indent=2)
    logger.info("Wrote %s  (%d classes)", label_map_path, len(label_map))

    # ------------------------------------------------------------------ #
    # Step 11 - SMOTE on the TRAINING set only
    # ------------------------------------------------------------------ #
    dist_before = dict(sorted(Counter(y_train).items()))
    logger.info("Class distribution BEFORE SMOTE (train):\n%s",
                "\n".join(f"    {k:<32} {v}" for k, v in dist_before.items()))

    smote = SMOTE(random_state=random_state, k_neighbors=smote_k_neighbors)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train_scaled, y_train_enc)

    dist_after = dict(sorted(Counter(label_encoder.inverse_transform(y_train_balanced)).items()))
    logger.info("Class distribution AFTER SMOTE (train):\n%s",
                "\n".join(f"    {k:<32} {v}" for k, v in dist_after.items()))
    logger.info("Training rows: %d -> %d after SMOTE", len(y_train_enc), len(y_train_balanced))

    return X_train_balanced, y_train_balanced, X_test_scaled, y_test_enc


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
        datefmt="%H:%M:%S",
    )
    X_train_balanced, y_train_balanced, X_test, y_test = load_and_preprocess()
    logger.info("=" * 62)
    logger.info("Preprocessing complete. Final shapes:")
    logger.info("  X_train_balanced: %s", X_train_balanced.shape)
    logger.info("  y_train_balanced: %s", y_train_balanced.shape)
    logger.info("  X_test:           %s", X_test.shape)
    logger.info("  y_test:           %s", y_test.shape)
