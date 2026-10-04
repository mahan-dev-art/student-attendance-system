from datetime import datetime, timezone
from models import db

class Attendance(db.Model):
    __tablename__ = "attendances"
    __table_args__ = (db.UniqueConstraint("student_id", "date", name="uq_student_attendance_date"),)
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="present")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    student = db.relationship("Student", back_populates="attendances")
