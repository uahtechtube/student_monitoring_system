from datetime import datetime

import bcrypt
from flask_login import UserMixin

from app.extensions import db


class User(UserMixin, db.Model):
    """Administrator accounts. See Table 3.4 - USERS."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="Lecturer")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    datasets = db.relationship("Dataset", backref="uploader", lazy=True)

    __table_args__ = (
        db.CheckConstraint(
            "role IN ('Admin', 'Lecturer', 'Exam Officer')", name="ck_user_role_valid"
        ),
    )

    def get_id(self):
        # Flask-Login requires get_id() to return a string.
        return str(self.user_id)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = bcrypt.hashpw(
            raw_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.checkpw(
            raw_password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    def __repr__(self):
        return f"<User {self.username}>"


class Dataset(db.Model):
    """One row per uploaded CSV file. See Table 3.4 - DATASETS."""

    __tablename__ = "datasets"

    dataset_id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    record_count = db.Column(db.Integer, nullable=False, default=0)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)

    students = db.relationship(
        "Student", backref="dataset", lazy=True, cascade="all, delete-orphan"
    )
    cluster_results = db.relationship(
        "ClusterResult", backref="dataset", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Dataset {self.filename} ({self.record_count} records)>"


class Student(db.Model):
    """Individual student academic record per dataset. See Table 3.4 - STUDENTS."""

    __tablename__ = "students"

    student_id = db.Column(db.Integer, primary_key=True)

    # "Returning" or "New" - determines which clustering model this record
    # is routed to (Section 3.3.1 / 3.7).
    student_type = db.Column(db.String(20), nullable=False)

    matric_number = db.Column(db.String(30), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    level = db.Column(db.Integer, nullable=False)

    # Nullable because new students have no CGPA history yet.
    cgpa = db.Column(db.Float, nullable=True)
    attendance_rate = db.Column(db.Float, nullable=False)
    assessment_score = db.Column(db.Float, nullable=False)

    dataset_id = db.Column(
        db.Integer, db.ForeignKey("datasets.dataset_id"), nullable=False
    )

    cluster_results = db.relationship(
        "ClusterResult", backref="student", lazy=True, cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.CheckConstraint(
            "student_type IN ('Returning', 'New')", name="ck_student_type_valid"
        ),
    )

    def __repr__(self):
        return f"<Student {self.matric_number} ({self.student_type})>"


class ClusterResult(db.Model):
    """Clustering output per student per analysis run. See Table 3.4 - CLUSTERRESULTS."""

    __tablename__ = "cluster_results"

    result_id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(
        db.Integer, db.ForeignKey("datasets.dataset_id"), nullable=False
    )
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.student_id"), nullable=False
    )

    # "High Performing" | "Average Performing" | "At Risk"
    cluster_label = db.Column(db.String(30), nullable=False)
    action_flag = db.Column(db.String(120), nullable=False)

    wcss = db.Column(db.Float, nullable=True)
    silhouette_score = db.Column(db.Float, nullable=True)
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ClusterResult student={self.student_id} label={self.cluster_label}>"
