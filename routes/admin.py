from datetime import date, datetime, timedelta
from io import StringIO
import csv
from flask import Blueprint, flash, redirect, render_template, request, url_for, Response, abort, current_app
from flask_login import current_user, login_required
from models import db
from models.user import User
from models.parent import Parent
from models.student import Student
from models.attendance import Attendance
from services.attendance_service import normalize_uid
from services.report_service import dashboard_stats, attendance_summary

admin_bp = Blueprint("admin", __name__)

def admin_required(view):
    from functools import wraps
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "admin": abort(403)
        return view(*args, **kwargs)
    return wrapped

@admin_bp.route("/")
@admin_required
def dashboard():
    stats = dashboard_stats()
    recent = Attendance.query.join(Student).order_by(Attendance.date.desc(), Attendance.time.desc()).limit(8).all()
    return render_template("admin/dashboard.html", stats=stats, recent=recent)

@admin_bp.route("/students")
@admin_required
def students():
    q = Student.query
    search = request.args.get("search", "").strip()
    grade = request.args.get("grade", "").strip()
    class_name = request.args.get("class_name", "").strip()
    if search:
        term = f"%{search}%"
        q = q.filter(db.or_(Student.first_name.ilike(term), Student.last_name.ilike(term), Student.student_code.ilike(term), Student.rfid_uid.ilike(term)))
    if grade: q = q.filter_by(grade=grade)
    if class_name: q = q.filter_by(class_name=class_name)
    students_list = q.order_by(Student.last_name, Student.first_name).all()
    grades = [x[0] for x in db.session.query(Student.grade).distinct().order_by(Student.grade).all()]
    classes = [x[0] for x in db.session.query(Student.class_name).distinct().order_by(Student.class_name).all()]
    return render_template("admin/students.html", students=students_list, grades=grades, classes=classes, filters={"search":search,"grade":grade,"class_name":class_name})

@admin_bp.route("/students/new", methods=["GET", "POST"])
@admin_required
def student_create():
    parents = Parent.query.order_by(Parent.last_name).all()
    if request.method == "POST":
        data = {k: request.form.get(k, "").strip() for k in ["first_name", "last_name", "student_code", "rfid_uid", "grade", "class_name"]}
        parent_id = request.form.get("parent_id") or None
        if not all(data.values()):
            flash("تمام فیلدهای دانش‌آموز به‌جز والد الزامی هستند.", "danger")
        elif Student.query.filter_by(student_code=data["student_code"]).first():
            flash("این کد دانش‌آموزی قبلاً ثبت شده است.", "danger")
        else:
            normalized_uid = normalize_uid(data["rfid_uid"])
            if Student.query.filter_by(rfid_uid=normalized_uid).first():
                flash("این شناسه کارت RFID قبلاً ثبت شده است.", "danger")
            else:
                try:
                    student_data = data.copy()
                    student_data["rfid_uid"] = normalized_uid
                    student = Student(**student_data, parent_id=int(parent_id) if parent_id else None)
                    db.session.add(student)
                    db.session.commit()
                    flash("دانش‌آموز با موفقیت ثبت شد.", "success")
                    return redirect(url_for("admin.students"))
                except Exception:
                    db.session.rollback()
                    current_app.logger.exception("Error while creating student")
                    flash("ثبت دانش‌آموز انجام نشد. لطفاً لاگ سرور را بررسی کنید.", "danger")
    return render_template("admin/student_form.html", student=None, parents=parents, title="افزودن دانش‌آموز")

@admin_bp.route("/students/<int:student_id>")
@admin_required
def student_detail(student_id):
    student = db.get_or_404(Student, student_id)
    attendances = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.date.desc(), Attendance.time.desc()).all()
    return render_template("admin/student_detail.html", student=student, attendances=attendances)

@admin_bp.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@admin_required
def student_edit(student_id):
    student = db.get_or_404(Student, student_id); parents = Parent.query.order_by(Parent.last_name).all()
    if request.method == "POST":
        fields = ["first_name","last_name","student_code","grade","class_name"]
        for f in fields: setattr(student, f, request.form.get(f, "").strip())
        student.rfid_uid = normalize_uid(request.form.get("rfid_uid", ""))
        student.parent_id = int(request.form["parent_id"]) if request.form.get("parent_id") else None
        if not all(getattr(student, f) for f in fields) or not student.rfid_uid: flash("All required fields must be filled.", "danger")
        elif Student.query.filter(Student.student_code == student.student_code, Student.id != student.id).first(): flash("Student code already exists.", "danger")
        elif Student.query.filter(Student.rfid_uid == student.rfid_uid, Student.id != student.id).first(): flash("RFID UID already exists.", "danger")
        else: db.session.commit(); flash("Student updated.", "success"); return redirect(url_for("admin.student_detail", student_id=student.id))
    return render_template("admin/student_form.html", student=student, parents=parents, title="Edit Student")

@admin_bp.post("/students/<int:student_id>/delete")
@admin_required
def student_delete(student_id):
    student = db.get_or_404(Student, student_id); db.session.delete(student); db.session.commit(); flash("Student deleted.", "success"); return redirect(url_for("admin.students"))

@admin_bp.route("/parents")
@admin_required
def parents():
    return render_template("admin/parents.html", parents=Parent.query.order_by(Parent.last_name).all())

@admin_bp.route("/parents/new", methods=["GET", "POST"])
@admin_required
def parent_create():
    if request.method == "POST":
        username = request.form.get("username", "").strip(); password = request.form.get("password", "")
        if User.query.filter_by(username=username).first(): flash("Username already exists.", "danger")
        elif not username or len(password) < 8: flash("Username is required and password must be at least 8 characters.", "danger")
        else:
            u=User(username=username, role="parent"); u.set_password(password); p=Parent(user=u, first_name=request.form.get("first_name","").strip(), last_name=request.form.get("last_name","").strip(), phone=request.form.get("phone","").strip()); db.session.add(p); db.session.commit(); flash("Parent created.", "success"); return redirect(url_for("admin.parents"))
    return render_template("admin/parent_form.html", parent=None, title="Add Parent")

@admin_bp.route("/parents/<int:parent_id>/edit", methods=["GET", "POST"])
@admin_required
def parent_edit(parent_id):
    p=db.get_or_404(Parent,parent_id)
    if request.method == "POST":
        p.first_name=request.form.get("first_name","").strip(); p.last_name=request.form.get("last_name","").strip(); p.phone=request.form.get("phone","").strip(); p.user.username=request.form.get("username","").strip()
        new_password=request.form.get("password","")
        if new_password: p.user.set_password(new_password)
        if not p.first_name or not p.last_name or not p.user.username: flash("Name and username are required.","danger")
        elif User.query.filter(User.username==p.user.username, User.id!=p.user_id).first(): flash("Username already exists.","danger")
        else: db.session.commit(); flash("Parent updated.","success"); return redirect(url_for("admin.parents"))
    return render_template("admin/parent_form.html", parent=p, title="Edit Parent")

@admin_bp.post("/parents/<int:parent_id>/delete")
@admin_required
def parent_delete(parent_id):
    p=db.get_or_404(Parent,parent_id); db.session.delete(p); db.session.commit(); flash("Parent deleted; linked students are unassigned.","success"); return redirect(url_for("admin.parents"))

@admin_bp.route("/attendance")
@admin_required
def attendance():
    q=Attendance.query.join(Student)
    date_filter=request.args.get("date",""); student_id=request.args.get("student_id",""); class_name=request.args.get("class_name","")
    if date_filter:
        try: q=q.filter(Attendance.date==datetime.strptime(date_filter,"%Y-%m-%d").date())
        except ValueError: date_filter=""
    if student_id and student_id.isdigit(): q=q.filter(Attendance.student_id==int(student_id))
    if class_name: q=q.filter(Student.class_name==class_name)
    rows=q.order_by(Attendance.date.desc(),Attendance.time.desc()).all()
    return render_template("admin/attendance.html", rows=rows, students=Student.query.order_by(Student.last_name).all(), classes=[x[0] for x in db.session.query(Student.class_name).distinct().order_by(Student.class_name)], filters={"date":date_filter,"student_id":student_id,"class_name":class_name})

@admin_bp.route("/reports")
@admin_required
def reports():
    today=date.today(); start=request.args.get("start",today.isoformat()); end=request.args.get("end",today.isoformat()); student_id=request.args.get("student_id",""); class_name=request.args.get("class_name","")
    try: start_date=datetime.strptime(start,"%Y-%m-%d").date(); end_date=datetime.strptime(end,"%Y-%m-%d").date()
    except ValueError: start_date=end_date=today; start=end=today.isoformat()
    rows=attendance_summary(start_date,end_date,int(student_id) if student_id.isdigit() else None,class_name or None)
    present_count=len([r for r in rows if r.status=="present"]); absent_count=max(0, Student.query.count()*((end_date-start_date).days+1)-present_count)
    return render_template("admin/reports.html", rows=rows, students=Student.query.order_by(Student.last_name).all(), classes=[x[0] for x in db.session.query(Student.class_name).distinct().order_by(Student.class_name)], filters={"start":start,"end":end,"student_id":student_id,"class_name":class_name}, present_count=present_count, absent_count=absent_count)

@admin_bp.get("/reports/csv")
@admin_required
def reports_csv():
    today=date.today(); start=request.args.get("start",today.isoformat()); end=request.args.get("end",today.isoformat())
    try: start_date=datetime.strptime(start,"%Y-%m-%d").date(); end_date=datetime.strptime(end,"%Y-%m-%d").date()
    except ValueError: start_date=end_date=today
    rows=attendance_summary(start_date,end_date,request.args.get("student_id") or None,request.args.get("class_name") or None)
    output=StringIO(); writer=csv.writer(output); writer.writerow(["Date","Time","Student","Code","Class","Grade","Status"])
    for r in rows: writer.writerow([r.date.isoformat(),r.time.strftime("%H:%M:%S"),r.student.full_name,r.student.student_code,r.student.class_name,r.student.grade,r.status])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=attendance-report.csv"})
