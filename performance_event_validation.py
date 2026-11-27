"""
Event-specific validation for student performance observations.

This module validates the structure of recorded observations.
It does not establish educational correctness or mastery.

Additional event attributes are permitted to support future
instructional methods and activity types.
"""

from performance_models import (
    EventType,
    EventSource,
    LearningMode,
    SessionStatus,
    ResponseEvaluation,
    AssistanceStatus,
    QuestionOutcome,
    ObservationCategory,
    validate_identifier,
    validate_enum,
    validate_positive_integer,
    validate_nonnegative_integer,
    encode_json_object
)


def require_fields(payload, fields):

    missing = [
        field for field in fields
        if field not in payload
    ]

    if missing:
        raise ValueError(
            "Missing event fields: " + ", ".join(missing)
        )


def validate_text(value, field_name, optional=False):

    if value is None and optional:
        return

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"{field_name} must be non-empty text."
        )


def validate_optional_duration(payload, field_name):

    validate_nonnegative_integer(
        payload.get(field_name),
        field_name,
        optional=True
    )


def validate_session_started(payload):

    require_fields(
        payload,
        ("learning_mode",)
    )

    validate_enum(
        payload["learning_mode"],
        LearningMode,
        "learning_mode"
    )

    for field in (
        "assignment_id",
        "activity_id",
        "achievement_code"
    ):
        validate_identifier(
            payload.get(field),
            field,
            optional=True
        )


def validate_session_ended(payload):

    require_fields(payload, ("status",))

    status = validate_enum(
        payload["status"],
        SessionStatus,
        "status"
    )

    if status == SessionStatus.ACTIVE.value:
        raise ValueError(
            "Session ending requires a terminal status."
        )

    validate_text(
        payload.get("termination_reason"),
        "termination_reason",
        optional=True
    )


def validate_question_presented(payload):

    require_fields(
        payload,
        (
            "sequence_number",
            "activity_type",
            "instruction",
            "target_answer",
            "presented_choices",
            "presentation_context"
        )
    )

    validate_positive_integer(
        payload["sequence_number"],
        "sequence_number"
    )

    validate_text(
        payload["activity_type"],
        "activity_type"
    )

    validate_text(
        payload["instruction"],
        "instruction",
        optional=True
    )

    validate_identifier(
        payload.get("achievement_code"),
        "achievement_code",
        optional=True
    )

    if not isinstance(payload["presented_choices"], list):
        raise ValueError(
            "Presented choices must be an ordered list."
        )

    encode_json_object(
        payload["presentation_context"],
        "presentation_context"
    )


def validate_response_submitted(payload):

    require_fields(
        payload,
        (
            "attempt_number",
            "response",
            "evaluation",
            "assistance_status"
        )
    )

    validate_positive_integer(
        payload["attempt_number"],
        "attempt_number"
    )

    validate_enum(
        payload["evaluation"],
        ResponseEvaluation,
        "evaluation"
    )

    validate_enum(
        payload["assistance_status"],
        AssistanceStatus,
        "assistance_status"
    )

    validate_nonnegative_integer(
        payload.get("selected_position"),
        "selected_position",
        optional=True
    )

    validate_optional_duration(
        payload,
        "elapsed_since_presentation_ms"
    )

    validate_optional_duration(
        payload,
        "elapsed_since_previous_attempt_ms"
    )

    first_duration = payload.get(
        "elapsed_since_presentation_ms"
    )

    previous_duration = payload.get(
        "elapsed_since_previous_attempt_ms"
    )

    if (
        first_duration is not None
        and previous_duration is not None
        and previous_duration > first_duration
    ):
        raise ValueError(
            "Time since previous attempt cannot exceed "
            "time since question presentation."
        )


def validate_question_completed(payload):

    require_fields(payload, ("outcome",))

    validate_enum(
        payload["outcome"],
        QuestionOutcome,
        "outcome"
    )

    validate_optional_duration(
        payload,
        "duration_ms"
    )


def validate_instruction(payload):

    require_fields(
        payload,
        ("modality",)
    )

    validate_text(
        payload["modality"],
        "modality"
    )

    validate_text(
        payload.get("instruction"),
        "instruction",
        optional=True
    )


def validate_support(payload):

    require_fields(
        payload,
        ("support_type",)
    )

    validate_text(
        payload["support_type"],
        "support_type"
    )

    validate_optional_duration(
        payload,
        "duration_ms"
    )


def validate_feedback(payload):

    require_fields(
        payload,
        ("feedback_type",)
    )

    validate_text(
        payload["feedback_type"],
        "feedback_type"
    )


def validate_reinforcement(payload):

    require_fields(
        payload,
        ("reinforcement_type",)
    )

    validate_text(
        payload["reinforcement_type"],
        "reinforcement_type"
    )


def validate_teacher_observation(payload):

    require_fields(
        payload,
        ("category", "observation_data")
    )

    validate_enum(
        payload["category"],
        ObservationCategory,
        "category"
    )

    encode_json_object(
        payload["observation_data"],
        "observation_data"
    )

    validate_text(
        payload.get("notes"),
        "notes",
        optional=True
    )

    validate_identifier(
        payload.get("teacher_id"),
        "teacher_id",
        optional=True
    )


EVENT_VALIDATORS = {

    EventType.SESSION_STARTED.value:
        validate_session_started,

    EventType.SESSION_ENDED.value:
        validate_session_ended,

    EventType.QUESTION_PRESENTED.value:
        validate_question_presented,

    EventType.RESPONSE_SUBMITTED.value:
        validate_response_submitted,

    EventType.QUESTION_COMPLETED.value:
        validate_question_completed,

    EventType.INSTRUCTION_DELIVERED.value:
        validate_instruction,

    EventType.INSTRUCTION_REPEATED.value:
        validate_instruction,

    EventType.PROMPT_DELIVERED.value:
        validate_support,

    EventType.ASSISTANCE_PROVIDED.value:
        validate_support,

    EventType.FEEDBACK_DELIVERED.value:
        validate_feedback,

    EventType.REINFORCEMENT_DELIVERED.value:
        validate_reinforcement,

    EventType.TEACHER_OBSERVATION_RECORDED.value:
        validate_teacher_observation
}


def validate_event_payload(event_type, source, payload):

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

    encode_json_object(
        payload,
        "payload"
    )

    if (
        event_type ==
        EventType.TEACHER_OBSERVATION_RECORDED.value
        and source != EventSource.TEACHER.value
    ):
        raise ValueError(
            "Teacher observations require a teacher source."
        )

    validator = EVENT_VALIDATORS.get(event_type)

    if validator is None:
        raise ValueError(
            f"No payload validator for {event_type}."
        )

    validator(payload)
