"""
KMeans clustering engine for the KIU Student Segmentation and Academic
Monitoring System.

Implements, per the project's Chapter Three methodology:
  - Section 3.3        : IQR outlier detection, Min-Max normalization
  - Section 3.3.1       : two independent models (Returning / New students)
  - Section 3.8         : KMeans with k-means++ init, n_init=10, max_iter=300, K=3
  - Section 3.8.1       : 80/20 train/test evaluation with frozen centroids
  - Section 2.5.2       : Elbow / Silhouette diagnostics across K=2..8

This module has no Flask or database dependency - it operates purely on
pandas DataFrames / NumPy arrays so it can be unit tested in isolation and
reused outside the web app (e.g. in a notebook or CLI script).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
import pickle
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

# --------------------------------------------------------------------------
# Feature configuration (Table 3.1 / Table 3.1(b))
# --------------------------------------------------------------------------

RETURNING_FEATURES: List[str] = ["cgpa", "attendance_rate", "assessment_score"]
NEW_STUDENT_FEATURES: List[str] = ["attendance_rate", "assessment_score"]

CLUSTER_LABELS_BY_RANK = ["High Performing", "Average Performing", "At Risk"]

ACTION_FLAGS: Dict[str, str] = {
    "High Performing": "No intervention required; consider for peer-mentorship or scholarship nomination.",
    "Average Performing": "Monitor next semester; recommend optional tutorial sessions.",
    "At Risk": "Refer to academic advisor for mentorship; flag for probation review if pattern persists.",
}


class InsufficientDataError(ValueError):
    """Raised when a dataset does not meet the minimum size for clustering (Section 3.3, Step 4)."""


def _features_for(student_type: str) -> List[str]:
    student_type = student_type.strip().lower()
    if student_type == "returning":
        return RETURNING_FEATURES
    if student_type == "new":
        return NEW_STUDENT_FEATURES
    raise ValueError(f"Unknown student_type '{student_type}'. Expected 'returning' or 'new'.")


# --------------------------------------------------------------------------
# Result containers
# --------------------------------------------------------------------------

@dataclass
class ClusteringResult:
    """Output of a production clustering run for one student-type model."""

    student_type: str
    features: List[str]
    labels: np.ndarray                     # raw KMeans cluster index per row (0..K-1)
    cluster_names: np.ndarray              # mapped label per row: High/Average/At Risk
    action_flags: np.ndarray               # mapped action string per row
    wcss: float
    silhouette: float
    centroid_rank_map: Dict[int, str]      # raw cluster index -> cluster name
    diagnostics: Dict[int, Dict[str, float]]  # K -> {"wcss": ..., "silhouette": ...} for K=2..8
    scaler: MinMaxScaler
    model: KMeans


@dataclass
class ModelEvaluationReport:
    """Output of the 80/20 train/test evaluation (Section 3.8.1)."""

    student_type: str
    train_wcss: float
    test_wcss: float
    train_silhouette: float
    test_silhouette: float
    silhouette_gap: float = field(init=False)
    possible_overfit: bool = field(init=False)
    overfit_threshold: float = 0.15

    def __post_init__(self):
        self.silhouette_gap = abs(self.train_silhouette - self.test_silhouette)
        self.possible_overfit = self.silhouette_gap > self.overfit_threshold


# --------------------------------------------------------------------------
# Preprocessing helpers (Section 3.3)
# --------------------------------------------------------------------------

def clean_missing_and_duplicates(df: pd.DataFrame, features: List[str], id_col: str = "matric_number") -> pd.DataFrame:
    """Step 1 (Data Cleaning): drop rows with missing feature values and duplicate IDs."""
    cleaned = df.dropna(subset=features).copy()
    cleaned = cleaned.drop_duplicates(subset=[id_col], keep="first")
    return cleaned.reset_index(drop=True)


def flag_outliers_iqr(df: pd.DataFrame, features: List[str], multiplier: float = 1.5) -> pd.Series:
    """
    Step 2 (Outlier Detection): IQR rule per feature.
    Returns a boolean Series, True where the row is an outlier on ANY feature.
    Rows are flagged, not silently dropped - the admin decides whether to exclude them.
    """
    is_outlier = pd.Series(False, index=df.index)
    for col in features:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - multiplier * iqr
        upper = q3 + multiplier * iqr
        is_outlier |= (df[col] < lower) | (df[col] > upper)
    return is_outlier


def validate_min_size(df: pd.DataFrame, minimum: int = 30) -> None:
    """Step 4 (Size Validation)."""
    if len(df) < minimum:
        raise InsufficientDataError(
            f"Dataset has {len(df)} records; at least {minimum} are required before clustering."
        )


# --------------------------------------------------------------------------
# Cluster labeling
# --------------------------------------------------------------------------

def _rank_centroids_to_labels(centroids: np.ndarray) -> Dict[int, str]:
    """
    Maps raw KMeans cluster indices to meaningful labels by ranking centroids
    on a composite performance score. Because all features are Min-Max
    normalized to [0, 1] and are all "higher is better" (CGPA, attendance,
    assessment score), the composite score is simply the mean of each
    centroid's coordinates.
    """
    composite_scores = centroids.mean(axis=1)
    # argsort descending: index 0 = best-performing cluster
    ranked_cluster_indices = np.argsort(-composite_scores)
    return {
        int(cluster_idx): CLUSTER_LABELS_BY_RANK[rank]
        for rank, cluster_idx in enumerate(ranked_cluster_indices)
    }


# --------------------------------------------------------------------------
# Main engine
# --------------------------------------------------------------------------

class ClusteringEngine:
    """
    Wraps scikit-learn's KMeans with the project's business rules.
    Instantiate one engine per student_type ("returning" or "new") -
    the two models must never share a fitting pass (Section 3.3.1).
    """

    def __init__(
        self,
        student_type: str,
        n_clusters: int = 3,
        n_init: int = 10,
        max_iter: int = 300,
        random_state: int = 42,
        iqr_multiplier: float = 1.5,
        min_dataset_size: int = 30,
    ):
        self.student_type = student_type
        self.features = _features_for(student_type)
        self.n_clusters = n_clusters
        self.n_init = n_init
        self.max_iter = max_iter
        self.random_state = random_state
        self.iqr_multiplier = iqr_multiplier
        self.min_dataset_size = min_dataset_size

    # ---- diagnostics -----------------------------------------------------

    def compute_diagnostics(self, X: np.ndarray, k_range=range(2, 9)) -> Dict[int, Dict[str, float]]:
        """
        Elbow + Silhouette sweep for K=2..8 (Section 2.5.2), used to render
        the diagnostic plots on the dashboard. Independent of the fixed K=3
        production model.
        """
        diagnostics: Dict[int, Dict[str, float]] = {}
        for k in k_range:
            km = KMeans(
                n_clusters=k,
                init="k-means++",
                n_init=self.n_init,
                max_iter=self.max_iter,
                random_state=self.random_state,
            )
            labels = km.fit_predict(X)
            sil = silhouette_score(X, labels, sample_size=1000, random_state=self.random_state) if k > 1 and len(set(labels)) > 1 else float("nan")
            diagnostics[k] = {"wcss": float(km.inertia_), "silhouette": float(sil)}
        return diagnostics

    # ---- production fit ---------------------------------------------------

    def fit(self, df: pd.DataFrame, id_col: str = "matric_number", run_diagnostics: bool = True) -> ClusteringResult:
        """
        Full production pipeline for one student-type model:
        clean -> validate size -> normalize -> KMeans(K=3) -> label -> action flags.

        `df` must already be filtered to rows matching this engine's student_type
        and must contain this engine's required feature columns plus `id_col`.
        """
        cleaned = clean_missing_and_duplicates(df, self.features, id_col=id_col)
        validate_min_size(cleaned, minimum=self.min_dataset_size)

        # Outliers are flagged for admin visibility but retained in the fit,
        # consistent with Section 3.3 ("flagging" rather than automatic removal).
        outlier_mask = flag_outliers_iqr(cleaned, self.features, multiplier=self.iqr_multiplier)

        scaler = MinMaxScaler()
        X = scaler.fit_transform(cleaned[self.features].values)

        model = KMeans(
            n_clusters=self.n_clusters,
            init="k-means++",
            n_init=self.n_init,
            max_iter=self.max_iter,
            random_state=self.random_state,
        )
        raw_labels = model.fit_predict(X)

        rank_map = _rank_centroids_to_labels(model.cluster_centers_)
        cluster_names = np.array([rank_map[label] for label in raw_labels])
        action_flags = np.array([ACTION_FLAGS[name] for name in cluster_names])

        sil = silhouette_score(X, raw_labels, sample_size=1000, random_state=self.random_state) if len(set(raw_labels)) > 1 else float("nan")

        diagnostics = self.compute_diagnostics(X) if run_diagnostics else {}

        result = ClusteringResult(
            student_type=self.student_type,
            features=self.features,
            labels=raw_labels,
            cluster_names=cluster_names,
            action_flags=action_flags,
            wcss=float(model.inertia_),
            silhouette=float(sil),
            centroid_rank_map=rank_map,
            diagnostics=diagnostics,
            scaler=scaler,
            model=model,
        )
        # Attach cleaned frame + outlier mask for the caller (e.g. the route
        # handler) to persist ClusterResult rows and surface outlier flags.
        result.cleaned_df = cleaned            # type: ignore[attr-defined]
        result.outlier_mask = outlier_mask      # type: ignore[attr-defined]
        return result

    # ---- train/test evaluation (Section 3.8.1) ----------------------------

    def evaluate_train_test(
        self, df: pd.DataFrame, id_col: str = "matric_number", test_size: float = 0.20
    ) -> ModelEvaluationReport:
        """
        Splits 80/20 AFTER outlier handling but BEFORE scaling, fits the
        scaler and KMeans on the training split only, then assigns the held-out
        test split to the frozen centroids (no retraining) to check whether
        the discovered structure generalizes.
        """
        cleaned = clean_missing_and_duplicates(df, self.features, id_col=id_col)
        validate_min_size(cleaned, minimum=self.min_dataset_size)

        train_df, test_df = train_test_split(
            cleaned, test_size=test_size, random_state=self.random_state
        )

        scaler = MinMaxScaler()
        X_train = scaler.fit_transform(train_df[self.features].values)
        X_test = scaler.transform(test_df[self.features].values)  # same fitted scaler, no leakage

        model = KMeans(
            n_clusters=self.n_clusters,
            init="k-means++",
            n_init=self.n_init,
            max_iter=self.max_iter,
            random_state=self.random_state,
        )
        train_labels = model.fit_predict(X_train)
        train_wcss = float(model.inertia_)
        train_sil = float(silhouette_score(X_train, train_labels, sample_size=1000, random_state=self.random_state)) if len(set(train_labels)) > 1 else float("nan")

        # Assign test rows to nearest FROZEN centroid - no fitting here.
        test_labels = model.predict(X_test)
        test_wcss = float(
            np.sum((X_test - model.cluster_centers_[test_labels]) ** 2)
        )
        test_sil = float(silhouette_score(X_test, test_labels, sample_size=1000, random_state=self.random_state)) if len(set(test_labels)) > 1 else float("nan")

        return ModelEvaluationReport(
            student_type=self.student_type,
            train_wcss=train_wcss,
            test_wcss=test_wcss,
            train_silhouette=train_sil,
            test_silhouette=test_sil,
        )


# --------------------------------------------------------------------------
# Serialization and Caching utilities
# --------------------------------------------------------------------------

def save_model_artifacts(result: ClusteringResult, model_dir: str, dataset_id: int) -> None:
    """
    Serializes the MinMaxScaler and KMeans model, and saves the diagnostics JSON,
    so that we don't have to retrain models for prediction or diagnostics views.
    """
    os.makedirs(model_dir, exist_ok=True)
    
    student_type_str = result.student_type.strip().lower()
    
    # 1. Save MinMaxScaler
    scaler_path = os.path.join(model_dir, f"scaler_{dataset_id}_{student_type_str}.pkl")
    with open(scaler_path, "wb") as f:
        pickle.dump(result.scaler, f)
        
    # 2. Save KMeans model
    model_path = os.path.join(model_dir, f"model_{dataset_id}_{student_type_str}.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(result.model, f)
        
    # 3. Save diagnostics dict as JSON
    if result.diagnostics:
        diag_path = os.path.join(model_dir, f"diagnostics_{dataset_id}_{student_type_str}.json")
        # Convert keys to string for JSON serialization compatibility
        json_diags = {str(k): v for k, v in result.diagnostics.items()}
        with open(diag_path, "w") as f:
            json.dump(json_diags, f, indent=2)


def load_model_artifacts(model_dir: str, dataset_id: int, student_type: str) -> tuple[MinMaxScaler, KMeans]:
    """Loads and returns the MinMaxScaler and KMeans model from pickled files."""
    student_type_str = student_type.strip().lower()
    scaler_path = os.path.join(model_dir, f"scaler_{dataset_id}_{student_type_str}.pkl")
    model_path = os.path.join(model_dir, f"model_{dataset_id}_{student_type_str}.pkl")
    
    if not os.path.exists(scaler_path) or not os.path.exists(model_path):
        raise FileNotFoundError(f"Model artifacts for dataset {dataset_id} ({student_type_str}) not found.")
        
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    with open(model_path, "rb") as f:
        model = pickle.load(f)
        
    return scaler, model


def load_diagnostics(model_dir: str, dataset_id: int, student_type: str) -> dict[int, dict[str, float]]:
    """Loads and returns the diagnostics map from the JSON cache file."""
    student_type_str = student_type.strip().lower()
    diag_path = os.path.join(model_dir, f"diagnostics_{dataset_id}_{student_type_str}.json")
    if not os.path.exists(diag_path):
        return {}
        
    with open(diag_path, "r") as f:
        data = json.load(f)
    # Convert string keys back to int
    return {int(k): v for k, v in data.items()}

