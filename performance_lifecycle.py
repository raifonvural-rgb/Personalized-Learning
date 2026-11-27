"""
Bridge between the existing learning workflow and
persistent student performance recording.

Teacher previews must never invoke session creation.

The performance subsystem preserves historical records
independently of current activity assignments.
"""

from copy import deepcopy

from profile_storage import get_profile
from activity_storage import get_activity
from activity_integrity import validate_activity_draft_integrity

from performance_models import (
    LearningMode,
    SessionStatus
)

from performance_storage import (
    create_learning_session,
    get_learning_session,
    end_learning_session
)


PERFORMANCE_SESSION_KEY = "performance_session_id"


def start_performance_session(student_id, assignment):
    """
    Create a persistent performance session for an
    approved activity assigned to the selected student.
    """

    if get_profile(student_id) is None:
        raise ValueError("Student does not exist.")

    if not isinstance(assignment, dict):
        raise ValueError("Invalid activity assignment.")

    if assignment.get("student_id") != student_id:
        raise ValueError(
            "Assignment belongs to another student."
        )

    assignment_id = assignment.get("id")
    activity_id = assignment.get("activity_id")

    if not assignment_id or not activity_id:
        raise ValueError(
            "Assignment identifiers are missing."
        )

    activity = get_activity(activity_id)

    if activity is None:
        raise ValueError("Assigned activity does not exist.")

    if activity.get("student_id") != student_id:
        raise ValueError(
            "Activity belongs to another student."
        )

    if activity.get("status") != "approved":
        raise ValueError(
            "Assigned activity is not approved."
        )

    configuration = activity.get("config")

    if not isinstance(configuration, dict):
        raise ValueError(
            "Activity configuration is missing."
        )

    validate_activity_draft_integrity(configuration)

    achievement_code = configuration.get(
        "achievement_code"
    )

    if not isinstance(achievement_code, str):
        achievement_code = None

    activity_snapshot = {
        "activity_id": activity_id,
        "configuration": deepcopy(configuration)
    }

    return create_learning_session(
        student_id=student_id,
        learning_mode=LearningMode.COMPUTER_BASED,
        activity_snapshot=activity_snapshot,
        assignment_id=assignment_id,
        activity_id=activity_id,
        achievement_code=achievement_code
    )


def get_bound_performance_session(
    performance_session_id,
    student_id,
    assignment_id
):
    """
    Retrieve a performance session only when its
    student and assignment associations match.
    """

    if not all((
        performance_session_id,
        student_id,
        assignment_id
    )):
        return None

    record = get_learning_session(
        performance_session_id
    )

    if record is None:
        return None

    if record["student_id"] != student_id:
        return None

    if record["assignment_id"] != assignment_id:
        return None

    return record


def finish_performance_session(
    performance_session_id,
    student_id,
    assignment_id,
    status=SessionStatus.TERMINATED,
    reason=None
):
    """
    Finalize the matching performance session.

    Never terminate an unrelated student's session.
    """

    record = get_bound_performance_session(
        performance_session_id,
        student_id,
        assignment_id
    )

    if record is None:
        return None

    return end_learning_session(
        session_id=record["session_id"],
        status=status,
        termination_reason=reason
    )
