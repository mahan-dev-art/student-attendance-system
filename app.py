
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

# --------------------------------------------------
# Database
# --------------------------------------------------

db = SQLAlchemy()


# --------------------------------------------------
# Application Factory
# --------------------------------------------------

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Create a writable directory for SQLite
    database_dir = "/tmp/attendance-data"
    os.makedirs(database_dir, exist_ok=True)

    database_path = os.path.join(database_dir, "attendance.db")

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///" + database_path
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize SQLAlchemy with Flask
    db.init_app(app)

    # --------------------------------------------------
    # Register Blueprints
    # --------------------------------------------------
    # Keep your project's existing blueprint imports here.
    # Examples (only if these names exist in your project):
    #
    # from routes.auth import auth_bp
    # app.register_blueprint(auth_bp)
    #
    # from routes.admin import admin_bp
    # app.register_blueprint(admin_bp)
    #
    # from routes.students import students_bp
    # app.register_blueprint(students_bp)
    #
    # from routes.parents import parents_bp
    # app.register_blueprint(parents_bp)
    #
    # from routes.api import api_bp
    # app.register_blueprint(api_bp)

    # --------------------------------------------------
    # Load Models and Create Tables
    # --------------------------------------------------

    with app.app_context():
        from models.user import User

        # Import these if the files exist in your project.
        # They must use the same db instance imported from app.
        try:
            from models.student import Student
        except ImportError:
            app.logger.warning(
                "Student model could not be imported."
            )

        try:
            from models.parent import Parent
        except ImportError:
            app.logger.warning(
                "Parent model could not be imported."
            )

        db.create_all()

        # --------------------------------------------------
        # Create Initial Admin
        # --------------------------------------------------

        admin_username = os.environ.get("ADMIN_USERNAME")
        admin_password = os.environ.get("ADMIN_PASSWORD")

        if admin_username and admin_password:
            existing_admin = User.query.filter_by(
                username=admin_username
            ).first()

            if not existing_admin:
                admin = User(
                    username=admin_username,
                    role="admin"
                )
                admin.set_password(admin_password)

                db.session.add(admin)
                db.session.commit()

    return app
