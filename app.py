from visual_library.routes import visual_library_bp
from flask import Flask, render_template
from pathlib import Path

from profile_api import profile_api
from active_student_api import active_student_api

app = Flask(__name__)

# Oturum anahtarını kaynak kodundan ayrı tut.
key_file = Path(__file__).resolve().parent / ".flask_secret_key"
app.config["SECRET_KEY"] = key_file.read_text(encoding="utf-8").strip()

app.register_blueprint(visual_library_bp)
app.register_blueprint(profile_api)
app.register_blueprint(active_student_api)

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
    return render_template("student.html", achievements=ACHIEVEMENTS)


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
