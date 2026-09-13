# AI-Powered NIDS

A network Intrusion Detection System for small networks, powered by AI and Machine Learning.
Created by Buljeeon Vishwadeep for UTM Capstone Project BCNS 24A FT1.

## Architecture

The system is split into three independently runnable services:

| Directory | Stack | Responsibility |
|-----------|-------|----------------|
| `core/` | Python 3.11 (Pandas, scikit-learn, imbalanced-learn) | Data preprocessing, model training, and the (planned) Flask detection engine |
| `api/` | Java 21 / Micronaut | REST + WebSocket API that orchestrates detection and serves alerts |
| `frontend/` | Vanilla HTML/CSS/JS | Dashboard for stats and the live alert feed |

Request flow: `frontend → API (/predict) → detection engine (/classify) → alert stored & broadcast → frontend (WebSocket)`.

## Prerequisites

- **Python 3.11**
- **Java 21** (e.g. Eclipse Temurin) — the Maven wrapper (`mvnw`) downloads Maven itself, so a separate Maven install is not required
- **CICIDS2017 dataset** — `MachineLearningCSV.zip` from the [CIC website](https://www.unb.ca/cic/datasets/ids-2017.html), downloaded manually

## Setup

### 1. Dataset

Download `MachineLearningCSV.zip` and extract the 8 CSVs into `core/data/raw/` so the folder looks like:

```
core/data/raw/
├── Monday-WorkingHours.pcap_ISCX.csv
├── Tuesday-WorkingHours.pcap_ISCX.csv
├── Wednesday-workingHours.pcap_ISCX.csv
├── Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv
├── Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv
├── Friday-WorkingHours-Morning.pcap_ISCX.csv
├── Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv
└── Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
```

The dataset is git-ignored (it is large and must be obtained separately).

### 2. Python environment (`core/`)

```bash
cd core
python -m venv .venv

# Activate the virtual environment:
#   Windows (PowerShell):  .venv\Scripts\Activate.ps1
#   Windows (cmd):         .venv\Scripts\activate.bat
#   Linux / macOS:         source .venv/bin/activate

pip install -r requirements.txt
```

Run the preprocessing pipeline (loads the CSVs, cleans, selects the top 30 features,
balances the training set, and writes the artifacts to `core/models/`):

```bash
python preprocessing/preprocessing.py
```

This produces `core/models/scaler.pkl`, `selected_features.json`, and `label_map.json`.
Expect a few minutes of runtime (the Random Forest feature ranking is the slow step).

### 3. Build the API (`api/`)

```bash
cd api

# Windows (PowerShell / cmd):
mvnw.cmd clean package -DskipTests

# Linux / macOS / Git Bash:
./mvnw clean package -DskipTests
```

This produces the runnable jar `api/target/api-0.1.jar`.

## Running the system

Start the services in separate terminals.

### 1. Start the API — terminal 1

```bash
java -jar api/target/api-0.1.jar
```

Serves on **http://localhost:8080**. The detection-engine URL is read from the
`DETECTION_ENGINE_URL` environment variable (default `http://localhost:5000`), e.g.:

```bash
# Windows (PowerShell):  $env:DETECTION_ENGINE_URL = "http://localhost:5000"
# Linux / macOS:         export DETECTION_ENGINE_URL=http://localhost:5000
```

### 2. Serve the frontend — terminal 2

```bash
python -m http.server 8000 --directory frontend
```

### 3. Open the dashboard

Navigate to **http://localhost:8000**. You should see the API and live-feed status
pills turn green. The dashboard polls `/stats`, renders the alert feed, connects to
the WebSocket, and the "Send test flow" button exercises `POST /predict`.

> **Note:** until the model training (Phase 2) and the Flask detection engine (Phase 3)
> are in place, `POST /predict` returns `503 Detection engine unavailable`. This is
> expected — it confirms the API is reachable and correctly attempting to contact the
> detection engine.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/predict` | Classify a flow's feature vector; raise & broadcast an alert if malicious |
| `GET`  | `/alerts?page=&size=` | Paginated alert history (newest first) |
| `GET`  | `/stats` | Aggregate counts by class and severity, computed on demand |
| `WS`   | `/alerts/live` | WebSocket stream of new alerts as they are raised |

## Build status

| Phase | Component | Status |
|-------|-----------|--------|
| 1 | Data preprocessing (`core/preprocessing`) | ✅ Complete |
| 2 | Model training (Random Forest, XGBoost, LSTM) | ⬜ Planned |
| 3 | Flask detection engine (`core/detection`) | ⬜ Planned |
| 4 | Micronaut API layer (`api/`) | ✅ Complete |
| 5 | Frontend dashboard (`frontend/`) | 🟡 Interim test dashboard (full modular version planned) |
| 6 | Attack simulation scripts (`simulation/`) | ⬜ Planned |
| 7 | Docker containerisation | ⬜ Planned |
