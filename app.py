
import os
from flask import Flask
from config import Config
from extensions import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # مسیر قابل ساخت برای دیتابیس SQLite
    database_dir = "/tmp/attendance-data"
    os.makedirs(database_dir, exist_ok=True)

    database_path = os.path.join(database_dir, "attendance.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///" + database_path
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # راه‌اندازی دیتابیس
    db.init_app(app)

    # ثبت مسیرهای پروژه را در این قسمت نگه دار
    # مثال:
    # from routes.api import api_bp
    # app.register_blueprint(api_bp)

    with app.app_context():
        # مدل‌ها باید قبل از create_all وارد شده باشند
        # مثال:
        # from models.user import User
        # from models.student import Student

        db.create_all()

        # ساخت ادمین اولیه در صورت تنظیم متغیرهای محیطی
        try:
            from models.user import User

            username = os.environ.get("ADMIN_USERNAME")
            password = os.environ.get("ADMIN_PASSWORD")

            if username and password:
                admin = User.query.filter_by(
                    username=username
                ).first()

                if not admin:
                    admin = User(
                        username=username,
                        role="admin"
                    )
                    admin.set_password(password)
                    db.session.add(admin)
                    db.session.commit()

        except Exception:
            app.logger.exception(
                "Admin initialization failed"
            )
            raise

    return app
