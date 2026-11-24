"""
Öğretmen kontrollü etkinlikler için öğrenciye özgü ön doğrulama.

Bu modül kayıt oluşturmaz, etkinlik onaylamaz.
Belirsiz ve denetlenemeyen gereksinimler öğretmen incelemesine yönlendirilir.
"""

from activity_builder import build_find_digit_draft
from activity_models import ActivityConfig
from student_activity_validation import (
    validate_common_student_requirements,
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

    return validate_common_student_requirements(draft, profile)
