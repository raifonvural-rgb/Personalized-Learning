import sqlite3

from flask import (
    Blueprint,
    jsonify,
    request,
    current_app,
)

from performance_database import database_transaction

from student_sequence_service import (
    initialize_student_sequence,
    retrieve_student_sequence,
    terminate_student_sequence,
)

from student_learning_context import (
    get_learning_context,
    clear_learning_context,
)


student_sequence_api = Blueprint(
    "student_sequence_api",
    __name__
)


def sequence_storage_error(error):

    current_app.logger.error(
        "Student sequence storage error: %s",
        error,
        exc_info=True
    )

    return jsonify({
        "ok": False,
        "error": (
            "Öğrenme oturumu bilgilerine "
            "şu anda erişilemiyor."
        ),
    }), 503


@student_sequence_api.before_request
def require_sequence_schema():

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
                        "Çoklu etkinlik öğrenme sistemi "
                        "henüz kullanıma açılmadı."
                    ),
                }), 503

    except sqlite3.Error as error:

        return sequence_storage_error(error)


@student_sequence_api.get("/api/student-sequence")
def read_student_sequence():

    try:

        result = retrieve_student_sequence()

        return jsonify({
            "ok": True,
            **result,
        })

    except sqlite3.Error as error:

        return sequence_storage_error(error)

    except (ValueError, RuntimeError) as error:

        current_app.logger.error(
            "Student sequence consistency error: %s",
            error,
            exc_info=True
        )

        return jsonify({
            "ok": False,
            "error": (
                "Öğrenme oturumu doğrulanamadı. "
                "Öğretmeninize danışınız."
            ),
        }), 409


@student_sequence_api.post("/api/student-sequence")
def start_student_sequence():

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):

        return jsonify({
            "ok": False,
            "error": "Geçersiz öğrenci bilgisi.",
        }), 400

    student_id = payload.get("student_id")

    if (
        not isinstance(student_id, str)
        or not student_id.strip()
    ):

        return jsonify({
            "ok": False,
            "error": "Lütfen bir öğrenci seçiniz.",
        }), 400

    student_id = student_id.strip()

    context = get_learning_context()

    if (
        context["student_id"] is not None
        and context["student_id"] != student_id
    ):

        return jsonify({
            "ok": False,
            "error": (
                "Başka bir öğrencinin öğrenme "
                "oturumu açık."
            ),
        }), 409

    try:

        existing = retrieve_student_sequence()

        existing_status = existing["sequence_status"]

        if existing_status == "ACTIVE":

            return jsonify({
                "ok": True,
                **existing,
                "resumed": True,
            })

        if existing_status in (
            "STALE_CONTEXT",
            "ASSIGNMENT_COMPLETED",
            "BETWEEN_ASSIGNMENTS",
        ):

            return jsonify({
                "ok": False,
                "sequence_status": existing_status,
                "error": (
                    "Mevcut öğrenme oturumu için "
                    "devam veya kurtarma işlemi gerekli."
                ),
            }), 409

        result = initialize_student_sequence(
            student_id
        )

        return jsonify({
            "ok": True,
            **result,
        })

    except sqlite3.Error as error:

        return sequence_storage_error(error)

    except (ValueError, RuntimeError) as error:

        current_app.logger.warning(
            "Student sequence initialization rejected: %s",
            error
        )

        return jsonify({
            "ok": False,
            "error": (
                "Öğrenme oturumu başlatılamadı. "
                "Öğretmeninize danışınız."
            ),
        }), 409


@student_sequence_api.post(
    "/api/student-sequence/recover"
)
def recover_student_sequence():

    try:

        existing = retrieve_student_sequence()

        sequence_status = existing[
            "sequence_status"
        ]

        if sequence_status == "NO_CONTEXT":

            return jsonify({
                "ok": True,
                "sequence_status": "NO_CONTEXT",
                "recovered": False,
                "student": None,
                "assignment": None,
                "execution": None,
            })

        if sequence_status != "STALE_CONTEXT":

            return jsonify({
                "ok": False,
                "sequence_status": sequence_status,
                "error": (
                    "Geçerli öğrenme oturumu "
                    "kurtarma işlemiyle kapatılamaz."
                ),
            }), 409

        clear_learning_context()

        return jsonify({
            "ok": True,
            "sequence_status": "NO_CONTEXT",
            "recovered": True,
            "student": None,
            "assignment": None,
            "execution": None,
            "message": (
                "Eski oturum bilgileri temizlendi. "
                "Öğrenciyi yeniden seçebilirsiniz."
            ),
        })

    except sqlite3.Error as error:

        return sequence_storage_error(error)

    except (ValueError, RuntimeError) as error:

        current_app.logger.error(
            "Student sequence recovery rejected: %s",
            error,
            exc_info=True
        )

        return jsonify({
            "ok": False,
            "error": (
                "Öğrenme oturumu güvenli biçimde "
                "kurtarılamadı. "
                "Öğretmeninize danışınız."
            ),
        }), 409


@student_sequence_api.delete("/api/student-sequence")
def end_student_sequence():

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):

        return jsonify(
            ok=False,
            error="Geçersiz oturum bilgisi."
        ), 400

    context = get_learning_context()

    for field in (
        "student_id",
        "assignment_id",
        "performance_session_id",
    ):

        if field not in payload or payload[field] != context[field]:

            return jsonify(
                ok=False,
                error="Öğrenme oturumu değişmiş."
            ), 409

    try:

        result = terminate_student_sequence()

        return jsonify({
            "ok": True,
            **result,
            "message": (
                "Öğrenme oturumu sonlandırıldı."
                if result["terminated"]
                else "Açık öğrenme oturumu bulunmuyor."
            ),
        })

    except sqlite3.Error as error:

        return sequence_storage_error(error)

    except (ValueError, RuntimeError) as error:

        current_app.logger.warning(
            "Student sequence termination rejected: %s",
            error,
            exc_info=True
        )

        return jsonify({
            "ok": False,
            "error": (
                "Öğrenme oturumu güvenli biçimde "
                "sonlandırılamadı. "
                "Öğretmeninize danışınız."
            ),
        }), 409


@student_sequence_api.after_request
def disable_sequence_cache(response):

    response.headers["Cache-Control"] = (
        "no-store, max-age=0"
    )

    return response


from student_sequence_service import advance_student_sequence


@student_sequence_api.post("/api/student-sequence/next")
def advance_student_sequence_endpoint():

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):

        return jsonify(
            ok=False,
            error="Geçersiz etkinlik bilgisi."
        ), 400

    for field in (
        "assignment_id",
        "performance_session_id",
    ):

        value = payload.get(field)

        if not isinstance(value, str) or not value.strip():

            return jsonify(
                ok=False,
                error="Eksik etkinlik veya oturum bilgisi."
            ), 400

    try:

        result = advance_student_sequence(
            assignment_id=payload["assignment_id"],
            performance_session_id=payload[
                "performance_session_id"
            ],
        )

        return jsonify(ok=True, **result)

    except sqlite3.Error as error:

        return sequence_storage_error(error)

    except (ValueError, RuntimeError) as error:

        current_app.logger.warning(
            "Student sequence advancement rejected: %s",
            error
        )

        return jsonify(
            ok=False,
            error="Sonraki etkinlik başlatılamadı."
        ), 409
