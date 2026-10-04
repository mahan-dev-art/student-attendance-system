from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please sign in to continue."
login_manager.login_message_category = "warning"

from models.user import User
from models.parent import Parent
from models.student import Student
from models.attendance import Attendance

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
