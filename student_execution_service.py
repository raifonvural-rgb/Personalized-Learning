from performance_database import database_transaction

from student_execution_context import (
    require_bound_execution,
)

from activity_execution_repository import (
    find_current_round,
    decode_execution_round,
)

from activity_presentation import (
    get_student_presentation,
)


def retrieve_assignment_execution(assignment_id):

    with database_transaction() as connection:

        context = require_bound_execution(
            connection,
            assignment_id
        )

        assignment = context["assignment"]

        execution_state = context["execution_state"]

        session_id = context["performance_session_id"]

        round_row = find_current_round(
            connection,
            session_id
        )

        if round_row is None:

            raise RuntimeError(
                "Current execution round is missing."
            )

        question_round = decode_execution_round(
            round_row
        )

        if (
            question_round["round_number"]
            != execution_state["current_round_number"]
        ):

            raise RuntimeError(
                "Execution round number mismatch."
            )

        expected_round_status = {

            "AWAITING_RESPONSE": "ACTIVE",

            "REPEAT_REQUIRED": "REPEAT_REQUIRED",

            "SUCCESS_CONFIRMED": "SUCCESS_CONFIRMED",

        }[execution_state["status"]]

        if (
            question_round["status"]
            != expected_round_status
        ):

            raise RuntimeError(
                "Execution and round status mismatch."
            )

        presentation = get_student_presentation(
            question_round["presentation_snapshot"]
        )

        return {

            "assignment": {

                "assignment_id": assignment[
                    "assignment_id"
                ],

                "activity_id": assignment[
                    "activity_id"
                ],

                "sequence_order": assignment[
                    "sequence_order"
                ],

                "status": assignment["status"],
            },

            "performance_session_id": session_id,

            "execution": {

                "status": execution_state["status"],

                "round_number": question_round[
                    "round_number"
                ],

                "question": {

                    "question_id": question_round[
                        "question_id"
                    ],

                    "round_number": question_round[
                        "round_number"
                    ],

                    "status": question_round[
                        "status"
                    ],

                    "attempt_count": question_round[
                        "attempt_count"
                    ],

                    "selected_alternatives": (
                        question_round[
                            "selected_alternatives"
                        ]
                    ),

                    "presentation": presentation,
                },

                "allowed_operations": {

                    "submit_response": (
                        execution_state["status"]
                        == "AWAITING_RESPONSE"
                    ),

                    "start_repetition": (
                        execution_state["status"]
                        == "REPEAT_REQUIRED"
                    ),

                    "complete_assignment": (
                        execution_state["status"]
                        == "SUCCESS_CONFIRMED"
                    ),
                },
            },
        }


from performance_models import (
    validate_identifier,
    validate_nonnegative_integer,
)

from activity_response_service import (
    record_response_in_transaction,
)


def submit_assignment_response(
    assignment_id,
    performance_session_id,
    question_id,
    request_id,
    selected_position
):

    assignment_id = validate_identifier(
        assignment_id,
        "assignment_id"
    )

    performance_session_id = validate_identifier(
        performance_session_id,
        "performance_session_id"
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

    with database_transaction(write=True) as connection:

        context = require_bound_execution(
            connection,
            assignment_id,
            allowed_execution_statuses=(
                "AWAITING_RESPONSE",
                "REPEAT_REQUIRED",
                "SUCCESS_CONFIRMED",
            )
        )

        if (
            context["performance_session_id"]
            != performance_session_id
        ):

            raise ValueError(
                "Response belongs to an outdated "
                "performance session."
            )

        result = record_response_in_transaction(

            connection,

            session_id=performance_session_id,

            question_id=question_id,

            request_id=request_id,

            selected_position=selected_position,
        )

        decision = result["decision"]

        return {

            "assignment_id": assignment_id,

            "performance_session_id": (
                performance_session_id
            ),

            "question_id": result["question_id"],

            "request_id": request_id,

            "response_event_id": result[
                "response_event_id"
            ],

            "duplicate_request": result[
                "duplicate_request"
            ],

            "feedback": {

                "type": decision["feedback_type"],

                "evaluation": decision["evaluation"],
            },

            "progression": {

                "next_action": decision["next_action"],

                "execution_status": decision[
                    "execution_status"
                ],

                "completion_authorized": decision[
                    "completion_authorized"
                ],
            },

            "attempt": {

                "attempt_number": decision[
                    "attempt_number"
                ],

                "selected_position": decision[
                    "selected_position"
                ],

                "round_number": decision[
                    "round_number"
                ],
            },
        }


from activity_repetition_service import (
    start_repetition_in_transaction,
)


def repeat_assignment_question(
    assignment_id,
    performance_session_id,
    previous_question_id
):

    with database_transaction(write=True) as connection:

        context = require_bound_execution(
            connection,
            assignment_id,
            allowed_execution_statuses=(
                "REPEAT_REQUIRED",
                "AWAITING_RESPONSE",
            ),
        )

        if (
            context["performance_session_id"]
            != performance_session_id
        ):
            raise ValueError(
                "Performance session has changed."
            )

        result = start_repetition_in_transaction(
            connection=connection,
            session_id=performance_session_id,
            previous_question_id=previous_question_id,
        )

        return {
            "assignment_id": assignment_id,
            "performance_session_id": performance_session_id,
            "question_id": result["round"]["question_id"],
            "round_number": result["round"]["round_number"],
            "duplicate_request": result["duplicate_request"],
        }


from assignment_completion_service import (
    complete_assignment_in_transaction,
)

from student_learning_context import get_learning_context


def complete_student_assignment(
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

    with database_transaction(write=True) as connection:

        result = complete_assignment_in_transaction(
            connection=connection,
            student_id=context["student_id"],
            assignment_id=assignment_id,
            performance_session_id=performance_session_id,
        )

        return {
            "assignment_id": assignment_id,
            "performance_session_id": performance_session_id,
            "assignment_status": result["assignment"]["status"],
            "execution_status": "COMPLETED",
            "already_completed": result["already_completed"],
        }
