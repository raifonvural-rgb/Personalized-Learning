from visual_library.routes import visual_library_bp
from flask import Flask, render_template
from pathlib import Path

from profile_api import profile_api
from active_student_api import active_student_api
from learning_session_api import (
    learning_session_api,
    interrupt_learning_session
)

import sqlite3

from performance_database import (
    initialize_database,
    ensure_active_assignment_uniqueness
)
from performance_models import SessionStatus

from performance_lifecycle import (
    PERFORMANCE_SESSION_KEY,
    get_bound_performance_session
)
from assignment_api import assignment_api

app = Flask(__name__)

initialize_database()
ensure_active_assignment_uniqueness()

# Oturum anahtarını kaynak kodundan ayrı tut.
key_file = Path(__file__).resolve().parent / ".flask_secret_key"
app.config["SECRET_KEY"] = key_file.read_text(encoding="utf-8").strip()

app.register_blueprint(visual_library_bp)
app.register_blueprint(profile_api)
app.register_blueprint(active_student_api)
app.register_blueprint(learning_session_api)
app.register_blueprint(assignment_api)

ACHIEVEMENTS = [
    {"code": "MAT1.1.1", "title": "Rakamları gösterir", "type": "select"},
    {"code": "MAT1.1.2", "title": "Gösterilen rakamı söyler", "type": "speak"},
    {"code": "MAT1.1.3", "title": "İstenen rakamı yazar", "type": "write"},
    {"code": "MAT1.1.4", "title": "1'den 200'e kadar sayıları gösterir", "type": "select"},
    {"code": "MAT1.1.5", "title": "1'den 200'e kadar sayıları söyler", "type": "speak"},
    {"code": "MAT1.1.6", "title": "1'den 200'e kadar sayıları yazar", "type": "write"},
]

@app.route("/")
def teacher():
    return render_template("teacher.html", achievements=ACHIEVEMENTS)

@app.route("/achievements")
def achievements():
    from flask import session
    from profile_storage import get_profile

    student_id = session.get("active_student_id")
    active_student = None

    if student_id:
        profile = get_profile(student_id)

        if profile:
            active_student = {
                "id": profile["id"],
                "name": profile["general"]["name"]
            }
        else:
            session.pop("active_student_id", None)

    return render_template(
        "achievements.html",
        achievements=ACHIEVEMENTS,
        active_student=active_student
    )

@app.route("/student")
def student():
    from flask import make_response

    response = make_response(
        render_template("student_dashboard.html")
    )
    response.headers["Cache-Control"] = "no-store, max-age=0"

    return response


@app.route("/student/preview")
def student_preview():
    from flask import request, redirect, url_for, session, make_response
    from profile_storage import get_profile

    student_id = session.get("active_student_id")

    if not student_id or not get_profile(student_id):
        return redirect(url_for("teacher"))

    draft_preview = request.args.get("preview") == "1"
    saved_preview = bool(request.args.get("activity_id"))

    if draft_preview == saved_preview:
        return redirect(url_for("activity_designer"))

    response = make_response(
        render_template(
            "student.html",
            achievements=ACHIEVEMENTS
        )
    )

    response.headers["Cache-Control"] = "no-store, max-age=0"

    return response


def get_assigned_learning_activity(activity_id):
    from flask import session
    from profile_storage import get_profile
    from assignment_storage import get_assignment
    from activity_storage import get_activity
    from activity_integrity import validate_activity_draft_integrity

    student_id = session.get("learning_student_id")
    assignment_id = session.get("learning_assignment_id")

    if not student_id or not assignment_id:
        return None

    if get_profile(student_id) is None:
        return None

    assignment = get_assignment(student_id)

    if not assignment:
        return None

    if assignment.get("id") != assignment_id:
        return None

    if assignment.get("activity_id") != activity_id:
        return None

    performance_record = get_bound_performance_session(
        performance_session_id=session.get(
            PERFORMANCE_SESSION_KEY
        ),
        student_id=student_id,
        assignment_id=assignment_id
    )

    if performance_record is None:
        return None

    if performance_record["status"] != SessionStatus.ACTIVE.value:
        return None

    if performance_record["activity_id"] != activity_id:
        return None

    activity = get_activity(activity_id)

    if not activity:
        return None

    if activity.get("student_id") != student_id:
        return None

    if activity.get("status") != "approved":
        return None

    try:
        validate_activity_draft_integrity(activity["config"])
    except (ValueError, TypeError, KeyError):
        return None

    snapshot = performance_record["activity_snapshot"]

    if snapshot.get("configuration") != activity.get("config"):
        return None

    return activity


@app.route("/student/activity/<activity_id>")
def student_assigned_activity(activity_id):
    from flask import redirect, url_for, make_response, session

    from assignment_storage import get_assignment

    try:

        current_student = session.get("learning_student_id")

        assignment = (
            get_assignment(current_student)
            if current_student else None
        )

        # An old browser tab must not terminate a newer
        # valid learning session merely by opening an old URL.
        if (
            assignment
            and assignment.get("id") ==
                session.get("learning_assignment_id")
            and assignment.get("activity_id") != activity_id
        ):
            return redirect(url_for("student"))

        activity = get_assigned_learning_activity(activity_id)

        if activity is None:

            interrupt_learning_session(
                "ASSIGNED_ACTIVITY_UNAVAILABLE_OR_INVALID"
            )

            return redirect(url_for("student"))

    except sqlite3.Error:

        app.logger.exception(
            "Performance session verification failed."
        )

        response = make_response(
            "Öğrenme kaydı işlenemedi. "
            "Lütfen tekrar deneyiniz.",
            503
        )

        response.headers["Cache-Control"] = (
            "no-store, max-age=0"
        )

        return response

    response = make_response(
        render_template(
            "student.html",
            achievements=ACHIEVEMENTS,
            learning_mode=True,
            learning_activity_id=activity_id
        )
    )

    response.headers["Cache-Control"] = "no-store, max-age=0"

    return response


@app.route("/api/learning-activity/<activity_id>")
def learning_activity_api(activity_id):
    from flask import jsonify, make_response

    try:

        activity = get_assigned_learning_activity(activity_id)

    except sqlite3.Error:

        app.logger.exception(
            "Performance session verification failed."
        )

        response = make_response(
            jsonify(
                ok=False,
                error="Öğrenme kaydı işlenemedi."
            ),
            503
        )

        response.headers["Cache-Control"] = (
            "no-store, max-age=0"
        )

        return response

    if activity is None:
        response = make_response(
            jsonify(
                ok=False,
                error="Etkinlik kullanılamıyor. Öğretmeninize danışınız."
            ),
            403
        )
    else:
        response = make_response(
            jsonify(ok=True, activity=activity)
        )

    response.headers["Cache-Control"] = "no-store, max-age=0"

    return response


@app.route("/activity-designer")
def activity_designer():
    from flask import session, redirect, url_for
    from profile_storage import get_profile
    from activity_layouts import FIND_DIGIT_LAYOUTS
    from visual_library.routes import OBJECTS
    from visual_library.photo_storage import list_approved_images

    student_id = session.get("active_student_id")

    if not student_id:
        return redirect(url_for("teacher"))

    profile = get_profile(student_id)

    if not profile:
        session.pop("active_student_id", None)
        return redirect(url_for("teacher"))

    active_student = {
        "id": profile["id"],
        "name": profile["general"]["name"],
    }

    return render_template(
        "activity_designer.html",
        active_student=active_student,
        layouts=FIND_DIGIT_LAYOUTS,
        visual_objects={
            **{
                object_id: {
                    "name": item["name"] + " (SVG)",
                    "image_url": url_for(
                        "visual_library.svg_image",
                        object_id=object_id,
                    ),
                }
                for object_id, item in OBJECTS.items()
            },
            **{
                "photo:" + asset["id"]: {
                    "name": asset["name"] + " (Fotoğraf)",
                    "image_url": url_for(
                        "visual_library.approved_photo_file",
                        asset_id=asset["id"],
                    ),
                }
                for asset in list_approved_images()
            },
        },
        achievement_code="MAT1.1.1",
    )



@app.route("/api/activity-draft", methods=["POST"])
def activity_draft_api():
    from flask import session, request, jsonify
    from profile_storage import get_profile
    from activity_request import build_draft_from_request

    student_id = session.get("active_student_id")

    if not student_id or not get_profile(student_id):
        return jsonify({
            "ok": False,
            "error": "Aktif öğrenci seçilmelidir."
        }), 403

    if not request.is_json:
        return jsonify({
            "ok": False,
            "error": "JSON verisi bekleniyor."
        }), 415

    data = request.get_json(silent=True)

    try:
        draft = build_draft_from_request(data)
    except (ValueError, TypeError) as exc:
        return jsonify({
            "ok": False,
            "error": str(exc)
        }), 400

    return jsonify({
        "ok": True,
        "draft": draft
    })



@app.route("/api/student-activities", methods=["GET"])
def student_activities_api():
    from flask import session, jsonify
    from activity_storage import list_student_activities

    student_id = session.get("active_student_id")
    if not student_id:
        return jsonify(ok=False, error="Aktif öğrenci yok."), 403

    return jsonify(
        ok=True,
        activities=list_student_activities(student_id)
    )


@app.route("/api/student-activities", methods=["POST"])
def save_student_activity_api():
    from flask import session, request, jsonify
    from activity_storage import save_activity_draft
    from profile_storage import get_profile

    student_id = session.get("active_student_id")
    if not student_id or not get_profile(student_id):
        return jsonify(ok=False, error="Aktif öğrenci yok."), 403

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(ok=False, error="Geçersiz JSON."), 400

    try:
        activity = save_activity_draft(student_id, data.get("draft"))
        return jsonify(ok=True, activity=activity), 201
    except (ValueError, TypeError, KeyError) as exc:
        return jsonify(ok=False, error=str(exc)), 400


@app.route("/api/student-activities/<activity_id>/validate", methods=["POST"])
def validate_student_activity_api(activity_id):
    from flask import session, jsonify
    from activity_storage import get_activity, validate_saved_activity

    activity = get_activity(activity_id)
    if not activity or activity.get("student_id") != session.get("active_student_id"):
        return jsonify(ok=False, error="Etkinlik bulunamadı."), 404

    try:
        updated = validate_saved_activity(activity_id)
        return jsonify(ok=True, activity=updated)
    except (ValueError, TypeError, KeyError) as exc:
        return jsonify(ok=False, error=str(exc)), 400


@app.route("/api/student-activities/<activity_id>/approve", methods=["POST"])
def approve_student_activity_api(activity_id):
    from flask import session, request, jsonify
    from activity_storage import get_activity, approve_saved_activity

    activity = get_activity(activity_id)
    if not activity or activity.get("student_id") != session.get("active_student_id"):
        return jsonify(ok=False, error="Etkinlik bulunamadı."), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(ok=False, error="Geçersiz JSON."), 400

    try:
        updated = approve_saved_activity(
            activity_id,
            acknowledge_issues=data.get("acknowledge_issues", False)
        )
        return jsonify(ok=True, activity=updated)
    except (ValueError, TypeError, KeyError) as exc:
        return jsonify(ok=False, error=str(exc)), 400


@app.route("/api/student-activities/<activity_id>", methods=["GET"])
def open_student_activity_api(activity_id):
    from flask import session, jsonify
    from activity_storage import get_activity

    activity = get_activity(activity_id)
    if not activity or activity.get("student_id") != session.get("active_student_id"):
        return jsonify(ok=False, error="Etkinlik bulunamadı."), 404

    if activity.get("status") != "approved":
        return jsonify(ok=False, error="Etkinlik henüz onaylanmadı."), 403

    from activity_integrity import validate_activity_draft_integrity

    try:
        validate_activity_draft_integrity(activity["config"])
    except (ValueError, TypeError, KeyError):
        return jsonify(
            ok=False,
            error=(
                "Etkinlik veya görsel nesne artık geçerli değil. "
                "Öğretmen incelemesi gereklidir."
            )
        ), 409

    return jsonify(ok=True, activity=activity)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=6000, debug=True)
