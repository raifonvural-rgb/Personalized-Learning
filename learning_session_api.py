"""
Student learning session management.

Independent of the teacher's active student selection.
Teacher-assisted identification for supervised learning.
"""

from flask import Blueprint, jsonify, request, session
from profile_storage import get_profile


learning_session_api = Blueprint(
    "learning_session_api",
    __name__
)

SESSION_KEY = "learning_student_id"


def student_summary(profile):
    return {
        "id": profile["id"],
        "name": profile["general"]["name"]
    }


@learning_session_api.get("/api/learning-session")
def read_learning_session():

    student_id = session.get(SESSION_KEY)

    if not student_id:
        return jsonify(student=None)

    profile = get_profile(student_id)

    if profile is None:
        session.pop(SESSION_KEY, None)
        return jsonify(student=None)

    return jsonify(student=student_summary(profile))


@learning_session_api.post("/api/learning-session")
def start_learning_session():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(error="Geçersiz istek."), 400

    student_id = data.get("student_id")

    if not isinstance(student_id, str) or not student_id.strip():
        return jsonify(error="Öğrenci seçilmelidir."), 400

    if session.get(SESSION_KEY):
        return jsonify(
            error="Önce mevcut oturumu sonlandırınız."
        ), 409

    profile = get_profile(student_id)

    if profile is None:
        return jsonify(error="Öğrenci bulunamadı."), 404

    session[SESSION_KEY] = student_id

    return jsonify(student=student_summary(profile))


@learning_session_api.delete("/api/learning-session")
def end_learning_session():

    session.pop(SESSION_KEY, None)

    return jsonify(student=None)


@learning_session_api.after_request
def disable_learning_session_cache(response):

    response.headers["Cache-Control"] = "no-store, max-age=0"

    return response
