"""
Transactional question presentation and round management.
"""

from activity_execution_models import (
    requires_first_attempt_success,
)

from activity_execution_repository import (
    require_transaction,
    find_execution_state,
    find_current_round,
    decode_execution_round,
    transition_execution_state,
)

from activity_presentation import (
    build_question_presentation,
)

from performance_models import (
    EventType,
    EventSource,
    generate_identifier,
    validate_identifier,
    encode_json_object,
    utc_now,
)

from performance_storage import (
    find_session,
    decode_session,
    append_performance_event_in_transaction,
)


def persist_question_round(
    connection,
    session_id,
    presentation
):
    """
    Persist a server-generated question presentation
    and its corresponding performance event.

    The caller owns the write transaction.
    """

    require_transaction(connection)

    session_id = validate_identifier(
        session_id,
        "session_id"
    )

    learning_session = find_session(
        connection,
        session_id
    )

    if (
        learning_session is None
        or learning_session["status"] != "ACTIVE"
    ):
        raise ValueError(
            "Active learning session required"
        )

    state = find_execution_state(
        connection,
        session_id
    )

    if state is None:
        raise ValueError(
            "Execution state does not exist"
        )

    if state["status"] not in (
        "READY",
        "REPEAT_REQUIRED",
    ):
        raise ValueError(
            "Execution is not ready for a new round"
        )

    round_number = (
        state["current_round_number"] + 1
    )

    first_attempt_required = (
        requires_first_attempt_success(
            round_number
        )
    )

    question_id = generate_identifier()

    timestamp = utc_now()

    event = append_performance_event_in_transaction(
        connection=connection,
        session_id=session_id,
        event_type=EventType.QUESTION_PRESENTED,
        source=EventSource.SYSTEM,
        question_id=question_id,
        occurred_at=timestamp,
        payload={
            "sequence_number": round_number,

            "activity_type":
                presentation["activity_type"],

            "achievement_code":
                presentation["achievement_code"],

            "instruction":
                presentation["instruction"],

            "target_answer":
                presentation["target_answer"],

            "presented_choices":
                presentation["presented_choices"],

            "presentation_context": {
                **presentation["presentation_context"],

                "question":
                    presentation["question"],

                "round_number":
                    round_number,

                "first_attempt_required":
                    first_attempt_required,

                "correct_index":
                    presentation["correct_index"],
            },
        }
    )

    record = {
        "question_id": question_id,
        "session_id": session_id,
        "round_number": round_number,
        "status": "ACTIVE",

        "presentation_snapshot":
            encode_json_object(
                presentation,
                "presentation_snapshot"
            ),

        "first_attempt_required":
            int(first_attempt_required),

        "attempt_count": 0,
        "selected_alternatives": "[]",
        "presentation_event_id": event["event_id"],
        "completion_event_id": None,
        "presented_at": timestamp,
        "ended_at": None,
    }

    connection.execute("""
        INSERT INTO activity_execution_rounds (
            question_id,
            session_id,
            round_number,
            status,
            presentation_snapshot,
            first_attempt_required,
            attempt_count,
            selected_alternatives,
            presentation_event_id,
            completion_event_id,
            presented_at,
            ended_at
        )
        VALUES (
            :question_id,
            :session_id,
            :round_number,
            :status,
            :presentation_snapshot,
            :first_attempt_required,
            :attempt_count,
            :selected_alternatives,
            :presentation_event_id,
            :completion_event_id,
            :presented_at,
            :ended_at
        )
    """, record)

    transition_execution_state(
        connection=connection,
        session_id=session_id,
        target_status="AWAITING_RESPONSE",
        current_round_number=round_number,
    )

    return decode_execution_round(record)


def initialize_first_round(
    connection,
    session_id
):
    """
    Initialize the first question using the immutable
    learning session activity snapshot.

    Repeated initialization returns the existing
    current round without creating another question.
    """

    require_transaction(connection)

    session_id = validate_identifier(
        session_id,
        "session_id"
    )

    learning_session = decode_session(
        find_session(
            connection,
            session_id
        )
    )

    if (
        learning_session is None
        or learning_session["status"] != "ACTIVE"
    ):
        raise ValueError(
            "Active learning session required"
        )

    state = find_execution_state(
        connection,
        session_id
    )

    if state is None:
        raise ValueError(
            "Execution state does not exist"
        )

    if state["status"] in (
        "COMPLETED",
        "INTERRUPTED",
    ):
        raise ValueError(
            "Execution state is terminal"
        )

    if state["current_round_number"] > 0:

        return decode_execution_round(
            find_current_round(
                connection,
                session_id
            )
        )

    if state["status"] != "READY":
        raise ValueError(
            "Invalid initial execution state"
        )

    configuration = learning_session[
        "activity_snapshot"
    ]["configuration"]

    presentation = build_question_presentation(
        configuration
    )

    return persist_question_round(
        connection=connection,
        session_id=session_id,
        presentation=presentation,
    )
