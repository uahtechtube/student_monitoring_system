"""
Small CLI for one-off admin tasks.

Usage:
    python manage.py create-admin <username> <password>
    python manage.py init-db
"""

import sys

from app import create_app
from app.extensions import db
from app.models import User


def create_admin(username: str, password: str) -> None:
    app = create_app()
    with app.app_context():
        if User.query.filter_by(username=username).first():
            print(f"User '{username}' already exists.")
            return
        user = User(username=username, role="Admin")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Admin user '{username}' created.")


def create_user(username: str, password: str, role: str) -> None:
    app = create_app()
    with app.app_context():
        if role not in ("Admin", "Lecturer", "Exam Officer"):
            print(f"Invalid role '{role}'. Expected 'Admin', 'Lecturer', or 'Exam Officer'.")
            return
        if User.query.filter_by(username=username).first():
            print(f"User '{username}' already exists.")
            return
        user = User(username=username, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"User '{username}' with role '{role}' created.")


def init_db() -> None:
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Database tables created.")
        
        seeded = False
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", role="Admin")
            admin.set_password("adminpass")
            db.session.add(admin)
            print("Seeded default Admin user 'admin' (password: adminpass).")
            seeded = True
            
        if not User.query.filter_by(username="lecturer").first():
            lecturer = User(username="lecturer", role="Lecturer")
            lecturer.set_password("lecturerpass")
            db.session.add(lecturer)
            print("Seeded default Lecturer user 'lecturer' (password: lecturerpass).")
            seeded = True
            
        if not User.query.filter_by(username="examofficer").first():
            officer = User(username="examofficer", role="Exam Officer")
            officer.set_password("officerpass")
            db.session.add(officer)
            print("Seeded default Exam Officer user 'examofficer' (password: officerpass).")
            seeded = True
            
        if seeded:
            db.session.commit()
            print("Default users database seed complete.")



if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    if command == "create-admin":
        create_admin(sys.argv[2], sys.argv[3])
    elif command == "create-user":
        create_user(sys.argv[2], sys.argv[3], sys.argv[4])
    elif command == "init-db":
        init_db()
    else:
        print(f"Unknown command '{command}'.")
        print(__doc__)
