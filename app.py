
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

# ساخت دیتابیس
db = SQLAlchemy()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # مسیر دیتابیس SQLite
    database_dir = "/tmp/attendance-data"
    os.makedirs(database_dir, exist_ok=True)

    database_path = os.path.join(database_dir, "attendance.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///" + database_path
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # اتصال دیتابیس به Flask
    db.init_app(app)

    # ثبت مسیرهای برنامه
    # نام Blueprintها باید با پروژه خودت مطابقت داشته باشد.
    try:
        from routes.api import api_bp
        app.register_blueprint(api_bp)
    except ImportError:
        app.logger.warning(
            "API blueprint was not registered. Check routes/api.py"
        )

    # ایجاد جدول‌ها و ساخت ادمین
    with app.app_context():
        # مدل‌ها را وارد کن تا SQLAlchemy جدول‌هایشان را بشناسد.
        try:
            from models.user import User
        except ImportError:
            User = None

        try:
            from models.student import Student
        except ImportError:
            Student = None

        try:
            from models.parent import Parent
        except ImportError:
            Parent = None

        db.create_all()

        # ساخت ادمین اولیه
        if User is not None:
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

    return app
