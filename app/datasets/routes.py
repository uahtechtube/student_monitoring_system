import io

import pandas as pd
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.datasets.preprocessing import summarize_upload, validate_schema
from app.extensions import db
from app.models import Dataset, Student

datasets_bp = Blueprint("datasets", __name__)


@datasets_bp.route("", methods=["POST"])
@login_required
def upload_dataset():
    """UC01 - Upload Dataset. Expects a multipart/form-data request with a 'file' field."""
    if "file" not in request.files:
        return jsonify(error="No file provided under field name 'file'."), 400

    file = request.files["file"]
    filename_lower = file.filename.lower()
    if not (filename_lower.endswith(".csv") or filename_lower.endswith(".xlsx")):
        return jsonify(error="Only .csv and .xlsx files are accepted."), 400

    try:
        if filename_lower.endswith(".csv"):
            df = pd.read_csv(io.StringIO(file.stream.read().decode("utf-8")))
        else:
            df = pd.read_excel(io.BytesIO(file.stream.read()))
    except Exception as exc:  # noqa: BLE001 - surface parse errors to the admin
        return jsonify(error=f"Could not parse file: {exc}"), 400

    schema_errors = validate_schema(df)
    if schema_errors:
        return jsonify(error="Schema validation failed.", details=schema_errors), 422

    summary = summarize_upload(df)

    dataset = Dataset(
        filename=file.filename,
        record_count=len(df),
        uploaded_by=current_user.user_id,
    )
    db.session.add(dataset)
    db.session.flush()  # get dataset.dataset_id before inserting students

    for _, row in df.iterrows():
        student = Student(
            student_type=row["student_type"],
            matric_number=str(row["matric_number"]),
            full_name=row["full_name"],
            level=int(row["level"]),
            cgpa=float(row["cgpa"]) if row.get("student_type") == "Returning" and not pd.isna(row.get("cgpa")) else None,
            attendance_rate=float(row["attendance_rate"]),
            assessment_score=float(row["assessment_score"]),
            dataset_id=dataset.dataset_id,
        )
        db.session.add(student)

    db.session.commit()

    return jsonify(
        dataset_id=dataset.dataset_id,
        filename=dataset.filename,
        summary=summary,
    ), 201


@datasets_bp.route("/<int:dataset_id>", methods=["GET"])
@login_required
def get_dataset(dataset_id):
    dataset = db.session.get(Dataset, dataset_id)
    if dataset is None:
        return jsonify(error="Dataset not found."), 404

    return jsonify(
        dataset_id=dataset.dataset_id,
        filename=dataset.filename,
        upload_date=dataset.upload_date.isoformat(),
        record_count=dataset.record_count,
    )


@datasets_bp.route("", methods=["GET"])
@login_required
def list_datasets():
    if current_user.role == "Admin":
        datasets = Dataset.query.order_by(Dataset.upload_date.desc()).all()
    else:
        datasets = Dataset.query.filter_by(uploaded_by=current_user.user_id).order_by(Dataset.upload_date.desc()).all()

    return jsonify(
        datasets=[
            {
                "dataset_id": d.dataset_id,
                "filename": d.filename,
                "upload_date": d.upload_date.isoformat(),
                "record_count": d.record_count,
            }
            for d in datasets
        ]
    )
