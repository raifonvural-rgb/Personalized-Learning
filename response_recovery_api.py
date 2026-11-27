"""Read-only student response recovery API."""

import sqlite3

from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
)

from performance_database import database_transaction

from student_learning_context import get_learning_context

from response_recovery_service import inspect_response_recording


response_recovery_api = Blueprint(
    "response_recovery_api",
    __name__,
)


@response_recovery_api.after_request
def prevent_response_caching(response):

    response.headers["Cache-Control"] = "no-store"

    return response


@response_recovery_api.route(
    "/api/student-execution/<assignment_id>/response-status",
    methods=["POST"],
)
def inspect_student_response(assignment_id):

    context = get_learning_context()

    student_id = context.get("student_id")

    if not isinstance(student_id, str) or not student_id.strip():

        return jsonify(
            ok=False,
            error="Öğrenme oturumu bulunamadı.",
        ), 403

    if context.get("assignment_id") != assignment_id:

        return jsonify(
            ok=False,
            error="Etkinlik ataması doğrulanamadı.",
        ), 403

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):

        return jsonify(
            ok=False,
            error="Geçersiz cevap kontrol isteği.",
        ), 400

    required_identifiers = (
        "performance_session_id",
        "question_id",
        "request_id",
    )

    for field in required_identifiers:

        value = payload.get(field)

        if not isinstance(value, str) or not value.strip():

            return jsonify(
                ok=False,
                error="Eksik veya geçersiz cevap bilgisi.",
            ), 400

    selected_position = payload.get(
        "selected_position"
    )

    if (
        type(selected_position) is not int
        or selected_position < 0
    ):

        return jsonify(
            ok=False,
            error="Geçersiz cevap seçimi.",
        ), 400

    try:

        with database_transaction() as connection:

            version = connection.execute(
                """
                SELECT value
                FROM schema_metadata
                WHERE key = 'schema_version'
                """
            ).fetchone()

            if version is None or version["value"] != "2":

                return jsonify(
                    ok=False,
                    error="Cevap kontrol sistemi hazır değil.",
                ), 503

            result = inspect_response_recording(
                connection=connection,
                student_id=student_id,
                assignment_id=assignment_id,
                performance_session_id=payload[
                    "performance_session_id"
                ],
                question_id=payload["question_id"],
                request_id=payload["request_id"],
                selected_position=selected_position,
            )

        return jsonify(
            ok=True,
            **result,
        )

    except ValueError:

        return jsonify(
            ok=False,
            error="Cevap kaydı ilişkisi doğrulanamadı.",
        ), 403

    except (sqlite3.Error, RuntimeError):

        current_app.logger.exception(
            "Student response recording inspection failed."
        )

        return jsonify(
            ok=False,
            error="Cevap kaydı şu anda kontrol edilemiyor.",
        ), 503
