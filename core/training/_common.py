"""Shared helpers for the Phase 2 training scripts.

Provides cached data loading (so the Phase-1 pipeline runs once, not once per
model) and a single evaluation routine used by all three models, so the metrics
and figure code is not duplicated.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent      # core/training
CORE_DIR = _HERE.parent                       # core
MODELS_DIR = CORE_DIR / "models"
CACHE_DIR = MODELS_DIR / "preprocessed"

# Make the Phase-1 `preprocessing` package importable when running these scripts.
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))


def load_data(use_cache: bool = True):
    """Return (X_train_balanced, y_train_balanced, X_test, y_test).

    Runs the Phase-1 pipeline once and caches the arrays under
    core/models/preprocessed/ (deterministic, random_state=42); later calls
    reload from that cache instead of re-preprocessing.
    """
    files = {k: CACHE_DIR / f"{k}.npy" for k in ("X_train", "y_train", "X_test", "y_test")}
    if use_cache and all(f.exists() for f in files.values()):
        print(f"[data] loading cached arrays from {CACHE_DIR}")
        return (np.load(files["X_train"]), np.load(files["y_train"]),
                np.load(files["X_test"]), np.load(files["y_test"]))

    print("[data] cache miss - running Phase-1 preprocessing (a few minutes)...")
    from preprocessing.preprocessing import load_and_preprocess
    X_train, y_train, X_test, y_test = load_and_preprocess()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    np.save(files["X_train"], X_train)
    np.save(files["y_train"], y_train)
    np.save(files["X_test"], X_test)
    np.save(files["y_test"], y_test)
    print(f"[data] cached arrays to {CACHE_DIR}")
    return X_train, y_train, X_test, y_test


def load_label_names():
    """Class names ordered by encoded index.

    The three CICIDS2017 'Web Attack' labels carry a non-ASCII artefact from the
    raw CSVs; it is replaced with a hyphen for readable figures/reports.
    """
    with open(MODELS_DIR / "label_map.json", encoding="utf-8") as fh:
        label_map = json.load(fh)
    names = []
    for i in range(len(label_map)):
        n = label_map[str(i)]
        for junk in ("ï¿½", "�", "\u0096"):
            n = n.replace(junk, "-")
        names.append(" ".join(n.split()))
    return names


def stratified_subsample(X, y, n, random_state: int = 42):
    """A stratified subsample of about ``n`` rows (or all rows if n >= len(y))."""
    if n >= len(y):
        return X, y
    from sklearn.model_selection import train_test_split
    X_s, _, y_s, _ = train_test_split(
        X, y, train_size=n, stratify=y, random_state=random_state)
    return X_s, y_s


def _save_confusion(matrix, label_names, title, path, values_format):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import ConfusionMatrixDisplay

    disp = ConfusionMatrixDisplay(confusion_matrix=matrix, display_labels=label_names)
    fig, ax = plt.subplots(figsize=(12, 10))
    disp.plot(ax=ax, cmap="Blues", xticks_rotation=90, colorbar=True,
              values_format=values_format)
    ax.set_title(title)
    plt.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def evaluate(name: str, y_test, y_pred, y_proba, label_names):
    """Evaluate one model on the held-out test set.

    Prints and persists: accuracy, weighted precision/recall/F1 (F1 is the
    primary metric), weighted one-vs-rest ROC-AUC, the per-class report, and two
    confusion-matrix figures (raw counts and row-normalised). Returns the
    headline metrics as a dict.
    """
    from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                                 f1_score, roc_auc_score, classification_report,
                                 confusion_matrix)

    n_classes = len(label_names)
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    rec = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1w = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    try:
        roc = float(roc_auc_score(y_test, y_proba, multi_class="ovr",
                                  average="weighted", labels=list(range(n_classes))))
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[eval] ROC-AUC could not be computed: {exc}")
        roc = None

    report = classification_report(y_test, y_pred, target_names=label_names,
                                   digits=4, zero_division=0)
    print(f"\n===== {name} - test-set evaluation =====")
    print(f"Accuracy               : {acc:.4f}")
    print(f"Precision (weighted)   : {prec:.4f}")
    print(f"Recall (weighted)      : {rec:.4f}")
    print(f"F1 (weighted) [PRIMARY]: {f1w:.4f}")
    print(f"ROC-AUC (ovr, weighted): {'n/a' if roc is None else round(roc, 4)}")
    print("\nPer-class report:\n" + report)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    cm = confusion_matrix(y_test, y_pred, labels=list(range(n_classes)))
    _save_confusion(cm, label_names, f"{name} - confusion matrix (counts)",
                    MODELS_DIR / f"{name}_confusion_matrix.png", "d")
    with np.errstate(all="ignore"):
        cmn = np.nan_to_num(cm.astype("float") / cm.sum(axis=1, keepdims=True))
    _save_confusion(cmn, label_names, f"{name} - confusion matrix (row-normalised)",
                    MODELS_DIR / f"{name}_confusion_matrix_normalized.png", ".2f")

    metrics = {"model": name, "accuracy": acc, "precision_weighted": prec,
               "recall_weighted": rec, "f1_weighted": f1w,
               "roc_auc_ovr_weighted": roc}
    with open(MODELS_DIR / f"{name}_metrics.json", "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)
    with open(MODELS_DIR / f"{name}_classification_report.txt", "w", encoding="utf-8") as fh:
        fh.write(report)
    print(f"[eval] wrote metrics, report, and confusion-matrix figures to {MODELS_DIR}")
    return metrics
