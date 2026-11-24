"""
Görsel Kütüphanesi Flask Blueprint.

Üç parametrik SVG nesnesi:
- Kurşun kalem
- Basketbol topu
- Futbol topu
"""

from flask import (
    Blueprint,
    request,
    abort,
    render_template,
    Response,
    url_for,
)

from .renderers.pencil import draw_pencil
from .renderers.basketball import draw_basketball
from .renderers.soccer_ball import draw_soccer_ball


visual_library_bp = Blueprint(
    "visual_library",
    __name__,
)


OBJECTS = {
    "pencil": {
        "name": "Kurşun Kalem",
        "description": (
            "Silgili ve ucu açılmış kurşun kalem. "
            "Gövde, silgi ve uç renkleri değiştirilebilir."
        ),
        "renderer": draw_pencil,
    },
    "basketball": {
        "name": "Basketbol Topu",
        "description": (
            "Çizgileri ve renkleri değiştirilebilen "
            "parametrik basketbol topu."
        ),
        "renderer": draw_basketball,
    },
    "soccer_ball": {
        "name": "Futbol Topu",
        "description": (
            "Panel renkleri ve çizgileri değiştirilebilen "
            "parametrik futbol topu."
        ),
        "renderer": draw_soccer_ball,
    },
}


@visual_library_bp.route("/visual-library")
def library_page():

    items = []

    for object_id, item in OBJECTS.items():
        items.append({
            "id": object_id,
            "name": item["name"],
            "description": item["description"],
            "image_url": url_for(
                "visual_library.svg_image",
                object_id=object_id,
            ),
        })

    return render_template(
        "visual_library.html",
        items=items,
    )


@visual_library_bp.route(
    "/visual-library/svg/<object_id>.svg"
)
def svg_image(object_id):

    item = OBJECTS.get(object_id)

    if item is None:
        abort(404)

    svg = item["renderer"]()

    return Response(
        svg,
        mimetype="image/svg+xml",
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": (
                "default-src 'none'; "
                "style-src 'unsafe-inline'; "
                "sandbox"
            ),
        },
    )


# Öğretmenin değiştirebileceği renk parametreleri.
ALLOWED_COLORS = {
    "pencil": {
        "body_color",
        "eraser_color",
        "wood_color",
        "graphite_color",
        "metal_color",
        "outline_color",
    },
    "basketball": {
        "ball_color",
        "line_color",
    },
    "soccer_ball": {
        "panel_color",
        "background_color",
        "line_color",
    },
}


@visual_library_bp.route(
    "/visual-library/preview/<object_id>.svg"
)
def svg_preview(object_id):
    """İzin verilen renklerle SVG'yi yeniden üret."""

    item = OBJECTS.get(object_id)

    if item is None:
        abort(404)

    allowed = ALLOWED_COLORS[object_id]
    properties = {}

    for key in request.args:
        if key not in allowed:
            abort(400, description="Desteklenmeyen parametre")

        values = request.args.getlist(key)

        if len(values) != 1:
            abort(400, description="Tekrarlanan parametre")

        value = values[0]

        if (
            len(value) != 7
            or not value.startswith("#")
            or any(
                char not in "0123456789abcdefABCDEF"
                for char in value[1:]
            )
        ):
            abort(400, description="Geçersiz renk")

        properties[key] = value

    svg = item["renderer"](**properties)

    return Response(
        svg,
        mimetype="image/svg+xml",
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": (
                "default-src 'none'; "
                "style-src 'unsafe-inline'; "
                "sandbox"
            ),
        },
    )


@visual_library_bp.post("/visual-library/check-colors")
def check_object_colors():
    """Öğrenci profiline göre SVG renklerini ön denetimden geçir."""

    import inspect
    import re
    from flask import jsonify
    from profile_storage import get_profile
    from .color_safety import COLOR_NAMES, check_avoided_colors

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(error="Geçerli JSON nesnesi gerekli"), 400

    student_id = data.get("student_id")
    object_id = data.get("object_id")
    overrides = data.get("colors", {})

    if not isinstance(student_id, str) or not student_id.strip():
        return jsonify(error="Öğrenci seçilmedi"), 400

    if not isinstance(object_id, str) or object_id not in OBJECTS:
        return jsonify(error="Geçersiz nesne"), 400

    if not isinstance(overrides, dict):
        return jsonify(error="Renkler JSON nesnesi olmalı"), 400

    allowed = ALLOWED_COLORS[object_id]

    for key, value in overrides.items():
        if key not in allowed:
            return jsonify(error="Desteklenmeyen renk parametresi"), 400

        if not isinstance(value, str) or not re.fullmatch(
            r"#[0-9a-fA-F]{6}", value
        ):
            return jsonify(error="Geçersiz HEX renk değeri"), 400

    try:
        profile = get_profile(student_id)
    except (KeyError, ValueError, FileNotFoundError):
        profile = None

    if not isinstance(profile, dict):
        return jsonify(error="Öğrenci profili bulunamadı"), 404

    visual = profile.get("visual") or {}
    if not isinstance(visual, dict):
        return jsonify(error="Görsel profil geçersiz"), 422

    avoided = visual.get("avoided_colors", [])

    if not isinstance(avoided, list):
        return jsonify(error="Kaçınılan renkler geçersiz"), 422

    renderer = OBJECTS[object_id]["renderer"]
    signature = inspect.signature(renderer)

    colors = {}

    for parameter in allowed:
        definition = signature.parameters.get(parameter)

        if definition is None or not isinstance(definition.default, str):
            return jsonify(error="SVG renk tanımı eksik"), 500

        colors[parameter] = overrides.get(
            parameter, definition.default
        )

    results = check_avoided_colors(colors, avoided)

    unknown_colors = [
        name for name in avoided
        if not isinstance(name, str) or name not in COLOR_NAMES
    ]

    warnings = sum(
        result["status"] == "warning" for result in results
    )
    reviews = sum(
        result["status"] == "review" for result in results
    )

    if unknown_colors:
        reviews += len(unknown_colors)

    # Serbest metin gereksinimleri otomatik doğrulanmış sayılmaz.
    additional_review = bool(
        visual.get("other") or profile.get("custom_requirements")
    )

    if additional_review:
        reviews += 1

    if warnings:
        overall = "warning"
    elif reviews:
        overall = "review"
    else:
        overall = "ok"

    return jsonify(
        student_id=student_id,
        object_id=object_id,
        overall_status=overall,
        colors=results,
        warning_count=warnings,
        review_count=reviews,
        unknown_avoided_colors=unknown_colors,
        additional_requirements_need_review=additional_review,
        teacher_approval_required=True,
        message=(
            "Bu sonuç yalnızca renk ön denetimidir. "
            "Materyalin son değerlendirmesi öğretmene aittir."
        ),
    )


# Step 39A.3 — Photographic image library API

@visual_library_bp.post("/visual-library/upload")
def upload_photo():
    from flask import jsonify
    from .photo_storage import prepare_upload

    try:
        result = prepare_upload(request.files.get("image"))
        return jsonify(ok=True, **result)
    except ValueError as exc:
        return jsonify(ok=False, error=str(exc)), 400


# Step 39C.11 — AI image generation API

@visual_library_bp.post("/visual-library/generate")
def generate_photo():
    import io
    from flask import jsonify
    from .image_generator import (
        generate_image,
        ImageGenerationError,
    )
    from .photo_storage import prepare_upload

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(
            ok=False,
            error="Geçersiz istek."
        ), 400

    description = data.get("description")

    try:
        generated = generate_image(description)

        result = prepare_upload(
            io.BytesIO(generated["content"]),
            metadata=generated["metadata"],
        )

        return jsonify(ok=True, **result)

    except ValueError as exc:
        return jsonify(ok=False, error=str(exc)), 400

    except ImageGenerationError as exc:
        return jsonify(ok=False, error=str(exc)), 502


@visual_library_bp.get("/visual-library/pending/<token>")
def pending_photo(token):
    import re
    from flask import send_file
    from .photo_storage import PENDING

    if not re.fullmatch(r"[0-9a-f]{32}", token):
        abort(404)

    path = PENDING / f"{token}.png"
    if not path.is_file():
        abort(404)

    return send_file(path, mimetype="image/png", max_age=0)


# Step 39C.12 — Reject a pending image

@visual_library_bp.post("/visual-library/reject")
def reject_photo():
    import re
    from flask import jsonify
    from .photo_storage import PENDING

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify(
            ok=False,
            error="Geçersiz istek."
        ), 400

    token = data.get("token")

    if not isinstance(token, str) or not re.fullmatch(
        r"[0-9a-f]{32}", token
    ):
        return jsonify(
            ok=False,
            error="Geçersiz görsel kimliği."
        ), 400

    image_path = PENDING / f"{token}.png"
    metadata_path = PENDING / f"{token}.json"

    image_path.unlink(missing_ok=True)
    metadata_path.unlink(missing_ok=True)

    return jsonify(
        ok=True,
        message="Görsel reddedildi."
    )


@visual_library_bp.post("/visual-library/approve")
def approve_photo():
    from flask import jsonify
    from .photo_storage import approve_upload

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(ok=False, error="Geçersiz istek."), 400

    try:
        asset = approve_upload(
            data.get("token"),
            data.get("name"),
        )
        return jsonify(ok=True, asset=asset)
    except ValueError as exc:
        return jsonify(ok=False, error=str(exc)), 400


@visual_library_bp.get("/visual-library/photos")
def approved_photos():
    from flask import jsonify
    from .photo_storage import list_approved_images

    assets = list_approved_images()

    for asset in assets:
        asset["image_url"] = (
            "/visual-library/photo/" + asset["id"]
        )

    return jsonify(ok=True, assets=assets)


@visual_library_bp.get("/visual-library/photo/<asset_id>")
def approved_photo_file(asset_id):
    import re
    from flask import send_file
    from .photo_storage import UPLOADS, list_approved_images

    if not re.fullmatch(r"[0-9a-f]{32}", asset_id):
        abort(404)

    asset = next(
        (a for a in list_approved_images() if a["id"] == asset_id),
        None,
    )

    if asset is None:
        abort(404)

    path = UPLOADS / asset["filename"]

    if not path.is_file():
        abort(404)

    return send_file(path, mimetype="image/png")
