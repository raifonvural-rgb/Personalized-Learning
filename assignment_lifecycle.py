"""
Transactional coordination of assignments and
persistent learning sessions.
"""

from copy import deepcopy

from assignment_models import decode_assignment

from assignment_repository import (
    find_assignment,
    find_in_progress_assignment,
    find_next_pending_assignment,
    validate_activity_eligibility,
)

from activity_integrity import (
    validate_activity_draft_integrity,
)

from performance_database import database_transaction

from performance_models import (
    LearningMode,
    validate_identifier,
    utc_now,
)

from performance_storage import (
    create_learning_session_in_transaction,
)

from activity_execution_repository import (
    initialize_execution_state,
)

from activity_round_service import (
    initialize_first_round,
)

from activity_interruption_service import (
    interrupt_execution_in_transaction,
)


def start_next_assignment(student_id):
    """
    Start or resume the student's eligible assignment.

    Assignment state, learning session creation and
    SESSION_STARTED event persistence share one
    database transaction.
    """

    student_id = validate_identifier(
        student_id,
        "student_id"
    )

    with database_transaction(write=True) as connection:

        assignment = find_in_progress_assignment(
            connection,
            student_id
        )

        resumed = assignment is not None

        if assignment is None:

            assignment = find_next_pending_assignment(
                connection,
                student_id
            )

        if assignment is None:

            return {
                "assignment": None,
                "learning_session": None,
                "resumed": False,
            }

        assignment_id = assignment["assignment_id"]
        activity_id = assignment["activity_id"]

        if not assignment["enabled"]:
            raise ValueError(
                "Assignment is not enabled"
            )

        activity = validate_activity_eligibility(
            student_id,
            activity_id
        )

        configuration = activity.get("config")

        if not isinstance(configuration, dict):
            raise ValueError(
                "Invalid activity configuration"
            )

        validate_activity_draft_integrity(
            configuration
        )

        achievement_code = configuration.get(
            "achievement_code"
        )

        if not isinstance(achievement_code, str):
            achievement_code = None

        activity_snapshot = {
            "activity_id": activity_id,
            "configuration": deepcopy(configuration),
        }

        active_sessions = connection.execute(
            '''
            SELECT *
            FROM learning_sessions
            WHERE assignment_id = ?
              AND status = 'ACTIVE'
            ''',
            (assignment_id,)
        ).fetchall()

        if assignment["status"] == "IN_PROGRESS":

            if len(active_sessions) != 1:

                raise RuntimeError(
                    "In-progress assignment must have "
                    "exactly one active learning session"
                )

        elif assignment["status"] == "PENDING":

            if active_sessions:

                raise RuntimeError(
                    "Pending assignment cannot have "
                    "an active learning session"
                )

        else:

            raise RuntimeError(
                "Invalid assignment initialization status"
            )

        learning_session = (
            create_learning_session_in_transaction(
                connection=connection,
                student_id=student_id,
                learning_mode=LearningMode.COMPUTER_BASED,
                activity_snapshot=activity_snapshot,
                assignment_id=assignment_id,
                activity_id=activity_id,
                achievement_code=achievement_code,
            )
        )

        if assignment["status"] == "PENDING":

            result = connection.execute("""
                UPDATE assignments

                SET status = 'IN_PROGRESS',

                    started_at = COALESCE(
                        started_at, ?
                    ),

                    updated_at = ?

                WHERE assignment_id = ?
                  AND status = 'PENDING'
                  AND enabled = 1
            """, (
                learning_session["started_at"],
                utc_now(),
                assignment_id,
            ))

            if result.rowcount != 1:
                raise RuntimeError(
                    "Assignment initialization failed"
                )

        execution_state = initialize_execution_state(
            connection=connection,
            session_id=learning_session["session_id"],
        )

        current_round = initialize_first_round(
            connection=connection,
            session_id=learning_session["session_id"],
        )

        from activity_execution_repository import (
            find_execution_state,
            decode_execution_state,
        )

        execution_state = decode_execution_state(
            find_execution_state(
                connection,
                learning_session["session_id"]
            )
        )

        updated_assignment = find_assignment(
            connection,
            assignment_id
        )

        return {
            "assignment": decode_assignment(
                updated_assignment
            ),
            "learning_session": learning_session,
            "execution_state": execution_state,
            "current_round": current_round,
            "resumed": resumed,
        }


def interrupt_assignment(
    student_id,
    assignment_id,
    performance_session_id,
    reason="USER_ENDED_SESSION",
    session_status="TERMINATED"
):
    """
    End an unfinished learning session and return
    its assignment to PENDING.

    Historical sessions and events are preserved.
    """

    from performance_models import (
        SessionStatus,
        validate_enum,
    )

    from performance_storage import (
        find_session,
        decode_session,
        end_learning_session_in_transaction,
    )

    from assignment_repository import (
        require_owned_assignment,
    )

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

    reason = validate_identifier(
        reason,
        "termination_reason"
    )

    session_status = validate_enum(
        session_status,
        SessionStatus,
        "session_status"
    )

    if session_status not in (
        SessionStatus.TERMINATED.value,
        SessionStatus.INTERRUPTED.value,
    ):
        raise ValueError(
            "Invalid interruption session status"
        )

    with database_transaction(write=True) as connection:

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

        # A repeated request concerning an old session
        # must never interrupt a newer learning session.

        if learning_session["status"] != "ACTIVE":

            return {
                "assignment": decode_assignment(
                    assignment
                ),
                "learning_session": decode_session(
                    learning_session
                ),
                "already_ended": True,
            }

        if assignment["status"] != "IN_PROGRESS":
            raise ValueError(
                "Assignment is not in progress"
            )

        interruption = interrupt_execution_in_transaction(
            connection=connection,
            session_id=performance_session_id,
            reason=reason,
        )

        ended_session = (
            end_learning_session_in_transaction(
                connection=connection,
                session_id=performance_session_id,
                status=session_status,
                termination_reason=reason,
            )
        )

        result = connection.execute("""
            UPDATE assignments

            SET status = 'PENDING',
                updated_at = ?

            WHERE assignment_id = ?
              AND student_id = ?
              AND status = 'IN_PROGRESS'
        """, (
            utc_now(),
            assignment_id,
            student_id,
        ))

        if result.rowcount != 1:
            raise RuntimeError(
                "Assignment interruption failed"
            )

        updated_assignment = find_assignment(
            connection,
            assignment_id
        )

        return {
            "assignment": decode_assignment(
                updated_assignment
            ),
            "learning_session": ended_session,
            "execution_interruption": interruption,
            "already_ended": False,
        }
