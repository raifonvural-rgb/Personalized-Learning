"""
Transactional interruption of activity execution.

Preserves historical responses and completed rounds.
Does not independently terminate learning sessions
or modify assignment status.
"""

from activity_execution_repository import (
    require_transaction,
    find_execution_state,
    find_current_round,
    decode_execution_state,
    decode_execution_round,
    transition_execution_state,
)

from performance_models import (
    EventType,
    EventSource,
    validate_identifier,
    utc_now,
)

from performance_storage import (
    find_session,
    append_performance_event_in_transaction,
)


def interrupt_execution_in_transaction(
    connection,
    session_id,
    reason
):
    """
    Interrupt unfinished execution within the
    caller's existing write transaction.
    """

    require_transaction(connection)

    session_id = validate_identifier(
        session_id,
        "session_id"
    )

    reason = validate_identifier(
        reason,
        "reason"
    )

    learning_session = find_session(
        connection,
        session_id
    )

    if learning_session is None:

        raise ValueError(
            "Learning session does not exist"
        )

    state = find_execution_state(
        connection,
        session_id
    )

    if state is None:

        # Legacy learning sessions may not have
        # an associated execution state.

        return {
            "execution_state": None,
            "interrupted_question_id": None,
            "already_interrupted": False,
        }

    if state["status"] == "INTERRUPTED":

        return {
            "execution_state":
                decode_execution_state(state),

            "interrupted_question_id": None,

            "already_interrupted": True,
        }

    if state["status"] == "COMPLETED":

        raise ValueError(
            "Completed execution cannot be interrupted"
        )

    if learning_session["status"] != "ACTIVE":

        raise ValueError(
            "Learning session is not active"
        )

    current_round = decode_execution_round(
        find_current_round(
            connection,
            session_id
        )
    )

    interrupted_question_id = None

    if (
        current_round is not None
        and current_round["status"] == "ACTIVE"
    ):

        timestamp = utc_now()

        interrupted_question_id = (
            current_round["question_id"]
        )

        completion_event = (
            append_performance_event_in_transaction(
                connection=connection,
                session_id=session_id,
                event_type=EventType.QUESTION_COMPLETED,
                source=EventSource.SYSTEM,
                question_id=interrupted_question_id,
                occurred_at=timestamp,

                payload={
                    "outcome": "INTERRUPTED",

                    "duration_ms": None,

                    "round_number":
                        current_round["round_number"],

                    "completion_authorized": False,

                    "interruption_reason": reason,
                }
            )
        )

        result = connection.execute("""
            UPDATE activity_execution_rounds

            SET status = 'INTERRUPTED',
                completion_event_id = ?,
                ended_at = ?

            WHERE question_id = ?
              AND session_id = ?
              AND status = 'ACTIVE'
        """, (
            completion_event["event_id"],
            timestamp,
            interrupted_question_id,
            session_id,
        ))

        if result.rowcount != 1:

            raise RuntimeError(
                "Question interruption update failed"
            )

    updated_state = transition_execution_state(
        connection=connection,
        session_id=session_id,
        target_status="INTERRUPTED",
    )

    return {
        "execution_state": updated_state,

        "interrupted_question_id":
            interrupted_question_id,

        "already_interrupted": False,
    }
