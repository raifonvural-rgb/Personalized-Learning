"""
Validate activity-designer requests and build unapproved drafts.
"""

from activity_models import ActivityConfig
from activity_builder import build_find_digit_draft


def build_digit_draft_from_request(data):
    if not isinstance(data, dict):
        raise ValueError("Request data must be an object")

    target = data.get("target_digit")

    if type(target) is not int:
        raise ValueError("Target digit must be an integer")

    layout_id = data.get("layout_id")
    visual_id = data.get("visual_id")

    if visual_id == "":
        visual_id = None

    options = data.get("options")

    if not isinstance(options, list):
        raise ValueError("Options must be a list")

    config = ActivityConfig(
        achievement_code="MAT1.1.1",
        target_digit=target,
        activity_type="find_digit",
        visual_id=visual_id,
        quantity_animation_enabled=data.get("quantity_animation_enabled", False),
        settings={"layout_id": layout_id},
    )

    return build_find_digit_draft(
        config=config,
        options=options,
    )



from quantity_activity_models import (
    QuantityActivityConfig,
    QUANTITY_ACTIVITY_TYPES,
)

from quantity_activity_builder import (
    build_quantity_activity_draft,
)


def build_quantity_draft_from_request(data):
    """Build an unapproved quantity activity draft."""

    config = QuantityActivityConfig(
        activity_type=data.get("activity_type"),
        target_quantity=data.get("target_quantity"),
        visual_id=data.get("visual_id"),
        min_quantity=data.get("min_quantity", 0),
        max_quantity=data.get("max_quantity", 9),
        options=data.get("options"),
        arrangement=data.get("arrangement", "grid"),
        audio_enabled=data.get("audio_enabled", True),
        spoken_counting_enabled=data.get(
            "spoken_counting_enabled", False
        ),
        quantity_animation_enabled=data.get(
            "quantity_animation_enabled", False
        ),
        celebration_enabled=data.get(
            "celebration_enabled", True
        ),
    )

    return build_quantity_activity_draft(config)


def build_draft_from_request(data):
    """Route requests to the appropriate activity builder."""

    if not isinstance(data, dict):
        raise ValueError("Request data must be an object")

    activity_type = data.get("activity_type", "find_digit")

    if not isinstance(activity_type, str):
        raise ValueError("Activity type must be a string")

    if activity_type == "find_digit":
        return build_digit_draft_from_request(data)

    if activity_type in QUANTITY_ACTIVITY_TYPES:
        return build_quantity_draft_from_request(data)

    raise ValueError("Unsupported activity type")
