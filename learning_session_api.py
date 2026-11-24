"""
Student learning session management.

Independent of the teacher's active student selection.
Teacher-assisted identification for supervised learning.
Each learning session is linked to a specific assignment.
"""

from flask import Blueprint, jsonify, request, session
from profile_storage import get_profile
from assignment_storage import get_assignment, clear_assignment


learning_session_api = Blueprint(
    "learning_session_api",
    __name__
)

SESSION_KEY = "learning_student_id"
ASSIGNMENT_KEY = "learning_assignment_id"


def student_summary(profile):
    return {
        "id": profile["id"],
        "name": profile["general"]["name"]
    }


def clear_learning_session():
    session.pop(SESSION_KEY, None)
    session.pop(ASSIGNMENT_KEY, None)


@learning_session_api.get("/api/learning-session")
def read_learning_session():

    student_id = session.get(SESSION_KEY)

    if not student_id:
        clear_learning_session()
        return jsonify(student=None, assignment=None)

    profile = get_profile(student_id)

    if profile is None:
        clear_learning_session()
        return jsonify(student=None, assignment=None)

    assignment = get_assignment(student_id)

    if (
        assignment is None
        or assignment.get("id") != session.get(ASSIGNMENT_KEY)
    ):
        clear_learning_session()
        return jsonify(student=None, assignment=None)

    return jsonify(
        student=student_summary(profile),
        assignment=assignment
    )


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

    assignment = get_assignment(student_id)

    if assignment is None:
        return jsonify(
            error="Henüz etkinlik atanmadı."
        ), 409

    session[SESSION_KEY] = student_id
    session[ASSIGNMENT_KEY] = assignment["id"]

    return jsonify(
        student=student_summary(profile),
        assignment=assignment
    )


@learning_session_api.delete("/api/learning-session")
def end_learning_session():

    student_id = session.get(SESSION_KEY)
    assignment_id = session.get(ASSIGNMENT_KEY)

    if student_id and assignment_id:
        clear_assignment(student_id, assignment_id)

    clear_learning_session()

    return jsonify(student=None, assignment=None)


@learning_session_api.after_request
def disable_learning_session_cache(response):

    response.headers["Cache-Control"] = "no-store, max-age=0"

    return response
