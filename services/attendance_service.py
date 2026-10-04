from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from models import db
from models.attendance import Attendance
from models.student import Student

def normalize_uid(uid):
    return "".join(str(uid).split()).upper()

def record_attendance_by_uid(uid):
    normalized = normalize_uid(uid)
    if not normalized:
        return None, "RFID UID is required.", False
    student = Student.query.filter_by(rfid_uid=normalized).first()
    if student is None:
        return None, "Unknown RFID card", False
    now = datetime.now().astimezone()
    existing = Attendance.query.filter_by(student_id=student.id, date=now.date()).first()
    if existing:
        return existing, "Attendance already recorded today", True
    attendance = Attendance(student_id=student.id, date=now.date(), time=now.time().replace(microsecond=0), status="present")
    db.session.add(attendance)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        existing = Attendance.query.filter_by(student_id=student.id, date=now.date()).first()
        return existing, "Attendance already recorded today", True
    return attendance, "Attendance recorded", True
