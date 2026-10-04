from functools import wraps
from flask import Blueprint, abort, render_template, request
from flask_login import current_user, login_required
from models import db
from models.student import Student
from models.attendance import Attendance

parent_bp=Blueprint("parent",__name__)

def parent_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args,**kwargs):
        if current_user.role!="parent" or not current_user.parent: abort(403)
        return view(*args,**kwargs)
    return wrapped

@parent_bp.route("/")
@parent_required
def dashboard():
    students=current_user.parent.students
    selected_id=request.args.get("student_id","")
    selected=next((s for s in students if str(s.id)==selected_id), students[0] if students else None)
    recent=Attendance.query.filter_by(student_id=selected.id).order_by(Attendance.date.desc(),Attendance.time.desc()).limit(10).all() if selected else []
    present=Attendance.query.filter_by(student_id=selected.id,status="present").count() if selected else 0
    return render_template("parent/dashboard.html",students=students,selected=selected,recent=recent,present=present,absent=0)

@parent_bp.get("/attendance")
@parent_required
def attendance():
    students=current_user.parent.students; selected_id=request.args.get("student_id",""); selected=next((s for s in students if str(s.id)==selected_id), students[0] if students else None)
    rows=Attendance.query.filter_by(student_id=selected.id).order_by(Attendance.date.desc(),Attendance.time.desc()).all() if selected else []
    return render_template("parent/attendance.html",students=students,selected=selected,rows=rows)

@parent_bp.get("/profile")
@parent_required
def profile(): return render_template("parent/profile.html", parent=current_user.parent)
