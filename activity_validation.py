"""
Öğretmen kontrollü etkinlikler için öğrenciye özgü ön doğrulama.

Bu modül kayıt oluşturmaz, etkinlik onaylamaz.
Belirsiz ve denetlenemeyen gereksinimler öğretmen incelemesine yönlendirilir.
"""

import inspect

from activity_builder import build_find_digit_draft
from activity_models import ActivityConfig
from visual_library.routes import OBJECTS, ALLOWED_COLORS
from visual_library.color_safety import (
    COLOR_NAMES,
    check_avoided_colors,
)


def validate_activity_for_student(draft, profile):
    if not isinstance(draft, dict) or not isinstance(profile, dict):
        raise ValueError("Etkinlik ve öğrenci profili gerekli")

    config = ActivityConfig(
        achievement_code=draft.get("achievement_code"),
        target_digit=draft.get("target_digit"),
        activity_type=draft.get("activity_type"),
        visual_id=draft.get("visual_id"),
        audio_enabled=draft.get("audio_enabled"),
        celebration_enabled=draft.get("celebration_enabled"),
        quantity_animation_enabled=draft.get("quantity_animation_enabled", False),
        settings={"layout_id": draft.get("layout_id")},
    )

    rebuilt = build_find_digit_draft(
        config, options=draft.get("options")
    )

    if draft != {k: v for k, v in rebuilt.items() if k in draft}:
        raise ValueError("Etkinlik taslağı geçersiz veya değiştirilmiş")

    checks = []

    def add(rule, status, message):
        checks.append({
            "rule": rule,
            "status": status,
            "message": message,
        })

    learning = profile.get("learning") or {}
    auditory = profile.get("auditory") or {}
    visual = profile.get("visual") or {}

    for section in (learning, auditory, visual):
        if not isinstance(section, dict):
            raise ValueError("Öğrenci profil bölümü geçersiz")

    max_choices = learning.get("max_choices")

    if type(max_choices) in (int, float) and max_choices > 0:
        if len(draft["options"]) > max_choices:
            add(
                "max_choices", "warning",
                "Seçenek sayısı öğrencinin belirlenen sınırını aşıyor."
            )
        else:
            add(
                "max_choices", "ok",
                "Seçenek sayısı belirlenen sınır içinde."
            )
    else:
        add(
            "max_choices", "review",
            "Öğrencinin seçenek sınırı belirtilmemiş."
        )

    spoken = auditory.get("spoken_instructions")

    if draft["audio_enabled"]:
        if spoken == "Uygun değil":
            add(
                "spoken_instructions", "warning",
                "Sesli yönerge öğrenci için uygun değil."
            )
        elif spoken == "Sınırlı kullanım":
            add(
                "spoken_instructions", "review",
                "Sesli yönerge sınırlı kullanılmalı."
            )
        elif spoken == "Uygun":
            add(
                "spoken_instructions", "ok",
                "Sesli yönerge profil tercihiyle uyumlu."
            )
        else:
            add(
                "spoken_instructions", "review",
                "Sesli yönerge uygunluğu belirtilmemiş."
            )
    else:
        add(
            "spoken_instructions", "ok",
            "Etkinlikte sesli yönerge kapalı."
        )

    visual_id = draft.get("visual_id")
    avoided = visual.get("avoided_colors", [])

    if not isinstance(avoided, list):
        raise ValueError("Kaçınılan renkler listesi geçersiz")

    if visual_id and visual_id.startswith("photo:"):
        from visual_library.photo_storage import list_approved_images

        photo_id = visual_id.removeprefix("photo:")
        approved = next(
            (
                asset for asset in list_approved_images()
                if asset.get("id") == photo_id
                and asset.get("teacher_approved") is True
            ),
            None,
        )

        if approved is None:
            raise ValueError("Fotoğraf onaylı görsel kütüphanesinde bulunamadı.")

        add(
            "photo_library_approval", "ok",
            "Fotoğraf öğretmen tarafından görsel kütüphanesine onaylanmış."
        )

        add(
            "photo_student_suitability", "review",
            "Fotoğrafın renkleri, içeriği ve öğrencinin bireysel "
            "görsel/duyusal gereksinimlerine uygunluğu otomatik "
            "olarak doğrulanamıyor. Öğretmen incelemesi gerekli."
        )

        if avoided:
            add(
                "photo_avoided_colors", "review",
                "Öğrencinin kaçınılan renkleri var. Fotoğraf bu "
                "renkler açısından öğretmen tarafından incelenmeli."
            )

    elif visual_id:
        renderer = OBJECTS[visual_id]["renderer"]
        signature = inspect.signature(renderer)
        colors = {}

        for parameter in ALLOWED_COLORS[visual_id]:
            definition = signature.parameters.get(parameter)

            if definition is None or not isinstance(
                definition.default, str
            ):
                add(
                    "svg_colors", "review",
                    "SVG varsayılan renkleri belirlenemedi."
                )
                break

            colors[parameter] = definition.default
        else:
            results = check_avoided_colors(colors, avoided)

            for result in results:
                add(
                    "svg_color_" + result["parameter"],
                    result["status"],
                    result["reason"] + ": " + result["color"],
                )

        unknown = [
            name for name in avoided
            if not isinstance(name, str) or name not in COLOR_NAMES
        ]

        if unknown:
            add(
                "unknown_colors", "review",
                "Tanımlanamayan kaçınılan renkler var."
            )
    else:
        add(
            "layout_colors", "review",
            "Bu görsel düzenin renkleri henüz denetlenmiyor."
        )

    review_fields = {
        "visual": ("other", "contrast"),
        "auditory": ("other", "avoided_sounds"),
        "motor": ("other",),
        "sensory_emotional": (
            "anxiety_triggers",
            "uncomfortable_stimuli",
            "stop_conditions",
            "other",
        ),
    }

    for section_name, field_names in review_fields.items():
        section = profile.get(section_name) or {}

        if not isinstance(section, dict):
            raise ValueError("Öğrenci profil bölümü geçersiz")

        for field_name in field_names:
            if section.get(field_name):
                add(
                    section_name + "." + field_name,
                    "review",
                    "Bu bireysel gereksinim öğretmen incelemesi gerektiriyor."
                )

    if profile.get("custom_requirements"):
        add(
            "custom_requirements", "review",
            "Ek bireysel gereksinimler öğretmen tarafından incelenmeli."
        )

    # Henüz kapsanmayan profil alanları uygun kabul edilmez.
    add(
        "remaining_requirements", "review",
        "Diğer profil özellikleri henüz otomatik doğrulanmıyor."
    )

    warnings = sum(c["status"] == "warning" for c in checks)
    reviews = sum(c["status"] == "review" for c in checks)

    overall = (
        "warning" if warnings else
        "review" if reviews else
        "ok"
    )

    return {
        "overall_status": overall,
        "warning_count": warnings,
        "review_count": reviews,
        "checks": checks,
        "teacher_approval_required": True,
    }
