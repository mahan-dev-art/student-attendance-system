from datetime import datetime, timezone
from models import db

class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    student_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    rfid_uid = db.Column(db.String(64), unique=True, nullable=False, index=True)
    grade = db.Column(db.String(30), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("parents.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    parent = db.relationship("Parent", back_populates="students")
    attendances = db.relationship("Attendance", back_populates="student", cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
