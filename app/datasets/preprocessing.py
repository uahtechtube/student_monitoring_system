"""
Upload-time validation for CSV datasets (Section 3.3, Step 1 + schema contract).
This is deliberately separate from app/clustering/engine.py: this module only
checks that the raw upload is well-formed enough to store in the database;
the clustering engine performs its own cleaning pass right before fitting.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd

REQUIRED_COLUMNS_BASE = [
    "matric_number",
    "full_name",
    "level",
    "student_type",
    "attendance_rate",
    "assessment_score",
]
# cgpa is required only for rows where student_type == "Returning"


def validate_schema(df: pd.DataFrame) -> List[str]:
    """Returns a list of human-readable schema errors; empty list means OK."""
    errors = []
    missing_cols = [c for c in REQUIRED_COLUMNS_BASE if c not in df.columns]
    if missing_cols:
        errors.append(f"Missing required column(s): {', '.join(missing_cols)}")
        return errors  # can't check further without the base columns

    bad_types = df[~df["student_type"].isin(["Returning", "New"])]
    if not bad_types.empty:
        errors.append(
            f"{len(bad_types)} row(s) have an invalid student_type "
            "(must be exactly 'Returning' or 'New')."
        )

    if "cgpa" not in df.columns:
        # Acceptable if the dataset only contains new students; flagged below otherwise.
        returning_rows = df[df["student_type"] == "Returning"]
        if not returning_rows.empty:
            errors.append("Column 'cgpa' is required for rows tagged 'Returning'.")
    else:
        missing_cgpa = df[(df["student_type"] == "Returning") & (df["cgpa"].isna())]
        if not missing_cgpa.empty:
            errors.append(
                f"{len(missing_cgpa)} 'Returning' row(s) are missing a CGPA value."
            )

    return errors


def summarize_upload(df: pd.DataFrame) -> Dict[str, int]:
    """Quick counts surfaced to the admin in the upload confirmation screen."""
    duplicate_ids = df["matric_number"].duplicated().sum()
    missing_required = df[REQUIRED_COLUMNS_BASE].isna().any(axis=1).sum()

    return {
        "rows_received": int(len(df)),
        "duplicate_matric_numbers": int(duplicate_ids),
        "rows_with_missing_required_fields": int(missing_required),
        "returning_students": int((df["student_type"] == "Returning").sum()),
        "new_students": int((df["student_type"] == "New").sum()),
    }


def split_by_student_type(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (returning_df, new_df)."""
    returning_df = df[df["student_type"] == "Returning"].copy()
    new_df = df[df["student_type"] == "New"].copy()
    return returning_df, new_df
