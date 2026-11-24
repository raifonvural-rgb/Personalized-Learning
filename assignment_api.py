"""
Teacher-controlled activity assignment API.

Uses the teacher's existing active student context.
Only one active assignment is permitted per student.
"""

from flask import Blueprint, jsonify, request, session

from profile_storage import get_profile
from assignment_storage import (
    get_assignment,
    assign_activity,
)


assignment_api = Blueprint(
    "assignment_api",
    __name__
)


@assignment_api.get("/api/activity-assignment")
def read_activity_assignment():

    student_id = session.get("active_student_id")

    if not student_id or get_profile(student_id) is None:
        return jsonify(
            error="Önce öğrenci seçiniz."
        ), 400

    return jsonify(
        ok=True,
        assignment=get_assignment(student_id)
    )


@assignment_api.post("/api/activity-assignment")
def create_activity_assignment():

    student_id = session.get("active_student_id")

    if not student_id or get_profile(student_id) is None:
        return jsonify(
            error="Önce öğrenci seçiniz."
        ), 400

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(
            error="Geçersiz istek."
        ), 400

    activity_id = data.get("activity_id")

    if not isinstance(activity_id, str) or not activity_id.strip():
        return jsonify(
            error="Etkinlik seçilmelidir."
        ), 400

    try:
        assignment = assign_activity(
            student_id,
            activity_id
        )

    except ValueError as error:
        return jsonify(
            error=str(error)
        ), 400

    return jsonify(
        ok=True,
        assignment=assignment,
        message="Etkinlik öğrenciye atandı."
    )


@assignment_api.after_request
def disable_assignment_cache(response):

    response.headers["Cache-Control"] = "no-store, max-age=0"

    return response
