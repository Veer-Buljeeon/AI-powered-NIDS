# AI-Powered NIDS — Project Brief for Claude Code

## What this is

A final year university capstone project: an AI-powered Network Intrusion
Detection System (NIDS) for small networks. This is an academic dissertation
project — the code must match what has already been documented and defended
in the accompanying dissertation (Chapters 3–5). I need to be able to explain
and defend every part of this system to my supervisor and examiners, so **you
are my pair programmer, not an autopilot.**

## How I want to work with you

- **Explain your plan before writing code.** For each new piece of
  functionality, briefly walk me through your approach and wait for my go-ahead
  before implementing it.
- **Do not add new features, libraries, or dependencies beyond what's
  specified below without asking me first.** If you think something extra
  would help, suggest it — don't just add it.
- **Follow the build order below, one phase at a time.** Don't skip ahead or
  build multiple phases in parallel. After each phase, stop and let me test
  it before moving on.
- **Flag any deviation** from the spec below — my code needs to match my
  dissertation, so if you think a documented approach is wrong or
  impractical, tell me rather than silently doing something different.
- I'm holding off on additional features until Phases 1–7 produce a working
  end-to-end prototype. Don't propose extra scope yet.

## Tech stack (already decided, don't change)

| Layer | Tech |
|---|---|
| ML / detection engine | Python 3.11, Pandas, Scikit-learn, XGBoost, TensorFlow/Keras, Flask, imbalanced-learn (SMOTE) |
| API layer | Java 21, Micronaut, Maven |
| Frontend | Vanilla HTML/CSS/JavaScript, Chart.js (no framework) |
| Containerisation | Docker, Docker Compose |
| Dataset | CICIDS2017 — `MachineLearningCSV.zip` from the CIC website |

## Current repo state

- Repo: `AI-powered-NIDS` (private GitHub repo, already initialised)
- Folders already scaffolded: `core/` (data, preprocessing, models, training,
  detection, capture), `api/` (Micronaut skeleton created via
  `mn create-app com.nids.api`), `frontend/` (css, js, components)
- The CICIDS2017 dataset (`MachineLearningCSV.zip`) needs to be downloaded by
  me manually and placed in `core/data/raw/` — check it's there before
  starting Phase 1; if it's missing, tell me rather than trying to fetch it.

## Build order

1. Data preprocessing pipeline
2. Model training (Random Forest, XGBoost, LSTM)
3. Python Flask detection engine
4. Java Micronaut API layer
5. Frontend dashboard
6. Attack simulation scripts (for use inside a GNS3 topology I set up manually)
7. Docker containerisation

---

## Phase 1 — Data Preprocessing (`core/preprocessing/`)

Build `preprocessing.py` exposing `load_and_preprocess()`:

1. Load all CICIDS2017 CSVs from `core/data/raw/`, concatenate, strip
   whitespace from column names (known formatting quirk).
2. Replace infinite values with NaN (`numpy.isinf`); drop rows with NaN; log
   how many rows were dropped.
3. Split features (X) from the label column (y).
4. Remove near-constant features: `VarianceThreshold(threshold=0.01)`.
5. Remove highly correlated features: drop one of each pair with Pearson
   correlation > 0.95.
6. Stratified `train_test_split(test_size=0.25, random_state=42)`.
7. Fit a preliminary Random Forest on the training set; rank features by
   `feature_importances_`; select the top N.
8. Fit `MinMaxScaler` on the training set only; transform both sets.
9. Encode labels with `LabelEncoder`.
10. Persist to `core/models/`: `scaler.pkl`, `selected_features.json`,
    `label_map.json` (all via joblib/json).
11. Apply SMOTE (`imbalanced-learn`, `k_neighbors=5`) to the **training set
    only**, after the split — never let synthetic samples reach the test set.
    Log class distribution before/after.

Return `X_train_balanced, y_train_balanced, X_test, y_test`.

## Phase 2 — Model Training (`core/training/`)

Three separate scripts, one per model, all trained on the SMOTE-balanced
training set:

- **Random Forest / XGBoost**: `GridSearchCV`, 5-fold `StratifiedKFold`,
  `scoring='f1_weighted'`. Retrain best config on full training set. Persist
  with `joblib.dump()`.
- **LSTM**: reshape input to `(samples, 1, num_features)`. Architecture:
  `LSTM(128, return_sequences=True) → Dropout(0.3) → LSTM(64) → Dropout(0.3)
  → Dense(num_classes, softmax)`. Adam optimizer, categorical crossentropy,
  `EarlyStopping(monitor='val_loss', patience=5)`, up to 50 epochs. Save via
  `model.save()` (TF SavedModel format).

Evaluate all three on the held-out test set: Accuracy, Precision, Recall,
**F1-score (primary metric)**, ROC-AUC. Report per-class F1 and a confusion
matrix — minority attack classes matter most here, not just overall accuracy.

File layout in `core/models/`: `random_forest_model.pkl`,
`xgboost_model.pkl`, `lstm_model/` (directory), plus the scaler/features/label
map from Phase 1.

## Phase 3 — Detection Engine (`core/detection/`)

Flask app, four modules:

- **ModelLoader** (Singleton): loads model/scaler/features/label map exactly
  once at startup based on a `MODEL_TYPE` env var (default `random_forest`).
  Store as module-level constants.
- **FeatureValidator**: checks incoming feature vector length matches the
  persisted feature list exactly; fail fast with a 400 if not.
- **Classifier** (Strategy): single `classify(feature_vector)` function.
  Branches internally on `MODEL_TYPE` but presents an identical interface
  regardless of which model is loaded — this is what makes the model
  swappable later without touching any other code.
- **ClassifyEndpoint**: `POST /classify`. Validate → classify → return JSON:
  `{class_label, class_index, confidence}`.

## Phase 4 — API Layer (`api/`)

Micronaut controllers/services:

- `PredictController` (`POST /predict`) — orchestrates only, no business
  logic of its own: calls `DetectionClient`, then if malicious writes to
  `AlertStore` and notifies `AlertBroadcaster`.
- `DetectionClient` (Adapter, `@Singleton`) — declarative `@Client` HTTP
  wrapper around the Flask `/classify` endpoint. Read the endpoint URL from
  an env var, don't hardcode it.
- `AlertStore` (Repository, `@Singleton`) — wrap a `CopyOnWriteArrayList` for
  thread-safe concurrent access.
- `AlertBroadcaster` (Observer) + `AlertSocket` (`@ServerWebSocket
  /alerts/live`) — maintain a session registry, push new alerts to all
  connected sessions via non-blocking `sendAsync()`.
- `AlertsController` (`GET /alerts`, paginated) and `StatsController` (`GET
  /stats`, computed on-demand from `AlertStore`, not a separately maintained
  counter).

## Phase 5 — Frontend (`frontend/`)

Vanilla JS modules, four-zone layout (header status → stats summary → charts
→ live alert feed):

- `WebSocketClient` (Observer/Subject) — connects to `/alerts/live`, exposes
  `subscribe(callback)`, auto-reconnects after 5s on disconnect.
- `AlertFeedRenderer`, `ChartManager` (Facade over 3 Chart.js instances),
  `AlertHistoryTable` — all subscribe to `WebSocketClient`.
- `StatsPoller` — polls `/stats` every 5s (deliberately separate from the
  WebSocket push path — aggregate stats don't need per-flow immediacy).
- Alert severity colours: red (`#843C0C`/`#DC2626`) for DoS/DDoS/Brute Force,
  amber (`#7B5E00`/`#D97706`) for Port Scan/recon, green
  (`#217346`/`#16A34A`) for benign. Prefix each alert entry with a plain `●`
  character in the matching colour (not an emoji — renders unreliably).

## Phase 6 — Attack Simulation Scripts (`simulation/`)

I'll build the GNS3 topology myself. You just need wrapper scripts for the
Kali Linux attacker node — one shell script per scenario that records a
start timestamp, runs the tool, records an end timestamp (needed later to
correlate ground-truth attack windows against NIDS alerts):

- Port scans: Nmap (`-sS`, `-sU`)
- DoS: Slowloris, Hulk
- DDoS: `hping3 --flood --syn`
- Brute force: Hydra (`-t ssh`, `-t ftp`)
- Botnet beaconing: **needs a custom Python script** (no Kali tool for this)
  — periodic HTTP GET to a C2 address every ~30s with randomised jitter, run
  for the scenario duration then exit cleanly.

## Phase 7 — Docker

- `core/Dockerfile`: `python:3.11-slim`, copy `requirements.txt` and install
  *before* copying source code (layer caching), `EXPOSE 5000`.
- `api/Dockerfile`: multi-stage — `maven:3.9-eclipse-temurin-21` to build,
  copy only the JAR into `eclipse-temurin:21-jre-alpine`, `EXPOSE 8080`.
- `frontend/Dockerfile`: `nginx:alpine`, copy static files + nginx config,
  `EXPOSE 80`.
- Root `docker-compose.yml`: all three on a shared `nids-network` bridge,
  healthchecks on `ids-core` and `ids-api`, `depends_on` with
  `condition: service_healthy` to enforce startup order, resource limits
  (ids-core: 1.5 CPU/1GB, ids-api: 1.0 CPU/512MB, ids-frontend: 0.5 CPU/128MB).
  `DETECTION_ENGINE_URL` passed into `ids-api` as an env var, not hardcoded.

---

**Start with Phase 1.** Confirm the dataset is present, then walk me through
your preprocessing plan before writing any code.
