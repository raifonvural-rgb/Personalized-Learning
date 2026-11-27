"""
Transactional assignment completion based on
verified educational progression evidence.
"""

from assignment_models import decode_assignment

from assignment_repository import (
    require_owned_assignment,
    find_assignment,
)

from activity_execution_repository import (
    require_transaction,
    find_execution_state,
    decode_execution_state,
)

from activity_completion_verifier import (
    verify_educational_completion,
)

from activity_progression_verifier import (
    verify_execution_history,
)

from performance_database import (
    database_transaction,
)

from performance_models import (
    SessionStatus,
    validate_identifier,
    utc_now,
)

from performance_storage import (
    find_session,
    decode_session,
    end_learning_session_in_transaction,
)


def complete_assignment_in_transaction(
    connection,
    student_id,
    assignment_id,
    performance_session_id
):

    require_transaction(connection)

    student_id = validate_identifier(
        student_id,
        "student_id"
    )

    assignment_id = validate_identifier(
        assignment_id,
        "assignment_id"
    )

    performance_session_id = validate_identifier(
        performance_session_id,
        "performance_session_id"
    )

    assignment = require_owned_assignment(
        connection,
        student_id,
        assignment_id
    )

    learning_session = find_session(
        connection,
        performance_session_id
    )

    if learning_session is None:

        raise ValueError(
            "Learning session does not exist"
        )

    if (
        learning_session["student_id"] != student_id
        or learning_session["assignment_id"] != assignment_id
        or learning_session["activity_id"] !=
            assignment["activity_id"]
    ):

        raise ValueError(
            "Learning session association mismatch"
        )

    state = find_execution_state(
        connection,
        performance_session_id
    )

    if state is None:

        raise ValueError(
            "Execution state does not exist"
        )

    # Idempotent completion request.

    if (
        assignment["status"] == "COMPLETED"
        and learning_session["status"] == "COMPLETED"
        and state["status"] == "COMPLETED"
    ):

        return {
            "assignment": decode_assignment(
                assignment
            ),

            "learning_session": decode_session(
                learning_session
            ),

            "execution_state": decode_execution_state(
                state
            ),

            "already_completed": True,
        }

    if assignment["status"] != "IN_PROGRESS":

        raise ValueError(
            "Assignment is not in progress"
        )

    if learning_session["status"] != "ACTIVE":

        raise ValueError(
            "Learning session is not active"
        )

    if state["status"] != "SUCCESS_CONFIRMED":

        raise ValueError(
            "Educational success has not been confirmed"
        )

    # Verify educational evidence before
    # modifying any operational state.

    history_evidence = verify_execution_history(
        connection=connection,
        session_id=performance_session_id,
    )

    if history_evidence.get("verified") is not True:

        raise RuntimeError(
            "Full execution history verification failed"
        )

    evidence = verify_educational_completion(
        connection=connection,
        session_id=performance_session_id,
    )

    if evidence.get("verified") is not True:

        raise RuntimeError(
            "Educational completion verification failed"
        )

    if (
        history_evidence["session_id"] !=
            evidence["session_id"]

        or history_evidence["final_question_id"] !=
            evidence["question_id"]

        or history_evidence["completion_event_id"] !=
            evidence["completion_event_id"]

        or history_evidence["round_count"] !=
            evidence["round_number"]

        or history_evidence["round_evidence"][-1][
            "attempt_count"
        ] != evidence["attempt_count"]

        or history_evidence["round_evidence"][-1][
            "decision_reason"
        ] != evidence["decision_reason"]
    ):

        raise RuntimeError(
            "Completion verification results disagree"
        )

    timestamp = utc_now()

    # 1. Complete execution state.

    result = connection.execute("""
        UPDATE activity_execution_states

        SET status = 'COMPLETED',
            updated_at = ?

        WHERE session_id = ?
          AND status = 'SUCCESS_CONFIRMED'
          AND completion_event_id = ?
    """, (
        timestamp,
        performance_session_id,
        evidence["completion_event_id"],
    ))

    if result.rowcount != 1:

        raise RuntimeError(
            "Execution completion failed"
        )

    # 2. Complete learning session and record
    # the corresponding SESSION_ENDED event.

    completed_session = (
        end_learning_session_in_transaction(
            connection=connection,
            session_id=performance_session_id,
            status=SessionStatus.COMPLETED,
            termination_reason=(
                "EDUCATIONAL_COMPLETION_VERIFIED"
            ),
        )
    )

    # 3. Complete assignment.

    result = connection.execute("""
        UPDATE assignments

        SET status = 'COMPLETED',
            completed_at = ?,
            updated_at = ?

        WHERE assignment_id = ?
          AND student_id = ?
          AND status = 'IN_PROGRESS'
    """, (
        completed_session["ended_at"],
        completed_session["ended_at"],
        assignment_id,
        student_id,
    ))

    if result.rowcount != 1:

        raise RuntimeError(
            "Assignment completion failed"
        )

    return {
        "assignment": decode_assignment(
            find_assignment(
                connection,
                assignment_id
            )
        ),

        "learning_session": completed_session,

        "execution_state": decode_execution_state(
            find_execution_state(
                connection,
                performance_session_id
            )
        ),

        "completion_evidence": evidence,

        "execution_history_evidence": history_evidence,

        "already_completed": False,
    }


def complete_assignment(
    student_id,
    assignment_id,
    performance_session_id
):

    with database_transaction(write=True) as connection:

        return complete_assignment_in_transaction(
            connection=connection,
            student_id=student_id,
            assignment_id=assignment_id,
            performance_session_id=performance_session_id,
        )
