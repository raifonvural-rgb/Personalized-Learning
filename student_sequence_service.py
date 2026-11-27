from profile_storage import get_profile

from performance_models import validate_identifier

from assignment_lifecycle import start_next_assignment

from student_learning_context import (
    get_learning_context,
    bind_learning_context,
    clear_learning_context,
)

from activity_presentation import get_student_presentation


def initialize_student_sequence(student_id):

    student_id = validate_identifier(
        student_id,
        "student_id"
    )

    context = get_learning_context()

    if (
        context["student_id"] is not None
        and context["student_id"] != student_id
    ):
        raise ValueError(
            "Another student learning context is active."
        )

    profile = get_profile(student_id)

    if profile is None:
        raise ValueError(
            "Student profile does not exist."
        )

    student = {
        "id": profile["id"],
        "name": profile["general"]["name"],
    }

    result = start_next_assignment(student_id)

    assignment = result["assignment"]

    learning_session = result["learning_session"]

    if assignment is None:

        clear_learning_context()

        return {
            "student": student,
            "sequence_status": "NO_ELIGIBLE_ASSIGNMENT",
            "assignment": None,
            "execution": None,
            "resumed": False,
        }

    execution_state = result["execution_state"]

    current_round = result["current_round"]

    execution = {
        "status": execution_state["status"],
        "round_number": execution_state[
            "current_round_number"
        ],
        "question": None,
    }

    if current_round is not None:

        execution["question"] = {
            "question_id": current_round["question_id"],
            "round_number": current_round["round_number"],
            "status": current_round["status"],
            "attempt_count": current_round["attempt_count"],
            "presentation": get_student_presentation(
                current_round["presentation_snapshot"]
            ),
        }

    bind_learning_context(
        student_id=student_id,
        assignment_id=assignment["assignment_id"],
        performance_session_id=learning_session[
            "session_id"
        ],
    )

    return {
        "student": student,
        "sequence_status": "ACTIVE",
        "assignment": {
            "assignment_id": assignment["assignment_id"],
            "activity_id": assignment["activity_id"],
            "sequence_order": assignment["sequence_order"],
            "status": assignment["status"],
        },
        "execution": execution,
        "resumed": result["resumed"],
    }


from performance_database import database_transaction

from performance_storage import (
    find_session,
    decode_session,
)

from assignment_repository import (
    find_assignment,
)

from assignment_models import decode_assignment

from activity_execution_repository import (
    find_execution_state,
    find_current_round,
    decode_execution_state,
    decode_execution_round,
)


def retrieve_student_sequence():

    context = get_learning_context()

    student_id = context["student_id"]

    assignment_id = context["assignment_id"]

    performance_session_id = context[
        "performance_session_id"
    ]

    result = {
        "student": None,
        "sequence_status": "NO_CONTEXT",
        "assignment": None,
        "execution": None,
    }

    if all(
        value is None
        for value in context.values()
    ):
        return result

    result["sequence_status"] = "STALE_CONTEXT"

    if not isinstance(student_id, str):
        return result

    if not student_id.strip():
        return result

    profile = get_profile(student_id)

    if profile is None:
        return result

    result["student"] = {
        "id": profile["id"],
        "name": profile["general"]["name"],
    }

    if (
        assignment_id is None
        and performance_session_id is None
    ):
        result["sequence_status"] = (
            "BETWEEN_ASSIGNMENTS"
        )

        return result

    if not all(
        isinstance(value, str) and bool(value.strip())
        for value in (
            assignment_id,
            performance_session_id,
        )
    ):
        return result

    with database_transaction() as connection:

        assignment_row = find_assignment(
            connection,
            assignment_id
        )

        session_row = find_session(
            connection,
            performance_session_id
        )

        if assignment_row is None or session_row is None:
            return result

        assignment = decode_assignment(
            assignment_row
        )

        learning_session = decode_session(
            session_row
        )

        if (
            assignment["student_id"] != student_id
            or learning_session["student_id"] != student_id
            or learning_session["assignment_id"] != assignment_id
            or learning_session["activity_id"] != assignment["activity_id"]
        ):
            return result

        state_row = find_execution_state(
            connection,
            performance_session_id
        )

        if state_row is None:
            return result

        execution_state = decode_execution_state(
            state_row
        )

        if (
            assignment["status"] == "COMPLETED"
            and learning_session["status"] == "COMPLETED"
            and execution_state["status"] == "COMPLETED"
        ):

            result["sequence_status"] = (
                "ASSIGNMENT_COMPLETED"
            )

        elif (
            assignment["status"] == "IN_PROGRESS"
            and assignment["enabled"]
            and learning_session["status"] == "ACTIVE"
            and execution_state["status"] in (
                "AWAITING_RESPONSE",
                "REPEAT_REQUIRED",
                "SUCCESS_CONFIRMED",
            )
        ):

            result["sequence_status"] = "ACTIVE"

        else:
            return result

        current_round = find_current_round(
            connection,
            performance_session_id
        )

        if current_round is None:

            result["sequence_status"] = "STALE_CONTEXT"

            return result

        if isinstance(
            current_round["presentation_snapshot"],
            str
        ):

            current_round = decode_execution_round(
                current_round
            )

        expected_round_status = {
            "AWAITING_RESPONSE": "ACTIVE",
            "REPEAT_REQUIRED": "REPEAT_REQUIRED",
            "SUCCESS_CONFIRMED": "SUCCESS_CONFIRMED",
            "COMPLETED": "SUCCESS_CONFIRMED",
        }

        if (
            current_round["round_number"]
            != execution_state["current_round_number"]
            or current_round["status"]
            != expected_round_status[
                execution_state["status"]
            ]
        ):

            result["sequence_status"] = "STALE_CONTEXT"

            return result

        result["performance_session_id"] = performance_session_id

        result["assignment"] = {
            "assignment_id": assignment["assignment_id"],
            "activity_id": assignment["activity_id"],
            "sequence_order": assignment["sequence_order"],
            "status": assignment["status"],
        }

        result["execution"] = {
            "status": execution_state["status"],
            "round_number": execution_state[
                "current_round_number"
            ],
            "question": {
                "question_id": current_round["question_id"],
                "round_number": current_round["round_number"],
                "status": current_round["status"],
                "attempt_count": current_round["attempt_count"],
                "presentation": get_student_presentation(
                    current_round["presentation_snapshot"]
                ),
            },
        }

    return result


from assignment_lifecycle import interrupt_assignment


def terminate_student_sequence():

    existing = retrieve_student_sequence()

    sequence_status = existing["sequence_status"]

    context = get_learning_context()

    result = {
        "student": None,
        "sequence_status": "NO_CONTEXT",
        "assignment": None,
        "execution": None,
        "terminated": False,
        "interrupted_assignment_id": None,
    }

    if sequence_status == "NO_CONTEXT":

        return result

    if sequence_status == "STALE_CONTEXT":

        raise ValueError(
            "Stale context requires explicit recovery."
        )

    if sequence_status == "ACTIVE":

        interruption = interrupt_assignment(

            student_id=context["student_id"],

            assignment_id=context["assignment_id"],

            performance_session_id=context[
                "performance_session_id"
            ],

            reason="USER_ENDED_SEQUENCE",

            session_status="TERMINATED",
        )

        result["interrupted_assignment_id"] = (
            context["assignment_id"]
        )

        result["already_ended"] = interruption[
            "already_ended"
        ]

    elif sequence_status not in (
        "ASSIGNMENT_COMPLETED",
        "BETWEEN_ASSIGNMENTS",
    ):

        raise ValueError(
            "Unsupported sequence termination state."
        )

    clear_learning_context()

    result["terminated"] = True

    return result


def advance_student_sequence(
    assignment_id,
    performance_session_id
):

    context = get_learning_context()

    if (
        not context["student_id"]
        or context["assignment_id"] != assignment_id
        or context["performance_session_id"]
            != performance_session_id
    ):
        raise ValueError(
            "Learning context has changed."
        )

    existing = retrieve_student_sequence()

    if existing["sequence_status"] != "ASSIGNMENT_COMPLETED":

        raise ValueError(
            "Current assignment must be completed first."
        )

    result = initialize_student_sequence(
        context["student_id"]
    )

    if result["sequence_status"] == "NO_ELIGIBLE_ASSIGNMENT":

        result["sequence_status"] = "SEQUENCE_COMPLETED"

    return result
