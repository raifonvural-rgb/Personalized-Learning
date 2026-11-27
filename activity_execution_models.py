"""
Data models for server-controlled activity execution.

Operational state is separate from historical
performance observations and educational interpretation.
"""

from enum import Enum

from performance_models import (
    validate_identifier,
    validate_enum,
    validate_positive_integer,
    validate_nonnegative_integer,
    utc_now,
)


class ExecutionStatus(str, Enum):

    READY = "READY"
    AWAITING_RESPONSE = "AWAITING_RESPONSE"
    REPEAT_REQUIRED = "REPEAT_REQUIRED"
    SUCCESS_CONFIRMED = "SUCCESS_CONFIRMED"
    COMPLETED = "COMPLETED"
    INTERRUPTED = "INTERRUPTED"


class RoundStatus(str, Enum):

    ACTIVE = "ACTIVE"
    REPEAT_REQUIRED = "REPEAT_REQUIRED"
    SUCCESS_CONFIRMED = "SUCCESS_CONFIRMED"
    INTERRUPTED = "INTERRUPTED"


class FeedbackType(str, Enum):

    SUCCESS = "SUCCESS"
    ENCOURAGEMENT = "ENCOURAGEMENT"
    DISCOVERY = "DISCOVERY"


EXECUTION_TRANSITIONS = {

    ExecutionStatus.READY: {
        ExecutionStatus.AWAITING_RESPONSE,
        ExecutionStatus.INTERRUPTED,
    },

    ExecutionStatus.AWAITING_RESPONSE: {
        ExecutionStatus.AWAITING_RESPONSE,
        ExecutionStatus.REPEAT_REQUIRED,
        ExecutionStatus.SUCCESS_CONFIRMED,
        ExecutionStatus.INTERRUPTED,
    },

    ExecutionStatus.REPEAT_REQUIRED: {
        ExecutionStatus.AWAITING_RESPONSE,
        ExecutionStatus.INTERRUPTED,
    },

    ExecutionStatus.SUCCESS_CONFIRMED: {
        ExecutionStatus.COMPLETED,
        ExecutionStatus.INTERRUPTED,
    },

    ExecutionStatus.COMPLETED: set(),

    ExecutionStatus.INTERRUPTED: set(),
}


def validate_execution_status(value):

    return validate_enum(
        value,
        ExecutionStatus,
        "execution_status"
    )


def validate_round_status(value):

    return validate_enum(
        value,
        RoundStatus,
        "round_status"
    )


def validate_execution_transition(
    current_status,
    target_status
):

    current = ExecutionStatus(
        validate_execution_status(current_status)
    )

    target = ExecutionStatus(
        validate_execution_status(target_status)
    )

    if target not in EXECUTION_TRANSITIONS[current]:

        raise ValueError(
            f"Invalid execution transition: "
            f"{current.value} -> {target.value}"
        )

    return target.value


def build_execution_state(session_id):

    session_id = validate_identifier(
        session_id,
        "session_id"
    )

    timestamp = utc_now()

    return {
        "session_id": session_id,
        "status": ExecutionStatus.READY.value,
        "current_round_number": 0,
        "completion_event_id": None,
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def validate_selected_alternatives(
    selected_alternatives,
    alternative_count
):

    alternative_count = validate_positive_integer(
        alternative_count,
        "alternative_count"
    )

    if not isinstance(selected_alternatives, list):

        raise ValueError(
            "Selected alternatives must be a list"
        )

    validated = []

    for position in selected_alternatives:

        position = validate_nonnegative_integer(
            position,
            "selected_position"
        )

        if position >= alternative_count:

            raise ValueError(
                "Selected alternative is out of range"
            )

        if position in validated:

            raise ValueError(
                "Duplicate selected alternative"
            )

        validated.append(position)

    return validated


def validate_round_progress(
    attempt_count,
    selected_alternatives,
    alternative_count
):

    attempt_count = validate_nonnegative_integer(
        attempt_count,
        "attempt_count"
    )

    selected_alternatives = (
        validate_selected_alternatives(
            selected_alternatives,
            alternative_count
        )
    )

    if len(selected_alternatives) > attempt_count:

        raise ValueError(
            "Distinct selections cannot exceed attempts"
        )

    if attempt_count > 0 and not selected_alternatives:

        raise ValueError(
            "Recorded attempts require a selection"
        )

    return {
        "attempt_count": attempt_count,
        "selected_alternatives": selected_alternatives,
        "distinct_selection_count": len(
            selected_alternatives
        ),
    }


def requires_first_attempt_success(round_number):

    round_number = validate_positive_integer(
        round_number,
        "round_number"
    )

    return round_number > 1
