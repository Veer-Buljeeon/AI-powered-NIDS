"""Phase 2 - XGBoost training.

Same flow as the Random Forest script: hyperparameter search (5-fold
StratifiedKFold, scoring='f1_weighted') on a stratified subsample of the
SMOTE-balanced training set, then retrain the best configuration on the FULL
training set and evaluate on the held-out test set. Persisted with joblib.
"""

from __future__ import annotations

import time

import joblib
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from xgboost import XGBClassifier

from _common import (MODELS_DIR, evaluate, load_data, load_label_names,
                     stratified_subsample)

RANDOM_STATE = 42
SEARCH_SUBSAMPLE = 300_000
PARAM_GRID = {
    "n_estimators": [200, 400],
    "max_depth": [6, 10],
    "learning_rate": [0.1, 0.3],
}


def _model(**extra):
    return XGBClassifier(
        objective="multi:softprob",
        tree_method="hist",
        eval_metric="mlogloss",
        random_state=RANDOM_STATE,
        **extra,
    )


def main():
    X_train, y_train, X_test, y_test = load_data()
    label_names = load_label_names()
    print(f"[xgb] train={X_train.shape}  test={X_test.shape}  classes={len(label_names)}")

    X_search, y_search = stratified_subsample(X_train, y_train, SEARCH_SUBSAMPLE, RANDOM_STATE)
    print(f"[xgb] hyperparameter search on stratified subsample: {X_search.shape}")

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    search = GridSearchCV(
        _model(n_jobs=1), param_grid=PARAM_GRID, scoring="f1_weighted",
        cv=cv, n_jobs=-1, refit=False, verbose=2,
    )
    t0 = time.time()
    search.fit(X_search, y_search)
    print(f"[xgb] best params: {search.best_params_}")
    print(f"[xgb] best CV f1_weighted: {search.best_score_:.4f}")
    print(f"[xgb] search took {(time.time() - t0) / 60:.1f} min")

    print("[xgb] retraining best config on the FULL training set...")
    t0 = time.time()
    best = _model(n_jobs=-1, **search.best_params_)
    best.fit(X_train, y_train)
    print(f"[xgb] final fit took {(time.time() - t0) / 60:.1f} min")

    y_pred = best.predict(X_test)
    y_proba = best.predict_proba(X_test)
    evaluate("xgboost", y_test, y_pred, y_proba, label_names)

    out = MODELS_DIR / "xgboost_model.pkl"
    joblib.dump(best, out)
    print(f"[xgb] saved model to {out}")


if __name__ == "__main__":
    main()
