"""Route student-specific validation by activity type.

This module does not save activities, create validation
records, approve activities or publish them.
"""

from activity_validation import (
    validate_activity_for_student as validate_digit_activity,
)

from quantity_activity_validation import (
    validate_quantity_activity_for_student,
)

from quantity_activity_models import QUANTITY_ACTIVITY_TYPES


def validate_activity_for_student(draft, profile):
    """Validate an activity against its student's profile."""

    if not isinstance(draft, dict):
        raise ValueError("Activity draft must be an object")

    if not isinstance(profile, dict):
        raise ValueError("Student profile must be an object")

    activity_type = draft.get("activity_type")

    if not isinstance(activity_type, str):
        raise ValueError("Invalid activity type")

    if activity_type == "find_digit":
        return validate_digit_activity(draft, profile)

    if activity_type in QUANTITY_ACTIVITY_TYPES:
        return validate_quantity_activity_for_student(
            draft, profile
        )

    raise ValueError("Unsupported activity type")
