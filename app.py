import os

from flask import Flask

from config import Config
from extensions import db, login_manager


# --------------------------------------------------
# Application Factory
# --------------------------------------------------

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # --------------------------------------------------
    # SQLite Database
    # --------------------------------------------------

    database_dir = "/tmp/attendance-data"
    os.makedirs(database_dir, exist_ok=True)

    database_path = os.path.join(
        database_dir,
        "attendance.db"
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///" + database_path
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --------------------------------------------------
    # Initialize Extensions
    # --------------------------------------------------

    db.init_app(app)
    login_manager.init_app(app)

    # --------------------------------------------------
    # Load All Models
    # --------------------------------------------------

    from models.user import User
    from models.parent import Parent
    from models.student import Student
    from models.attendance import Attendance

    # --------------------------------------------------
    # Main Route
    # --------------------------------------------------

    @app.route("/")
    def index():
        return "Student Attendance System is running!"

    # --------------------------------------------------
    # Create Database Tables
    # --------------------------------------------------

    with app.app_context():
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
