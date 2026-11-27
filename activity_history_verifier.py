"""
Verify consistency of question presentation history
against the original learning session activity snapshot.
"""

from copy import deepcopy

from activity_execution_repository import (
    require_transaction,
    find_execution_state,
    decode_execution_round,
)

from activity_presentation import (
    build_question_presentation,
)

from performance_models import (
    validate_identifier,
    encode_json_object,
)

from performance_storage import (
    find_session,
    decode_session,
)


def require_consistency(condition, message):

    if not condition:

        raise ValueError(message)


def canonical_choices(choices):

    if not isinstance(choices, list):

        raise ValueError(
            "Invalid presentation alternatives"
        )

    return sorted(
        encode_json_object(
            choice,
            "alternative"
        )

        for choice in choices
    )


def presentation_without_order(presentation):

    result = deepcopy(presentation)

    result.pop("presented_choices")

    result.pop("correct_index")

    return result


def verify_presentation_history(
    connection,
    session_id
):

    require_transaction(connection)

    session_id = validate_identifier(
        session_id,
        "session_id"
    )

    session_row = find_session(
        connection,
        session_id
    )

    require_consistency(
        session_row is not None,
        "Learning session does not exist"
    )

    learning_session = decode_session(
        session_row
    )

    require_consistency(
        learning_session["status"] == "ACTIVE",
        "Active learning session required"
    )

    state = find_execution_state(
        connection,
        session_id
    )

    require_consistency(
        state is not None
        and state["status"] == "SUCCESS_CONFIRMED",
        "Successful execution state required"
    )

    configuration = learning_session[
        "activity_snapshot"
    ]["configuration"]

    original_presentation = (
        build_question_presentation(
            configuration
        )
    )

    original_choices = original_presentation[
        "presented_choices"
    ]

    original_correct_choice = original_choices[
        original_presentation["correct_index"]
    ]

    original_content = presentation_without_order(
        original_presentation
    )

    rounds = connection.execute("""
        SELECT *
        FROM activity_execution_rounds
        WHERE session_id = ?
        ORDER BY round_number
    """, (session_id,)).fetchall()

    rounds = [
        decode_execution_round(row)
        for row in rounds
    ]

    require_consistency(
        len(rounds) > 0,
        "No question rounds available"
    )

    require_consistency(
        len(rounds) ==
            state["current_round_number"],
        "Execution round count mismatch"
    )

    previous_correct_index = None

    for expected_number, question_round in enumerate(
        rounds,
        start=1
    ):

        require_consistency(
            question_round["round_number"] ==
                expected_number,
            "Nonconsecutive question round numbers"
        )

        presentation = question_round[
            "presentation_snapshot"
        ]

        choices = presentation[
            "presented_choices"
        ]

        correct_index = presentation[
            "correct_index"
        ]

        require_consistency(
            type(correct_index) is int
            and 0 <= correct_index < len(choices),
            "Invalid correct answer position"
        )

        require_consistency(
            question_round["first_attempt_required"]
                == (expected_number > 1),
            "Invalid first-attempt requirement"
        )

        require_consistency(
            presentation_without_order(
                presentation
            ) == original_content,
            "Original presentation content changed"
        )

        require_consistency(
            canonical_choices(choices) ==
                canonical_choices(original_choices),
            "Original alternatives changed"
        )

        require_consistency(
            choices[correct_index] ==
                original_correct_choice,
            "Correct alternative content changed"
        )

        if expected_number == 1:

            require_consistency(
                presentation == original_presentation,
                "Initial presentation differs from snapshot"
            )

        else:

            require_consistency(
                correct_index != previous_correct_index,
                "Correct answer position was not changed"
            )

        expected_status = (
            "SUCCESS_CONFIRMED"
            if expected_number == len(rounds)
            else "REPEAT_REQUIRED"
        )

        require_consistency(
            question_round["status"] ==
                expected_status,
            "Invalid historical round status"
        )

        require_consistency(
            question_round["completion_event_id"]
                is not None,
            "Historical completion evidence missing"
        )

        previous_correct_index = correct_index

    return {
        "verified": True,
        "session_id": session_id,
        "round_count": len(rounds),
        "repetition_count": len(rounds) - 1,
        "final_question_id": rounds[-1]["question_id"],
    }
