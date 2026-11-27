from performance_models import validate_identifier

from student_learning_context import (
    get_learning_context,
    has_complete_learning_context,
)

from assignment_repository import find_assignment

from assignment_models import decode_assignment

from performance_storage import (
    find_session,
    decode_session,
)

from activity_execution_repository import (
    find_execution_state,
    decode_execution_state,
)


def require_bound_execution(
    connection,
    assignment_id,
    allowed_execution_statuses=None
):

    if not connection.in_transaction:

        raise RuntimeError(
            "Execution validation requires a transaction."
        )

    assignment_id = validate_identifier(
        assignment_id,
        "assignment_id"
    )

    if not has_complete_learning_context():

        raise ValueError(
            "Complete learning context is required."
        )

    context = get_learning_context()

    if context["assignment_id"] != assignment_id:

        raise ValueError(
            "Requested assignment does not match "
            "the browser learning context."
        )

    assignment_row = find_assignment(
        connection,
        assignment_id
    )

    if assignment_row is None:

        raise ValueError(
            "Assignment does not exist."
        )

    assignment = decode_assignment(
        assignment_row
    )

    if assignment["student_id"] != context["student_id"]:

        raise ValueError(
            "Assignment student association mismatch."
        )

    if (
        assignment["status"] != "IN_PROGRESS"
        or not assignment["enabled"]
    ):

        raise ValueError(
            "Assignment is not executable."
        )

    session_row = find_session(
        connection,
        context["performance_session_id"]
    )

    if session_row is None:

        raise ValueError(
            "Performance session does not exist."
        )

    learning_session = decode_session(
        session_row
    )

    if (
        learning_session["student_id"]
        != context["student_id"]

        or learning_session["assignment_id"]
        != assignment_id

        or learning_session["activity_id"]
        != assignment["activity_id"]
    ):

        raise ValueError(
            "Performance session association mismatch."
        )

    if learning_session["status"] != "ACTIVE":

        raise ValueError(
            "Performance session is not active."
        )

    state_row = find_execution_state(
        connection,
        context["performance_session_id"]
    )

    if state_row is None:

        raise ValueError(
            "Activity execution state does not exist."
        )

    execution_state = decode_execution_state(
        state_row
    )

    if allowed_execution_statuses is None:

        allowed_execution_statuses = (
            "AWAITING_RESPONSE",
            "REPEAT_REQUIRED",
            "SUCCESS_CONFIRMED",
        )

    if (
        execution_state["status"]
        not in allowed_execution_statuses
    ):

        raise ValueError(
            "Operation is not permitted in the "
            "current execution state."
        )

    return {
        "student_id": context["student_id"],
        "assignment_id": assignment_id,
        "performance_session_id": context[
            "performance_session_id"
        ],
        "assignment": assignment,
        "learning_session": learning_session,
        "execution_state": execution_state,
    }
