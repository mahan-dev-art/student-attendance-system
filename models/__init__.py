from extensions import db, login_manager

# Import all models so SQLAlchemy knows about all relationships
from models.user import User
from models.parent import Parent
from models.student import Student
from models.attendance import Attendance


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
