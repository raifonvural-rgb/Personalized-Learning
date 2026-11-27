"""
Data models for teacher-controlled activity assignments.

Assignment identity, enablement, ordering and lifecycle
are independent of the original activity configuration.
"""

from enum import Enum

from performance_models import (
    generate_identifier,
    utc_now,
    validate_identifier,
    validate_enum,
    validate_positive_integer,
)


class AssignmentStatus(str, Enum):

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


def validate_enabled(value):

    if not isinstance(value, bool):
        raise ValueError(
            "Assignment enabled must be a Boolean"
        )

    return int(value)


def validate_assignment_status(value):

    return validate_enum(
        value,
        AssignmentStatus,
        "assignment_status"
    )


def build_assignment_record(
    student_id,
    activity_id,
    sequence_order,
    enabled=True
):

    student_id = validate_identifier(
        student_id,
        "student_id"
    )

    activity_id = validate_identifier(
        activity_id,
        "activity_id"
    )

    sequence_order = validate_positive_integer(
        sequence_order,
        "sequence_order"
    )

    enabled = validate_enabled(enabled)

    timestamp = utc_now()

    return {
        "assignment_id": generate_identifier(),
        "student_id": student_id,
        "activity_id": activity_id,
        "sequence_order": sequence_order,
        "enabled": enabled,
        "status": AssignmentStatus.PENDING.value,
        "assigned_at": timestamp,
        "started_at": None,
        "completed_at": None,
        "updated_at": timestamp,
    }


def decode_assignment(row):

    if row is None:
        return None

    record = dict(row)

    record["enabled"] = bool(record["enabled"])

    return record
