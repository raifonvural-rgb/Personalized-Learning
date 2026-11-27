"""
Student learning session management.

Independent of the teacher's active student selection.

Each learning session is linked to a specific assignment
and a persistent performance session.

Teacher-assisted identification for supervised learning.
"""

import sqlite3

from flask import (
    Blueprint,
    jsonify,
    request,
    session,
    current_app
)

from profile_storage import get_profile
from assignment_storage import get_assignment, clear_assignment

from performance_models import SessionStatus

from performance_lifecycle import (
    PERFORMANCE_SESSION_KEY,
    start_performance_session,
    get_bound_performance_session,
    finish_performance_session
)


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
    session.pop(PERFORMANCE_SESSION_KEY, None)


def interrupt_learning_session(reason):
    """
    Record an identifiable interruption before clearing
    the browser's learning session.

    The current assignment is preserved.
    """

    finish_performance_session(
        performance_session_id=session.get(
            PERFORMANCE_SESSION_KEY
        ),
        student_id=session.get(SESSION_KEY),
        assignment_id=session.get(ASSIGNMENT_KEY),
        status=SessionStatus.INTERRUPTED,
        reason=reason
    )

    clear_learning_session()


def performance_storage_error(error):

    current_app.logger.error(
        "Performance storage operation failed.",
        exc_info=True
    )

    return jsonify(
        error=(
            "Öğrenme kaydı işlenemedi. "
            "Lütfen tekrar deneyiniz."
        )
    ), 503


@learning_session_api.get("/api/learning-session")
def read_learning_session():

    student_id = session.get(SESSION_KEY)

    try:

        if not student_id:

            clear_learning_session()

            return jsonify(
                student=None,
                assignment=None
            )

        profile = get_profile(student_id)

        if profile is None:

            interrupt_learning_session(
                "STUDENT_PROFILE_UNAVAILABLE"
            )

            return jsonify(
                student=None,
                assignment=None
            )

        assignment = get_assignment(student_id)

        if (
            assignment is None
            or assignment.get("id") !=
            session.get(ASSIGNMENT_KEY)
        ):

            interrupt_learning_session(
                "ASSIGNMENT_UNAVAILABLE_OR_CHANGED"
            )

            return jsonify(
                student=None,
                assignment=None
            )

        performance_record = get_bound_performance_session(
            performance_session_id=session.get(
                PERFORMANCE_SESSION_KEY
            ),
            student_id=student_id,
            assignment_id=assignment["id"]
        )

        if (
            performance_record is None
            or performance_record["status"] !=
            SessionStatus.ACTIVE.value
        ):

            clear_learning_session()

            return jsonify(
                student=None,
                assignment=None
            )

        return jsonify(
            student=student_summary(profile),
            assignment=assignment
        )

    except sqlite3.Error as error:

        return performance_storage_error(error)


@learning_session_api.post("/api/learning-session")
def start_learning_session():

    data = request.get_json(silent=True)

    if not isinstance(data, dict):

        return jsonify(
            error="Geçersiz istek."
        ), 400

    student_id = data.get("student_id")

    if (
        not isinstance(student_id, str)
        or not student_id.strip()
    ):

        return jsonify(
            error="Öğrenci seçilmelidir."
        ), 400

    if session.get(SESSION_KEY):

        return jsonify(
            error="Önce mevcut oturumu sonlandırınız."
        ), 409

    profile = get_profile(student_id)

    if profile is None:

        return jsonify(
            error="Öğrenci bulunamadı."
        ), 404

    assignment = get_assignment(student_id)

    if assignment is None:

        return jsonify(
            error="Henüz etkinlik atanmadı."
        ), 409

    try:

        performance_record = start_performance_session(
            student_id=student_id,
            assignment=assignment
        )

    except (ValueError, TypeError, KeyError):

        current_app.logger.warning(
            "Assigned activity failed lifecycle validation."
        )

        return jsonify(
            error=(
                "Atanan etkinlik kullanılamıyor. "
                "Öğretmeninize danışınız."
            )
        ), 409

    except sqlite3.Error as error:

        return performance_storage_error(error)

    session[SESSION_KEY] = student_id

    session[ASSIGNMENT_KEY] = assignment["id"]

    session[PERFORMANCE_SESSION_KEY] = (
        performance_record["session_id"]
    )

    return jsonify(
        student=student_summary(profile),
        assignment=assignment
    )


@learning_session_api.delete("/api/learning-session")
def end_learning_session():

    student_id = session.get(SESSION_KEY)

    assignment_id = session.get(ASSIGNMENT_KEY)

    performance_session_id = session.get(
        PERFORMANCE_SESSION_KEY
    )

    try:

        finish_performance_session(
            performance_session_id=performance_session_id,
            student_id=student_id,
            assignment_id=assignment_id,
            status=SessionStatus.TERMINATED,
            reason="USER_ENDED_SESSION"
        )

    except sqlite3.Error as error:

        return performance_storage_error(error)

    if student_id and assignment_id:

        clear_assignment(
            student_id,
            assignment_id
        )

    clear_learning_session()

    return jsonify(
        student=None,
        assignment=None
    )


@learning_session_api.after_request
def disable_learning_session_cache(response):

    response.headers["Cache-Control"] = (
        "no-store, max-age=0"
    )

    return response
