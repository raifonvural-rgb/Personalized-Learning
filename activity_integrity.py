"""Activity-specific integrity verification dispatcher.

This module does not save, validate for a student,
approve or publish activities.
"""

from quantity_activity_models import QUANTITY_ACTIVITY_TYPES

from quantity_activity_integrity import (
    validate_quantity_draft_integrity,
)


def validate_digit_draft_integrity(draft):
    """Preserve existing digit draft verification."""

    required = {
        "achievement_code",
        "activity_type",
        "target_digit",
        "layout_id",
        "options",
        "correct_index",
    }

    if not required.issubset(draft):
        raise ValueError("Activity draft is incomplete")

    from activity_models import ActivityConfig
    from activity_builder import build_find_digit_draft

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

    validated = build_find_digit_draft(
        config,
        options=draft.get("options"),
    )

    if draft != {k: v for k, v in validated.items() if k in draft}:
        raise ValueError(
            "Draft does not match the validated activity configuration"
        )



def validate_activity_draft_integrity(draft):
    """Route integrity verification by activity type."""

    if not isinstance(draft, dict):
        raise ValueError("Activity draft must be an object")

    if draft.get("status") != "draft":
        raise ValueError("Only drafts can be verified")

    if draft.get("teacher_approved") is not False:
        raise ValueError("Draft must not be teacher-approved")

    activity_type = draft.get("activity_type")

    if not isinstance(activity_type, str):
        raise ValueError("Invalid activity type")

    if activity_type == "find_digit":
        return validate_digit_draft_integrity(draft)

    if activity_type in QUANTITY_ACTIVITY_TYPES:
        return validate_quantity_draft_integrity(draft)

    raise ValueError("Unsupported activity type")
