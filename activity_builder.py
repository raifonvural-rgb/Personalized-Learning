"""
Build teacher-reviewable activity drafts.

No student assignment, persistence, or approval occurs here.
"""

from activity_models import ActivityConfig
from activity_options import (
    generate_digit_options,
    validate_digit_options,
)


def build_find_digit_draft(
    config,
    options=None,
    option_count=4,
    seed=None,
):
    if not isinstance(config, ActivityConfig):
        raise ValueError("config must be an ActivityConfig")

    config.validate()

    if config.activity_type != "find_digit":
        raise ValueError("Only find_digit is supported")

    layout_id = config.settings.get("layout_id")

    if layout_id is None:
        raise ValueError(
            "A visual layout must be selected before building a draft"
        )

    if options is None:
        result = generate_digit_options(
            target_digit=config.target_digit,
            option_count=option_count,
            seed=seed,
        )
    else:
        result = validate_digit_options(
            target_digit=config.target_digit,
            options=options,
        )

    return {
        "achievement_code": config.achievement_code,
        "activity_type": config.activity_type,
        "target_digit": config.target_digit,
        "layout_id": layout_id,
        "visual_id": config.visual_id,
        "audio_enabled": config.audio_enabled,
        "celebration_enabled": config.celebration_enabled,
        "quantity_animation_enabled": config.quantity_animation_enabled,
        "options": result["options"],
        "correct_index": result["correct_index"],
        "status": "draft",
        "teacher_approved": False,
    }
