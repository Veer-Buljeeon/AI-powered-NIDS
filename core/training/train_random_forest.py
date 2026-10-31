"""Phase 2 - Random Forest training.

Hyperparameter search (5-fold StratifiedKFold, scoring='f1_weighted') is run on
a stratified subsample of the SMOTE-balanced training set for tractability; the
best configuration is then retrained on the FULL training set and evaluated on
the held-out test set. The fitted model is persisted with joblib.

max_depth is deliberately bounded (not None) so the final fit on ~3M rows stays
within a laptop's memory.
"""

from __future__ import annotations

import time

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold

from _common import (MODELS_DIR, evaluate, load_data, load_label_names,
                     stratified_subsample)

RANDOM_STATE = 42
SEARCH_SUBSAMPLE = 300_000
PARAM_GRID = {
    "n_estimators": [100, 200],
    "max_depth": [20, 40],
    "min_samples_split": [2, 10],
}


def main():
    X_train, y_train, X_test, y_test = load_data()
    label_names = load_label_names()
    print(f"[rf] train={X_train.shape}  test={X_test.shape}  classes={len(label_names)}")

    X_search, y_search = stratified_subsample(X_train, y_train, SEARCH_SUBSAMPLE, RANDOM_STATE)
    print(f"[rf] hyperparameter search on stratified subsample: {X_search.shape}")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    search = GridSearchCV(
        RandomForestClassifier(random_state=RANDOM_STATE, n_jobs=1),
        param_grid=PARAM_GRID, scoring="f1_weighted", cv=cv,
        n_jobs=-1, refit=False, verbose=2,
    )
    t0 = time.time()
    search.fit(X_search, y_search)
    print(f"[rf] best params: {search.best_params_}")
    print(f"[rf] best CV f1_weighted: {search.best_score_:.4f}")
    print(f"[rf] search took {(time.time() - t0) / 60:.1f} min")

    print("[rf] retraining best config on the FULL training set...")
    t0 = time.time()
    best = RandomForestClassifier(random_state=RANDOM_STATE, n_jobs=-1, **search.best_params_)
    best.fit(X_train, y_train)
    print(f"[rf] final fit took {(time.time() - t0) / 60:.1f} min")

    y_pred = best.predict(X_test)
    y_proba = best.predict_proba(X_test)
    evaluate("random_forest", y_test, y_pred, y_proba, label_names)

    out = MODELS_DIR / "random_forest_model.pkl"
    joblib.dump(best, out)
    print(f"[rf] saved model to {out}")


if __name__ == "__main__":
    main()
