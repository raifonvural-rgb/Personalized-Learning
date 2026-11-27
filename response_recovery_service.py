"""Read-only verification of uncertain student response submissions."""

from performance_models import (
    EventType,
    EventSource,
    validate_identifier,
    validate_nonnegative_integer,
)

from performance_storage import (
    find_session,
    decode_event,
)


def inspect_response_recording(
    connection,
    student_id,
    assignment_id,
    performance_session_id,
    question_id,
    request_id,
    selected_position,
):
    """Inspect a response without modifying execution or event history."""

    if not connection.in_transaction:
        raise RuntimeError(
            "Response inspection requires a database transaction."
        )

    student_id = validate_identifier(
        student_id,
        "student_id",
    )

    assignment_id = validate_identifier(
        assignment_id,
        "assignment_id",
    )

    performance_session_id = validate_identifier(
        performance_session_id,
        "performance_session_id",
    )

    question_id = validate_identifier(
        question_id,
        "question_id",
    )

    request_id = validate_identifier(
        request_id,
        "request_id",
    )

    selected_position = validate_nonnegative_integer(
        selected_position,
        "selected_position",
    )

    learning_session = find_session(
        connection,
        performance_session_id,
    )

    if (
        learning_session is None
        or learning_session["student_id"] != student_id
        or learning_session["assignment_id"] != assignment_id
    ):
        raise ValueError(
            "Learning session association could not be verified."
        )

    result = {
        "assignment_id": assignment_id,
        "performance_session_id": performance_session_id,
        "question_id": question_id,
        "request_id": request_id,
        "selected_position": selected_position,
        "session_status": learning_session["status"],
    }

    row = connection.execute(
        """
        SELECT *
        FROM performance_events
        WHERE event_id = ?
        """,
        (request_id,),
    ).fetchone()

    if row is None:

        return {
            **result,
            "recording_status": "NOT_RECORDED",
        }

    event = decode_event(row)

    payload = event["payload"]

    if (
        event["session_id"] != performance_session_id
        or event["question_id"] != question_id
        or event["event_type"] != EventType.RESPONSE_SUBMITTED.value
        or event["source"] != EventSource.SYSTEM.value
        or payload.get("selected_position") != selected_position
    ):

        return {
            **result,
            "recording_status": "CONFLICT",
        }

    return {
        **result,
        "recording_status": "RECORDED",
        "recorded_response": {
            "event_id": event["event_id"],
            "attempt_id": event["attempt_id"],
            "sequence_number": event["sequence_number"],
            "recorded_at": event["recorded_at"],
            "attempt_number": payload.get("attempt_number"),
        },
    }
