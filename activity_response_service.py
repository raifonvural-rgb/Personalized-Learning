"""
Transactional student response recording and
educational execution state management.
"""

import json

from activity_response_evaluator import (
    evaluate_response,
)

from activity_execution_repository import (
    require_transaction,
    find_execution_state,
    find_current_round,
    decode_execution_round,
    transition_execution_state,
)

from performance_database import (
    database_transaction,
)

from performance_models import (
    EventType,
    EventSource,
    generate_identifier,
    validate_identifier,
    validate_nonnegative_integer,
    utc_now,
)

from performance_storage import (
    find_session,
    decode_event,
    append_performance_event_in_transaction,
)


def record_response_in_transaction(
    connection,
    session_id,
    question_id,
    request_id,
    selected_position
):

    require_transaction(connection)

    session_id = validate_identifier(
        session_id,
        "session_id"
    )

    question_id = validate_identifier(
        question_id,
        "question_id"
    )

    request_id = validate_identifier(
        request_id,
        "request_id"
    )

    selected_position = validate_nonnegative_integer(
        selected_position,
        "selected_position"
    )

    learning_session = find_session(
        connection,
        session_id
    )

    if learning_session is None:

        raise ValueError(
            "Learning session does not exist"
        )

    # Check request idempotency before checking
    # whether the question is still active.

    existing = connection.execute("""
        SELECT *
        FROM performance_events
        WHERE event_id = ?
    """, (request_id,)).fetchone()

    if existing is not None:

        existing = decode_event(existing)

        if (
            existing["session_id"] != session_id
            or existing["question_id"] != question_id
            or existing["event_type"] !=
                "RESPONSE_SUBMITTED"
            or existing["source"] != "SYSTEM"
            or existing["payload"].get(
                "selected_position"
            ) != selected_position
        ):

            raise ValueError(
                "Response request identifier conflict"
            )

        decision = existing["payload"].get(
            "progression_decision"
        )

        if not isinstance(decision, dict):

            raise ValueError(
                "Existing event is not an execution response"
            )

        return {
            "question_id": question_id,
            "response_event_id": request_id,
            "decision": decision,
            "duplicate_request": True,
        }

    if learning_session["status"] != "ACTIVE":

        raise ValueError(
            "Learning session is not active"
        )

    state = find_execution_state(
        connection,
        session_id
    )

    if (
        state is None
        or state["status"] != "AWAITING_RESPONSE"
    ):

        raise ValueError(
            "Execution is not awaiting a response"
        )

    current_round = decode_execution_round(
        find_current_round(
            connection,
            session_id
        )
    )

    if (
        current_round is None
        or current_round["question_id"] != question_id
        or current_round["status"] != "ACTIVE"
    ):

        raise ValueError(
            "Response does not belong to the active round"
        )

    presentation = current_round[
        "presentation_snapshot"
    ]

    decision = evaluate_response(
        presentation=presentation,

        round_number=current_round[
            "round_number"
        ],

        previous_attempt_count=current_round[
            "attempt_count"
        ],

        previously_selected_alternatives=current_round[
            "selected_alternatives"
        ],

        selected_position=selected_position,
    )

    timestamp = utc_now()

    attempt_id = generate_identifier()

    response_event = (
        append_performance_event_in_transaction(
            connection=connection,
            session_id=session_id,
            event_type=EventType.RESPONSE_SUBMITTED,
            source=EventSource.SYSTEM,
            question_id=question_id,
            attempt_id=attempt_id,
            event_id=request_id,
            occurred_at=timestamp,

            payload={
                "attempt_number":
                    decision["attempt_number"],

                "response":
                    presentation["presented_choices"][
                        selected_position
                    ],

                "selected_position":
                    selected_position,

                "evaluation":
                    decision["evaluation"],

                "assistance_status": "UNKNOWN",

                "elapsed_since_presentation_ms": None,

                "elapsed_since_previous_attempt_ms": None,

                "progression_decision": decision,
            }
        )
    )

    completion_event_id = None
    ended_at = None

    if decision["evaluation"] == "CORRECT":

        completion_event = (
            append_performance_event_in_transaction(
                connection=connection,
                session_id=session_id,
                event_type=EventType.QUESTION_COMPLETED,
                source=EventSource.SYSTEM,
                question_id=question_id,
                occurred_at=timestamp,

                payload={
                    "outcome": "CORRECT",
                    "duration_ms": None,

                    "response_event_id":
                        response_event["event_id"],

                    "round_number":
                        decision["round_number"],

                    "completion_authorized":
                        decision["completion_authorized"],

                    "decision_reason":
                        decision["decision_reason"],
                }
            )
        )

        completion_event_id = (
            completion_event["event_id"]
        )

        ended_at = timestamp

    result = connection.execute("""
        UPDATE activity_execution_rounds

        SET status = ?,
            attempt_count = ?,
            selected_alternatives = ?,
            completion_event_id = ?,
            ended_at = ?

        WHERE question_id = ?
          AND session_id = ?
          AND status = 'ACTIVE'
          AND attempt_count = ?
    """, (
        decision["round_status"],
        decision["attempt_number"],

        json.dumps(
            decision["selected_alternatives"],
            separators=(",", ":")
        ),

        completion_event_id,
        ended_at,
        question_id,
        session_id,
        current_round["attempt_count"],
    ))

    if result.rowcount != 1:

        raise RuntimeError(
            "Question round update failed"
        )

    if decision["completion_authorized"]:

        # Successful progression is authorized only
        # by the server-side response evaluator.

        if completion_event_id is None:

            raise RuntimeError(
                "Completion evidence is missing"
            )

        result = connection.execute("""
            UPDATE activity_execution_states

            SET status = 'SUCCESS_CONFIRMED',
                completion_event_id = ?,
                updated_at = ?

            WHERE session_id = ?
              AND status = 'AWAITING_RESPONSE'
              AND current_round_number = ?
        """, (
            completion_event_id,
            timestamp,
            session_id,
            current_round["round_number"],
        ))

        if result.rowcount != 1:

            raise RuntimeError(
                "Educational success update failed"
            )

    else:

        transition_execution_state(
            connection=connection,
            session_id=session_id,
            target_status=decision[
                "execution_status"
            ],
        )

    return {
        "question_id": question_id,

        "response_event_id":
            response_event["event_id"],

        "decision": decision,

        "duplicate_request": False,
    }


def record_student_response(
    session_id,
    question_id,
    request_id,
    selected_position
):

    with database_transaction(write=True) as connection:

        return record_response_in_transaction(
            connection=connection,
            session_id=session_id,
            question_id=question_id,
            request_id=request_id,
            selected_position=selected_position,
        )
