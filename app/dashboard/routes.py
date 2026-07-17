from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required

from app.extensions import db
from app.models import ClusterResult, Dataset, Student

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    return render_template("landing.html")


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@dashboard_bp.route("/api/dashboard/<int:dataset_id>")
@login_required
def dashboard_data(dataset_id):
    """UC03 - View Dashboard. Returns chart-ready JSON for scatter/bar/radar plots."""
    rows = (
        db.session.query(Student, ClusterResult)
        .join(ClusterResult, ClusterResult.student_id == Student.student_id)
        .filter(ClusterResult.dataset_id == dataset_id)
        .all()
    )

    points = [
        {
            "matric_number": student.matric_number,
            "full_name": student.full_name,
            "level": student.level,
            "student_type": student.student_type,
            "cgpa": student.cgpa,
            "attendance_rate": student.attendance_rate,
            "assessment_score": student.assessment_score,
            "cluster_label": result.cluster_label,
            "action_flag": result.action_flag,
        }
        for student, result in rows
    ]

    cluster_sizes = {}
    for p in points:
        cluster_sizes[p["cluster_label"]] = cluster_sizes.get(p["cluster_label"], 0) + 1

    return jsonify(points=points, cluster_sizes=cluster_sizes)


@dashboard_bp.route("/api/students/search")
@login_required
def student_profile():
    """UC04 - View Student Profile, searched by matric number or name."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify(error="Provide a 'q' query parameter (matric number or name)."), 400

    student = (
        Student.query.filter(
            (Student.matric_number == query) | (Student.full_name.ilike(f"%{query}%"))
        ).first()
    )
    if student is None:
        return jsonify(error="Student not found."), 404

    latest_result = (
        ClusterResult.query.filter_by(student_id=student.student_id)
        .order_by(ClusterResult.analysis_date.desc())
        .first()
    )

    return jsonify(
        matric_number=student.matric_number,
        full_name=student.full_name,
        student_type=student.student_type,
        level=student.level,
        cgpa=student.cgpa,
        attendance_rate=student.attendance_rate,
        assessment_score=student.assessment_score,
        cluster_label=latest_result.cluster_label if latest_result else None,
        action_flag=latest_result.action_flag if latest_result else None,
    )


@dashboard_bp.route("/api/datasets/<int:dataset_id>/history")
@login_required
def historical_analysis(dataset_id):
    """Historical Analysis view - all past clustering runs for a dataset."""
    runs = (
        db.session.query(ClusterResult.analysis_date, ClusterResult.wcss, ClusterResult.silhouette_score)
        .filter(ClusterResult.dataset_id == dataset_id)
        .distinct()
        .order_by(ClusterResult.analysis_date.desc())
        .all()
    )
    return jsonify(
        runs=[
            {
                "analysis_date": r.analysis_date.isoformat(),
                "wcss": r.wcss,
                "silhouette_score": r.silhouette_score,
            }
            for r in runs
        ]
    )
