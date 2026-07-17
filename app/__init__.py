import os

from flask import Flask

from app.config import config_by_name
from app.extensions import db, login_manager, migrate


def create_app(config_name: str = None) -> Flask:
    config_name = config_name or os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.auth.routes import auth_bp
    from app.datasets.routes import datasets_bp
    from app.clustering.routes import clustering_bp
    from app.dashboard.routes import dashboard_bp
    from app.reports.routes import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(datasets_bp, url_prefix="/api/datasets")
    app.register_blueprint(clustering_bp, url_prefix="/api/clustering")
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reports_bp, url_prefix="/api/reports")

    return app
