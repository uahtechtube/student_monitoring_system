# KIU Student Segmentation and Academic Monitoring System

Flask skeleton implementing the architecture in Chapter Three: three-tier
(Presentation / Application Logic / Data), two independent K-Means models
(Returning students vs. New students), bcrypt auth, and CSV-based reporting.

## Setup and Running Instructions

Follow these steps to set up, run, and test the project locally.

### 1. Prerequisites
Ensure you have **Python 3.11 or later** installed.

### 2. Repository Cloning and Virtual Environment Setup
Clone the project repository and enter the directory:
```bash
git clone https://github.com/uahtechtube/student_monitoring_system.git
cd student_monitoring_system
```

Create a virtual environment and activate it:
```bash
# Windows (PowerShell/Command Prompt)
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux (Terminal)
python3 -m venv .venv
source .venv/bin/activate
```

Install all project dependencies:
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy the provided `.env.example` configuration file to create your local `.env` file:
```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

### 4. Running the Web Application
This repository comes pre-packaged with `kiu_monitoring.db` preloaded with **80,000 student records** and **40,000 historical clustering runs** for immediate demonstration.

To start the Flask development server:
```bash
flask run
```
Open your browser and navigate to `http://127.0.0.1:5000` to view the landing page and login portal.

#### Creating Administrator Credentials
To log in, you will need an administrator account. You can create one easily using the CLI manager:
```bash
python manage.py create-admin your_username your_password
```
Use these credentials on the login screen to access the full clustering and reporting dashboards.

#### Optional: Starting with a Fresh Database
If you wish to wipe the preloaded database and initialize a clean, empty database structure:
```bash
python manage.py init-db
python manage.py create-admin admin admin123
```
You can then upload `KIU_Student_Dataset_20000.xlsx` or another CSV dataset through the interface to run your own clustering simulations.


## Project layout

```
app/
  __init__.py          # application factory
  config.py             # env-based config + business-rule constants
  extensions.py          # db, login_manager, migrate singletons
  models.py              # User, Dataset, Student, ClusterResult (Table 3.4)
  auth/routes.py          # login / logout (Auth Manager)
  datasets/
    preprocessing.py       # upload-time CSV schema validation
    routes.py               # POST /api/datasets  (Upload Module, UC01)
  clustering/
    engine.py                # ClusteringEngine - the KMeans wrapper (core logic)
    routes.py                 # POST /api/clustering/datasets/<id>/run (UC02)
  dashboard/routes.py           # dashboard data, student search, history (UC03/UC04)
  reports/routes.py              # CSV download (UC05)
  templates/                      # Bootstrap + Chart.js shell
manage.py                          # CLI: init-db, create-admin
run.py                               # dev server entrypoint
```

## The clustering engine (`app/clustering/engine.py`)

- `ClusteringEngine(student_type="returning" | "new")` — instantiate one
  per model; the two feature sets (3 features vs. 2) are never mixed.
- `.fit(df)` — runs the full production pipeline: clean → validate size (≥30)
  → Min-Max normalize → KMeans (k-means++, K=3, n_init=10, max_iter=300) →
  rank clusters into High Performing / Average Performing / At Risk → attach
  action flags. Returns a `ClusteringResult`.
- `.evaluate_train_test(df)` — 80/20 split done *before* scaling, scaler and
  KMeans fitted on the training 80% only, test 20% assigned to frozen
  centroids. Returns a `ModelEvaluationReport` with an `possible_overfit` flag.
- `.compute_diagnostics(X)` — WCSS + silhouette for K=2..8, for the Elbow and
  Silhouette dashboard plots.

Run it standalone (no Flask/DB needed) for experimentation:

```python
import pandas as pd
from app.clustering.engine import ClusteringEngine

df = pd.read_csv("sample_returning_students.csv")
engine = ClusteringEngine(student_type="returning")
result = engine.fit(df)
print(result.cluster_names[:10])
```

## Next steps

- Wire the dashboard templates to the JSON endpoints with Chart.js (scatter,
  bar, radar, elbow/silhouette).
- Add `pytest` unit tests for `preprocessing.py` and `engine.py` edge cases
  (empty dataset, all-outlier dataset, dataset under the 30-record minimum).
- Add a MySQL `DATABASE_URL` in `.env` and run `flask db upgrade` for
  production deployment.
"# student_monitoring_system" 
