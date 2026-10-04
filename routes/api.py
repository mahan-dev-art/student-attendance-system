from flask import Blueprint, current_app, jsonify, request
from services.attendance_service import record_attendance_by_uid

api_bp=Blueprint("api",__name__)

def valid_api_key():
    configured=current_app.config.get("ESP32_API_KEY")
    supplied=request.headers.get("X-API-Key") or request.args.get("api_key")
    return bool(configured and supplied and supplied==configured)

@api_bp.post("/attendance")
def api_attendance():
    if not valid_api_key(): return jsonify(success=False,message="Unauthorized"),401
    if not request.is_json: return jsonify(success=False,message="Content-Type must be application/json"),415
    payload=request.get_json(silent=True) or {}; uid=payload.get("rfid_uid")
    attendance,message,ok=record_attendance_by_uid(uid)
    if not ok:
        return jsonify(success=False,message=message),404 if message=="Unknown RFID card" else 400
    student=attendance.student
    return jsonify(success=True,message=message,student={"id":student.id,"name":student.full_name,"student_code":student.student_code,"date":attendance.date.isoformat(),"time":attendance.time.isoformat(),"status":attendance.status,"duplicate":message.endswith("today")})
