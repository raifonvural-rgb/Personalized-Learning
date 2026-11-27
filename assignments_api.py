"""
Teacher-facing API for multiple ordered assignments.

Uses the existing teacher-side active student context.
"""

import sqlite3

from flask import (
    Blueprint,
    jsonify,
    request,
    session,
    current_app,
)

from performance_database import (
    database_transaction,
)

from profile_storage import get_profile

from assignment_repository import (
    list_student_assignments,
    create_assignment,
    set_assignment_enabled,
    reorder_pending_assignments,
    cancel_pending_assignment,
)

from activity_storage import get_activity


assignments_api = Blueprint(
    "assignments_api",
    __name__,
)


def get_selected_student():

    student_id = session.get("active_student_id")

    if not student_id:

        return None

    return get_profile(student_id)


def assignment_storage_error(error):

    current_app.logger.error(
        "Assignment storage operation failed: %s",
        error,
        exc_info=True,
    )

    return jsonify({
        "ok": False,
        "error": (
            "Atama bilgilerine şu anda erişilemiyor."
        ),
    }), 503


def build_assignment_summary(assignment):

    result = dict(assignment)

    activity = get_activity(
        assignment["activity_id"]
    )

    result["activity_available"] = False

    result["activity"] = None

    if (
        activity is not None
        and activity.get("student_id") ==
            assignment["student_id"]
    ):

        configuration = activity.get("config", {})

        result["activity_available"] = True

        result["activity"] = {
            "id": assignment["activity_id"],

            "status": activity.get("status"),

            "activity_type": configuration.get(
                "activity_type"
            ),

            "achievement_code": configuration.get(
                "achievement_code"
            ),

            "target_digit": configuration.get(
                "target_digit"
            ),

            "target_quantity": configuration.get(
                "target_quantity"
            ),
        }

    is_pending = assignment["status"] == "PENDING"

    result["allowed_operations"] = {
        "enable_disable": is_pending,
        "reorder": is_pending,
        "cancel": is_pending,
    }

    return result


@assignments_api.before_request
def require_assignment_schema():

    try:

        with database_transaction() as connection:

            record = connection.execute(
                '''
                SELECT value
                FROM schema_metadata
                WHERE key = 'schema_version'
                '''
            ).fetchone()

        if (
            record is None
            or record["value"] != "2"
        ):

            return jsonify({
                "ok": False,

                "error": (
                    "Çoklu etkinlik atama sistemi "
                    "henüz kullanıma açılmadı."
                ),
            }), 503

    except sqlite3.Error as error:

        return assignment_storage_error(error)


@assignments_api.get("/api/activity-assignments")
def read_assignments():

    profile = get_selected_student()

    if profile is None:

        return jsonify({
            "ok": False,
            "error": "Önce bir öğrenci seçiniz.",
        }), 400

    try:

        assignments = list_student_assignments(
            profile["id"]
        )

        summaries = [
            build_assignment_summary(assignment)
            for assignment in assignments
        ]

        return jsonify({
            "ok": True,

            "student": {
                "id": profile["id"],
                "name": profile["general"]["name"],
            },

            "assignments": summaries,
        })

    except sqlite3.Error as error:

        return assignment_storage_error(error)


@assignments_api.post("/api/activity-assignments")
def add_assignment():

    profile = get_selected_student()

    if profile is None:

        return jsonify({
            "ok": False,
            "error": "Önce bir öğrenci seçiniz.",
        }), 400

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):

        return jsonify({
            "ok": False,
            "error": "Geçersiz atama bilgileri.",
        }), 400

    activity_id = payload.get("activity_id")

    enabled = payload.get("enabled", True)

    if (
        not isinstance(activity_id, str)
        or not activity_id.strip()
    ):

        return jsonify({
            "ok": False,
            "error": "Geçerli bir etkinlik seçiniz.",
        }), 400

    if type(enabled) is not bool:

        return jsonify({
            "ok": False,
            "error": "Geçersiz etkinleştirme değeri.",
        }), 400

    try:

        assignment = create_assignment(
            student_id=profile["id"],
            activity_id=activity_id.strip(),
            enabled=enabled,
        )

        return jsonify({
            "ok": True,

            "assignment":
                build_assignment_summary(
                    assignment
                ),

            "message":
                "Etkinlik öğrenciye atandı.",
        }), 201

    except ValueError as error:

        current_app.logger.warning(
            "Assignment creation rejected: %s",
            error,
        )

        return jsonify({
            "ok": False,
            "error": (
                "Etkinlik atanamadı. "
                "Etkinliğin öğrenciye ait ve "
                "onaylanmış olduğunu kontrol ediniz."
            ),
        }), 409

    except sqlite3.Error as error:

        return assignment_storage_error(error)


@assignments_api.patch(
    "/api/activity-assignments/<assignment_id>/enabled"
)
def update_assignment_enabled(assignment_id):

    profile = get_selected_student()

    if profile is None:

        return jsonify({
            "ok": False,
            "error": "Önce bir öğrenci seçiniz.",
        }), 400

    payload = request.get_json(silent=True)

    if (
        not isinstance(payload, dict)
        or type(payload.get("enabled")) is not bool
    ):

        return jsonify({
            "ok": False,
            "error": "Geçersiz etkinleştirme değeri.",
        }), 400

    try:

        assignment = set_assignment_enabled(
            student_id=profile["id"],
            assignment_id=assignment_id,
            enabled=payload["enabled"],
        )

        message = (
            "Atama etkinleştirildi."
            if assignment["enabled"]
            else "Atama devre dışı bırakıldı."
        )

        return jsonify({
            "ok": True,

            "assignment":
                build_assignment_summary(
                    assignment
                ),

            "message": message,
        })

    except ValueError as error:

        current_app.logger.warning(
            "Assignment enablement rejected: %s",
            error,
        )

        return jsonify({
            "ok": False,
            "error": (
                "Atamanın durumu değiştirilemedi. "
                "Yalnızca bekleyen ve öğrenciye ait "
                "atamalar değiştirilebilir."
            ),
        }), 409

    except sqlite3.Error as error:

        return assignment_storage_error(error)


@assignments_api.put(
    "/api/activity-assignments/order"
)
def update_assignment_order():

    profile = get_selected_student()

    if profile is None:

        return jsonify({
            "ok": False,
            "error": "Önce bir öğrenci seçiniz.",
        }), 400

    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):

        return jsonify({
            "ok": False,
            "error": "Geçersiz sıralama bilgileri.",
        }), 400

    assignment_ids = payload.get("assignment_ids")

    if (
        not isinstance(assignment_ids, list)
        or any(
            not isinstance(item, str)
            or not item.strip()
            for item in assignment_ids
        )
    ):

        return jsonify({
            "ok": False,
            "error": "Geçersiz atama sıralaması.",
        }), 400

    assignment_ids = [
        item.strip()
        for item in assignment_ids
    ]

    if len(assignment_ids) != len(set(assignment_ids)):

        return jsonify({
            "ok": False,
            "error": (
                "Bir atama sıralamada birden "
                "fazla kez bulunamaz."
            ),
        }), 400

    try:

        reorder_pending_assignments(
            profile["id"],
            assignment_ids,
        )

        assignments = list_student_assignments(
            profile["id"]
        )

        return jsonify({
            "ok": True,

            "assignments": [
                build_assignment_summary(assignment)
                for assignment in assignments
            ],

            "message":
                "Etkinlik sıralaması güncellendi.",
        })

    except ValueError as error:

        current_app.logger.warning(
            "Assignment reordering rejected: %s",
            error,
        )

        return jsonify({
            "ok": False,
            "error": (
                "Etkinlik sıralaması güncellenemedi. "
                "Atama listesini yenileyip tekrar deneyiniz."
            ),
        }), 409

    except sqlite3.Error as error:

        return assignment_storage_error(error)


@assignments_api.delete(
    "/api/activity-assignments/<assignment_id>"
)
def cancel_assignment(assignment_id):

    profile = get_selected_student()

    if profile is None:

        return jsonify({
            "ok": False,
            "error": "Önce bir öğrenci seçiniz.",
        }), 400

    try:

        assignment = cancel_pending_assignment(
            student_id=profile["id"],
            assignment_id=assignment_id,
        )

        return jsonify({
            "ok": True,

            "assignment":
                build_assignment_summary(
                    assignment
                ),

            "message":
                "Etkinlik ataması iptal edildi.",
        })

    except ValueError as error:

        current_app.logger.warning(
            "Assignment cancellation rejected: %s",
            error,
        )

        return jsonify({
            "ok": False,
            "error": (
                "Atama iptal edilemedi. "
                "Yalnızca bekleyen ve öğrenciye ait "
                "atamalar iptal edilebilir."
            ),
        }), 409

    except sqlite3.Error as error:

        return assignment_storage_error(error)


@assignments_api.after_request
def disable_assignments_cache(response):

    response.headers["Cache-Control"] = (
        "no-store, max-age=0"
    )

    return response
