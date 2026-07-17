from flask import Blueprint, redirect, render_template, request, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user

from app.models import User
from app.extensions import db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_url = request.args.get("next")
            return redirect(next_url or url_for("dashboard.dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


# --------------------------------------------------------------------------
# User Management CRUD Endpoints (Admin Only)
# --------------------------------------------------------------------------

@auth_bp.route("/api/users", methods=["GET"])
@login_required
def list_users():
    if current_user.role != "Admin":
        return jsonify(error="Forbidden. Admin role required."), 403

    users = User.query.order_by(User.username).all()
    return jsonify(
        users=[
            {
                "user_id": u.user_id,
                "username": u.username,
                "role": u.role,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]
    )


@auth_bp.route("/api/users", methods=["POST"])
@login_required
def create_user():
    if current_user.role != "Admin":
        return jsonify(error="Forbidden. Admin role required."), 403

    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    role = data.get("role", "").strip()

    if not username or not password or not role:
        return jsonify(error="Missing username, password, or role."), 400

    if role not in ("Admin", "Lecturer", "Exam Officer"):
        return jsonify(error=f"Invalid role '{role}'."), 400

    if User.query.filter_by(username=username).first():
        return jsonify(error="Username already exists."), 400

    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    current_app.logger.info(f"AUDIT: User '{current_user.username}' created new user '{username}' with role '{role}'.")

    return jsonify(
        user={
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    ), 201


@auth_bp.route("/api/users/<int:user_id>", methods=["PUT"])
@login_required
def update_user(user_id):
    if current_user.role != "Admin":
        return jsonify(error="Forbidden. Admin role required."), 403

    user = db.session.get(User, user_id)
    if user is None:
        return jsonify(error="User not found."), 404

    data = request.get_json() or {}
    role = data.get("role", "").strip()
    password = data.get("password", "")

    if role:
        if role not in ("Admin", "Lecturer", "Exam Officer"):
            return jsonify(error=f"Invalid role '{role}'."), 400
        user.role = role

    if password:
        user.set_password(password)

    db.session.commit()

    current_app.logger.info(
        f"AUDIT: User '{current_user.username}' updated user '{user.username}' "
        f"(role updated: {bool(role)}, password reset: {bool(password)})."
    )

    return jsonify(
        user={
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }
    ), 200


@auth_bp.route("/api/users/<int:user_id>", methods=["DELETE"])
@login_required
def delete_user(user_id):
    if current_user.role != "Admin":
        return jsonify(error="Forbidden. Admin role required."), 403

    if user_id == current_user.user_id:
        return jsonify(error="Cannot delete your own active administrator session."), 400

    user = db.session.get(User, user_id)
    if user is None:
        return jsonify(error="User not found."), 404

    db.session.delete(user)
    db.session.commit()

    current_app.logger.info(f"AUDIT: User '{current_user.username}' deleted user '{user.username}'.")

    return jsonify(success=True, message=f"User '{user.username}' deleted successfully."), 200

