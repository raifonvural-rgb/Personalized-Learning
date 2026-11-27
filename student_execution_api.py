import sqlite3

from flask import (
    Blueprint,
    jsonify,
    request,
    current_app,
)

from performance_database import database_transaction

from student_execution_service import (
    retrieve_assignment_execution,
    submit_assignment_response,
)


student_execution_api = Blueprint(
    "student_execution_api",
    __name__
)


def execution_storage_error(error):

    current_app.logger.error(
        "Student execution storage failure: %s",
        error,
        exc_info=True
    )

    return jsonify({
        "ok": False,
        "error": (
            "Etkinlik bilgilerine şu anda erişilemiyor."
        ),
    }), 503


@student_execution_api.before_request
def require_execution_schema():

    try:

        with database_transaction() as connection:

            version = connection.execute(
                """
                SELECT value
                FROM schema_metadata
                WHERE key = 'schema_version'
                """
            ).fetchone()

            if (
                version is None
                or version["value"] != "2"
            ):

                return jsonify({
                    "ok": False,
                    "error": (
                        "Öğrenme sistemi henüz "
                        "kullanıma açılmadı."
                    ),
                }), 503

    except sqlite3.Error as error:

        return execution_storage_error(error)


@student_execution_api.get(
    "/api/student-execution/<assignment_id>"
)
def read_student_execution(assignment_id):

    try:

        result = retrieve_assignment_execution(
            assignment_id
        )

        return jsonify({
            "ok": True,
            **result,
        })

    except sqlite3.Error as error:

        return execution_storage_error(error)

    except ValueError as error:

        current_app.logger.warning(
            "Student execution request rejected: %s",
            error
        )

        return jsonify({
            "ok": False,
            "error": (
                "Geçerli etkinlik oturumu bulunamadı."
            ),
        }), 409

    except RuntimeError as error:

        current_app.logger.error(
            "Student execution consistency failure: %s",
            error,
            exc_info=True
        )

        return jsonify({
            "ok": False,
            "error": (
                "Etkinlik oturumu güvenli biçimde "
                "açılamadı. Öğretmeninize danışınız."
            ),
        }), 409


@student_execution_api.post(
    "/api/student-execution/<assignment_id>/response"
)
def submit_student_response(assignment_id):

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):

        return jsonify({
            "ok": False,
            "error": "Geçersiz cevap bilgisi.",
        }), 400

    required_identifiers = (
        "performance_session_id",
        "question_id",
        "request_id",
    )

    for field in required_identifiers:

        value = payload.get(field)

        if (
            not isinstance(value, str)
            or not value.strip()
        ):

            return jsonify({
                "ok": False,
                "error": "Eksik veya geçersiz oturum bilgisi.",
                "field": field,
            }), 400

    selected_position = payload.get(
        "selected_position"
    )

    if (
        isinstance(selected_position, bool)
        or not isinstance(selected_position, int)
        or selected_position < 0
    ):

        return jsonify({
            "ok": False,
            "error": "Geçersiz cevap seçimi.",
        }), 400

    try:

        result = submit_assignment_response(

            assignment_id=assignment_id,

            performance_session_id=payload[
                "performance_session_id"
            ],

            question_id=payload["question_id"],

            request_id=payload["request_id"],

            selected_position=selected_position,
        )

        return jsonify({
            "ok": True,
            **result,
        })

    except sqlite3.Error as error:

        return execution_storage_error(error)

    except ValueError as error:

        current_app.logger.warning(
            "Student response rejected: %s",
            error
        )

        return jsonify({
            "ok": False,
            "error": (
                "Cevap mevcut etkinlik durumuyla "
                "uyumlu değil. Etkinliği yenileyiniz."
            ),
        }), 409

    except RuntimeError as error:

        current_app.logger.error(
            "Student response consistency failure: %s",
            error,
            exc_info=True
        )

        return jsonify({
            "ok": False,
            "error": (
                "Cevap güvenli biçimde kaydedilemedi. "
                "Öğretmeninize danışınız."
            ),
        }), 409


@student_execution_api.after_request
def disable_execution_response_caching(response):

    response.headers["Cache-Control"] = (
        "no-store, max-age=0"
    )

    return response


from student_execution_service import (
    repeat_assignment_question,
)


@student_execution_api.post(
    "/api/student-execution/<assignment_id>/repeat"
)
def repeat_student_question(assignment_id):

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify(
            ok=False,
            error="Geçersiz tekrar isteği."
        ), 400

    for field in (
        "performance_session_id",
        "previous_question_id",
    ):
        value = payload.get(field)

        if not isinstance(value, str) or not value.strip():
            return jsonify(
                ok=False,
                error="Eksik oturum veya soru bilgisi."
            ), 400

    try:

        result = repeat_assignment_question(
            assignment_id=assignment_id,
            performance_session_id=payload[
                "performance_session_id"
            ],
            previous_question_id=payload[
                "previous_question_id"
            ],
        )

        return jsonify(ok=True, **result)

    except sqlite3.Error:

        return jsonify(
            ok=False,
            error="Etkinlik şu anda tekrarlanamıyor."
        ), 503

    except (ValueError, RuntimeError):

        return jsonify(
            ok=False,
            error="Etkinlik tekrarı doğrulanamadı."
        ), 409


from student_execution_service import (
    complete_student_assignment,
)


@student_execution_api.post(
    "/api/student-execution/<assignment_id>/complete"
)
def complete_student_activity(assignment_id):

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify(
            ok=False,
            error="Geçersiz tamamlama isteği."
        ), 400

    performance_session_id = payload.get(
        "performance_session_id"
    )

    if (
        not isinstance(performance_session_id, str)
        or not performance_session_id.strip()
    ):
        return jsonify(
            ok=False,
            error="Geçersiz öğrenme oturumu."
        ), 400

    try:

        result = complete_student_assignment(
            assignment_id=assignment_id,
            performance_session_id=performance_session_id,
        )

        return jsonify(ok=True, **result)

    except sqlite3.Error:

        return jsonify(
            ok=False,
            error="Etkinlik şu anda tamamlanamıyor."
        ), 503

    except (ValueError, RuntimeError):

        return jsonify(
            ok=False,
            error="Etkinliğin tamamlandığı doğrulanamadı."
        ), 409
