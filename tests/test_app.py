from datetime import date
from models import db
from models.user import User
from models.parent import Parent
from models.student import Student
from models.attendance import Attendance

def make_user(role, username, password="password123"):
    u=User(username=username, role=role); u.set_password(password); db.session.add(u); db.session.flush(); return u

def login(client, username, password="password123"):
    return client.post('/login', data={'username':username,'password':password}, follow_redirects=False)

def test_login_and_role_redirect(client, app):
    with app.app_context(): make_user('admin','admin')
    r=login(client,'admin'); assert r.status_code==302 and '/admin/' in r.headers['Location']

def test_unauthorized_and_role_authorization(client, app):
    assert client.get('/admin/').status_code==302
    with app.app_context(): make_user('parent','p1');
    login(client,'p1'); assert client.get('/admin/').status_code==403

def test_student_creation(app, client):
    with app.app_context(): make_user('admin','admin')
    login(client,'admin')
    r=client.post('/admin/students/new',data={'first_name':'Ali','last_name':'Ahmadi','student_code':'S1','rfid_uid':'a1b2','grade':'10','class_name':'A'})
    assert r.status_code==302
    with app.app_context(): assert Student.query.filter_by(student_code='S1').one().rfid_uid=='A1B2'

def test_attendance_creation_and_duplicate(app, client):
    with app.app_context():
        s=Student(first_name='Ali',last_name='Ahmadi',student_code='S1',rfid_uid='A1B2',grade='10',class_name='A'); db.session.add(s); db.session.commit()
    r=client.post('/api/attendance',json={'rfid_uid':'a1 b2'},headers={'X-API-Key':'test-api-key'}); assert r.status_code==200; assert r.json['success']
    r=client.post('/api/attendance',json={'rfid_uid':'A1B2'},headers={'X-API-Key':'test-api-key'}); assert r.status_code==200; assert r.json['student']['duplicate'] is True

def test_rfid_unknown_and_auth(app, client):
    assert client.post('/api/attendance',json={'rfid_uid':'A1'},headers={'X-API-Key':'bad'}).status_code==401
    with app.app_context(): make_user('admin','admin');
    assert client.post('/api/attendance',json={'rfid_uid':'A1'},headers={'X-API-Key':'test-api-key'}).status_code==404

def test_parent_isolation(app, client):
    with app.app_context():
        u1=make_user('parent','p1'); p1=Parent(user_id=u1.id,first_name='P',last_name='One'); u2=make_user('parent','p2'); p2=Parent(user_id=u2.id,first_name='P',last_name='Two'); db.session.add_all([p1,p2]); db.session.flush(); s1=Student(first_name='A',last_name='One',student_code='1',rfid_uid='11',grade='1',class_name='A',parent_id=p1.id); s2=Student(first_name='B',last_name='Two',student_code='2',rfid_uid='22',grade='1',class_name='B',parent_id=p2.id); db.session.add_all([s1,s2]); db.session.commit(); sid=s2.id
    login(client,'p1'); r=client.get(f'/parent/?student_id={sid}'); assert r.status_code==200; assert 'B Two' not in r.get_data(as_text=True)
