from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import db, login_manager
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.parent import parent_bp
from routes.api import api_bp
from models.user import User
import os

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    CSRFProtect(app)
    login_manager.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(parent_bp, url_prefix="/parent")
    app.register_blueprint(api_bp, url_prefix="/api")
    csrf = app.extensions["csrf"]
    csrf.exempt(api_bp)

    @app.errorhandler(403)
    def forbidden(_):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(_):
        return render_template("errors/500.html"), 500

    with app.app_context():
        db.create_all()
        admin_username = os.environ.get("ADMIN_USERNAME")
        admin_password = os.environ.get("ADMIN_PASSWORD")
        if admin_username and admin_password and not User.query.filter_by(username=admin_username).first():
            admin = User(username=admin_username, role="admin")
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
