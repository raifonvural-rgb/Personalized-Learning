"""
Validate activity-designer requests and build unapproved drafts.
"""

from activity_models import ActivityConfig
from activity_builder import build_find_digit_draft


def build_draft_from_request(data):
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
