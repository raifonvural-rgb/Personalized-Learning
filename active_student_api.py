from flask import Blueprint, jsonify, request, session
from profile_storage import get_profile

active_student_api = Blueprint("active_student_api", __name__)


@active_student_api.get("/api/active-student")
def read_active_student():
    student_id = session.get("active_student_id")

    if not student_id:
        return jsonify({"student": None})

    profile = get_profile(student_id)

    if profile is None:
        session.pop("active_student_id", None)
        return jsonify({"student": None})

    return jsonify({
        "student": {
            "id": profile["id"],
            "name": profile["general"]["name"]
        }
    })


@active_student_api.post("/api/active-student")
def set_active_student():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Geçersiz istek."}), 400

    student_id = data.get("student_id")

    if student_id is None or student_id == "":
        session.pop("active_student_id", None)
        return jsonify({"student": None})

    if not isinstance(student_id, str):
        return jsonify({"error": "Geçersiz öğrenci kimliği."}), 400

    profile = get_profile(student_id)

    if profile is None:
        return jsonify({"error": "Öğrenci bulunamadı."}), 404

    session["active_student_id"] = student_id

    return jsonify({
        "student": {
            "id": profile["id"],
            "name": profile["general"]["name"]
        }
    })
