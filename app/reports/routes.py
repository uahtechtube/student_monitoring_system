import csv
import io

from flask import Blueprint, Response
from flask_login import login_required

from app.extensions import db
from app.models import ClusterResult, Student

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/datasets/<int:dataset_id>/download", methods=["GET"])
@login_required
def download_report(dataset_id):
    """UC05 - Download Report: CSV of all student cluster assignments and action flags."""
    rows = (
        db.session.query(Student, ClusterResult)
        .join(ClusterResult, ClusterResult.student_id == Student.student_id)
        .filter(ClusterResult.dataset_id == dataset_id)
        .all()
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "matric_number",
            "full_name",
            "student_type",
            "cgpa",
            "attendance_rate",
            "assessment_score",
            "cluster_label",
            "action_flag",
        ]
    )
    for student, result in rows:
        writer.writerow(
            [
                student.matric_number,
                student.full_name,
                student.student_type,
                student.cgpa if student.cgpa is not None else "",
                student.attendance_rate,
                student.assessment_score,
                result.cluster_label,
                result.action_flag,
            ]
        )

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=dataset_{dataset_id}_report.csv"},
    )
