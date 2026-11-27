"""
Common models and validation rules for performance recording.

Independent of Flask and database persistence.

Raw observations must remain separate from educational
interpretation and achievement mastery decisions.
"""

import json
import uuid

from datetime import datetime, timezone
from enum import Enum


EVENT_SCHEMA_VERSION = 1


class LearningMode(str, Enum):

    COMPUTER_BASED = "COMPUTER_BASED"
    TEACHER_ASSISTED = "TEACHER_ASSISTED"
    TEACHER_LED = "TEACHER_LED"


class SessionStatus(str, Enum):

    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"
    INTERRUPTED = "INTERRUPTED"


class EventSource(str, Enum):

    SYSTEM = "SYSTEM"
    TEACHER = "TEACHER"


class EventType(str, Enum):

    SESSION_STARTED = "SESSION_STARTED"
    SESSION_ENDED = "SESSION_ENDED"

    QUESTION_PRESENTED = "QUESTION_PRESENTED"
    QUESTION_COMPLETED = "QUESTION_COMPLETED"

    INSTRUCTION_DELIVERED = "INSTRUCTION_DELIVERED"
    INSTRUCTION_REPEATED = "INSTRUCTION_REPEATED"

    RESPONSE_SUBMITTED = "RESPONSE_SUBMITTED"

    PROMPT_DELIVERED = "PROMPT_DELIVERED"
    ASSISTANCE_PROVIDED = "ASSISTANCE_PROVIDED"

    FEEDBACK_DELIVERED = "FEEDBACK_DELIVERED"
    REINFORCEMENT_DELIVERED = "REINFORCEMENT_DELIVERED"

    TEACHER_OBSERVATION_RECORDED = (
        "TEACHER_OBSERVATION_RECORDED"
    )


class ResponseEvaluation(str, Enum):

    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"
    PARTIALLY_CORRECT = "PARTIALLY_CORRECT"
    NOT_EVALUATED = "NOT_EVALUATED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AssistanceStatus(str, Enum):

    INDEPENDENT = "INDEPENDENT"
    ASSISTED = "ASSISTED"
    UNKNOWN = "UNKNOWN"


class QuestionOutcome(str, Enum):

    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"
    PARTIALLY_CORRECT = "PARTIALLY_CORRECT"
    SKIPPED = "SKIPPED"
    INTERRUPTED = "INTERRUPTED"
    NOT_EVALUATED = "NOT_EVALUATED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ObservationCategory(str, Enum):

    ATTENTION = "ATTENTION"
    MOTIVATION = "MOTIVATION"
    SENSORY_RESPONSE = "SENSORY_RESPONSE"
    EMOTIONAL_RESPONSE = "EMOTIONAL_RESPONSE"
    MOTOR_PERFORMANCE = "MOTOR_PERFORMANCE"
    EXTERNAL_CONDITIONS = "EXTERNAL_CONDITIONS"
    ASSISTANCE = "ASSISTANCE"
    TEACHER_RECOMMENDATION = "TEACHER_RECOMMENDATION"
    OTHER = "OTHER"


def generate_identifier():
    """Generate a unique performance record identifier."""

    return str(uuid.uuid4())


def utc_now():
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc).isoformat(
        timespec="milliseconds"
    )


def validate_identifier(value, field_name, optional=False):

    if value is None and optional:
        return None

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{field_name} must be a non-empty string."
        )

    return value.strip()


def validate_enum(value, enum_class, field_name):

    try:
        return enum_class(value).value

    except (ValueError, TypeError):
        raise ValueError(
            f"Invalid {field_name}: {value!r}"
        ) from None


def validate_timestamp(value, field_name):

    if not isinstance(value, str):
        raise ValueError(
            f"{field_name} must be an ISO timestamp."
        )

    try:
        timestamp = datetime.fromisoformat(value)

    except ValueError:
        raise ValueError(
            f"Invalid timestamp for {field_name}."
        ) from None

    if timestamp.tzinfo is None:
        raise ValueError(
            f"{field_name} must include timezone information."
        )

    return timestamp.astimezone(timezone.utc).isoformat(
        timespec="milliseconds"
    )


def validate_nonnegative_integer(
    value,
    field_name,
    optional=False
):

    if value is None and optional:
        return None

    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
    ):
        raise ValueError(
            f"{field_name} must be a non-negative integer."
        )

    return value


def validate_positive_integer(value, field_name):

    value = validate_nonnegative_integer(
        value,
        field_name
    )

    if value == 0:
        raise ValueError(
            f"{field_name} must be greater than zero."
        )

    return value


def encode_json_object(value, field_name):
    """
    Serialize a JSON object without non-standard numeric values.

    Reject NaN, Infinity and unsupported Python objects.
    """

    if not isinstance(value, dict):
        raise ValueError(
            f"{field_name} must be a JSON object."
        )

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":")
        )

    except (ValueError, TypeError) as error:
        raise ValueError(
            f"Invalid JSON object for {field_name}: {error}"
        ) from error


def decode_json_object(value, field_name):

    try:
        result = json.loads(value)

    except (ValueError, TypeError) as error:
        raise ValueError(
            f"Invalid stored JSON for {field_name}."
        ) from error

    if not isinstance(result, dict):
        raise ValueError(
            f"Stored {field_name} must be a JSON object."
        )

    return result


def build_session_record(
    student_id,
    learning_mode,
    activity_snapshot,
    assignment_id=None,
    activity_id=None,
    achievement_code=None
):
    """Construct a new persistent learning session record."""

    return {
        "session_id": generate_identifier(),

        "student_id": validate_identifier(
            student_id, "student_id"
        ),

        "assignment_id": validate_identifier(
            assignment_id, "assignment_id", optional=True
        ),

        "activity_id": validate_identifier(
            activity_id, "activity_id", optional=True
        ),

        "achievement_code": validate_identifier(
            achievement_code,
            "achievement_code",
            optional=True
        ),

        "learning_mode": validate_enum(
            learning_mode,
            LearningMode,
            "learning_mode"
        ),

        "activity_snapshot": encode_json_object(
            activity_snapshot,
            "activity_snapshot"
        ),

        "started_at": utc_now(),
        "ended_at": None,
        "status": SessionStatus.ACTIVE.value,
        "termination_reason": None
    }


def build_event_record(
    session_id,
    sequence_number,
    event_type,
    source,
    payload,
    question_id=None,
    attempt_id=None,
    occurred_at=None,
    event_id=None
):
    """Construct a chronological performance event."""

    event_type = validate_enum(
        event_type,
        EventType,
        "event_type"
    )

    source = validate_enum(
        source,
        EventSource,
        "source"
    )

    if (
        event_type == EventType.TEACHER_OBSERVATION_RECORDED.value
        and source != EventSource.TEACHER.value
    ):
        raise ValueError(
            "Teacher observations require a teacher source."
        )

    question_id = validate_identifier(
        question_id,
        "question_id",
        optional=True
    )

    attempt_id = validate_identifier(
        attempt_id,
        "attempt_id",
        optional=True
    )

    if attempt_id is not None and question_id is None:
        raise ValueError(
            "An attempt must belong to a question."
        )

    if event_type in (
        EventType.QUESTION_PRESENTED.value,
        EventType.QUESTION_COMPLETED.value,
        EventType.RESPONSE_SUBMITTED.value
    ) and question_id is None:
        raise ValueError(
            f"{event_type} requires a question identifier."
        )

    if (
        event_type == EventType.RESPONSE_SUBMITTED.value
        and attempt_id is None
    ):
        raise ValueError(
            "A response requires an attempt identifier."
        )

    recorded_at = utc_now()

    return {
        "event_id": (
            generate_identifier()
            if event_id is None
            else validate_identifier(event_id, "event_id")
        ),

        "session_id": validate_identifier(
            session_id,
            "session_id"
        ),

        "question_id": question_id,
        "attempt_id": attempt_id,

        "sequence_number": validate_positive_integer(
            sequence_number,
            "sequence_number"
        ),

        "event_type": event_type,

        "occurred_at": (
            recorded_at
            if occurred_at is None
            else validate_timestamp(
                occurred_at,
                "occurred_at"
            )
        ),

        "recorded_at": recorded_at,
        "source": source,

        "payload": encode_json_object(
            payload,
            "payload"
        ),

        "schema_version": EVENT_SCHEMA_VERSION
    }
