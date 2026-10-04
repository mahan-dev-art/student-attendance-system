from datetime import date
from sqlalchemy import func
from models import db
from models.student import Student
from models.parent import Parent
from models.attendance import Attendance

def dashboard_stats():
    today = date.today()
    total_students = Student.query.count()
    total_parents = Parent.query.count()
    present_today = Attendance.query.filter_by(date=today, status="present").count()
    absent_today = max(total_students - present_today, 0)
    return dict(total_students=total_students, total_parents=total_parents, present_today=present_today, absent_today=absent_today)

def attendance_summary(start_date, end_date, student_id=None, class_name=None):
    q = Attendance.query.join(Student).filter(Attendance.date.between(start_date, end_date))
    if student_id:
        q = q.filter(Attendance.student_id == student_id)
    if class_name:
        q = q.filter(Student.class_name == class_name)
    return q.order_by(Attendance.date.desc(), Attendance.time.desc()).all()
